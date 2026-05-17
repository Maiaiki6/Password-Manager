"""
Session management for password vault authentication and timeout.
Handles master password verification and session state tracking.
"""

import threading
from datetime import datetime, timedelta
from src.crypto import CryptoManager
from src.database import PasswordDatabase


class SessionManager:
    """Manages user authentication and session state with timeout."""
    
    def __init__(self, timeout_minutes=15, db_path=None):
        """
        Initialize session manager.
        
        Args:
            timeout_minutes (int): Session timeout in minutes (default 15)
            db_path (str): Optional path to the vault database file
        """
        self.timeout_minutes = timeout_minutes
        self.db_path = db_path
        self.is_authenticated = False
        self.master_key = None
        self.last_activity = None
        self.timeout_timer = None
        self.lock_callback = None  # Called when session times out
    
    def set_lock_callback(self, callback):
        """
        Set callback function to call when session times out.
        
        Args:
            callback (callable): Function to call on timeout
        """
        self.lock_callback = callback
    
    def login(self, master_password, db_path=None):
        """
        Authenticate user with master password.
        
        Args:
            master_password (str): The master password to verify
            db_path (str, optional): Path to the vault database file
            
        Returns:
            tuple: (success: bool, master_key: bytes or None, error: str or None)
            
        Raises:
            RuntimeError: If vault not initialized
        """
        if db_path is not None:
            self.db_path = db_path
        try:
            db = PasswordDatabase(self.db_path)
            
            if not db.vault_exists():
                return False, None, "Vault not initialized. Please create a master password first."
            
            # Retrieve vault metadata
            metadata = db.get_vault_metadata()
            salt = metadata['salt']
            stored_hash = metadata['master_password_hash']
            
            # Verify password
            if not CryptoManager.verify_master_password(master_password, salt, stored_hash):
                return False, None, "Invalid master password."
            
            # Derive master key for this session
            master_key = CryptoManager.derive_master_key(master_password, salt)
            
            # Update session state
            self.is_authenticated = True
            self.master_key = master_key
            self.last_activity = datetime.now()
            
            # Start timeout timer
            self._reset_timeout_timer()
            
            return True, master_key, None
        
        except RuntimeError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def create_vault(self, master_password, db_path=None):
        """
        Create a new vault with a master password.
        
        Args:
            master_password (str): The master password (must be validated by caller)
            db_path (str, optional): Path to create the vault database file
            
        Returns:
            tuple: (success: bool, error: str or None)
            
        Raises:
            RuntimeError: If vault already exists
        """
        if db_path is not None:
            self.db_path = db_path
        try:
            db = PasswordDatabase(self.db_path)
            
            if db.vault_exists():
                return False, "Vault already exists."
            
            # Generate salt and hash
            salt = CryptoManager.generate_salt()
            password_hash = CryptoManager.hash_master_password(master_password, salt)
            
            # Initialize vault
            db.init_vault(salt, password_hash)
            
            return True, None
        
        except RuntimeError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Vault creation error: {str(e)}"
    
    def logout(self):
        """Log out and clear sensitive data."""
        self.is_authenticated = False
        self.master_key = None
        self.last_activity = None
        self._cancel_timeout_timer()
    
    def check_session(self):
        """
        Check if session is still valid (not timed out).
        
        Returns:
            bool: True if authenticated and not timed out, False otherwise
        """
        if not self.is_authenticated or self.master_key is None:
            return False
        
        if self.last_activity is None:
            return False
        
        elapsed = datetime.now() - self.last_activity
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        
        if elapsed > timeout_delta:
            self.logout()
            if self.lock_callback:
                self.lock_callback()
            return False
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp (called on user interaction)."""
        if self.is_authenticated:
            self.last_activity = datetime.now()
            self._reset_timeout_timer()
    
    def _reset_timeout_timer(self):
        """Reset the timeout timer."""
        self._cancel_timeout_timer()
        
        # Create a new timer that checks session timeout
        def check_timeout():
            if not self.check_session() and self.lock_callback:
                self.lock_callback()
        
        self.timeout_timer = threading.Timer(
            self.timeout_minutes * 60,
            check_timeout
        )
        self.timeout_timer.daemon = True
        self.timeout_timer.start()
    
    def _cancel_timeout_timer(self):
        """Cancel the timeout timer."""
        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None
    
    def get_master_key(self):
        """
        Get current session's master key if authenticated.
        
        Returns:
            bytes: Master key if authenticated, None otherwise
        """
        if self.check_session():
            return self.master_key
        return None

    def get_database(self):
        """Return a PasswordDatabase instance for the current vault path."""
        return PasswordDatabase(self.db_path)
    
    def is_locked(self):
        """
        Check if vault is locked (not authenticated).
        
        Returns:
            bool: True if locked, False if authenticated
        """
        return not self.check_session()

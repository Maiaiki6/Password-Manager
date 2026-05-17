"""
Database module for managing encrypted password storage in SQLite.
Handles vault initialization, CRUD operations, and metadata management.
"""

import sqlite3
import os
import base64
from datetime import datetime
from pathlib import Path


class PasswordDatabase:
    """Manages SQLite database for encrypted password storage."""
    
    def __init__(self, db_path=None):
        """
        Initialize the database connection.
        
        Args:
            db_path (str): Path to SQLite database file. 
                          Defaults to data/vault.db
        """
        if db_path is None:
            # Use data directory in project root
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "vault.db"
        
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def init_vault(self, salt, master_password_hash):
        """
        Initialize a new vault with metadata.
        Creates tables if they don't exist.
        
        Args:
            salt (bytes): Salt used for PBKDF2 derivation
            master_password_hash (bytes): Hash of master password for verification
            
        Raises:
            RuntimeError: If vault already initialized (has metadata)
        """
        self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Check if vault already exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='vault_metadata'"
            )
            if cursor.fetchone():
                cursor.execute("SELECT * FROM vault_metadata")
                if cursor.fetchone():
                    self.disconnect()
                    raise RuntimeError("Vault already initialized. Use existing vault or delete database.")
            
            # Create vault_metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vault_metadata (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    salt BLOB NOT NULL,
                    master_password_hash BLOB NOT NULL,
                    created_date TEXT NOT NULL,
                    last_modified TEXT NOT NULL
                )
            """)
            
            # Create passwords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    iv BLOB NOT NULL,
                    ciphertext BLOB NOT NULL,
                    created_date TEXT NOT NULL,
                    updated_date TEXT NOT NULL
                )
            """)
            
            # Insert vault metadata
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO vault_metadata (id, salt, master_password_hash, created_date, last_modified)
                VALUES (1, ?, ?, ?, ?)
            """, (salt, master_password_hash, now, now))
            
            self.connection.commit()
        finally:
            self.disconnect()
    
    def vault_exists(self):
        """
        Check if vault has been initialized.
        
        Returns:
            bool: True if vault metadata exists, False otherwise
        """
        if not Path(self.db_path).exists():
            return False
        
        self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='vault_metadata'"
            )
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                return False
            
            cursor.execute("SELECT * FROM vault_metadata")
            return cursor.fetchone() is not None
        finally:
            self.disconnect()
    
    def get_vault_metadata(self):
        """
        Retrieve vault metadata (salt and master password hash).
        
        Returns:
            dict: Contains 'salt' (bytes) and 'master_password_hash' (bytes)
            
        Raises:
            RuntimeError: If vault not initialized
        """
        if not Path(self.db_path).exists():
            raise RuntimeError("Vault not initialized")
        
        self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT salt, master_password_hash FROM vault_metadata WHERE id = 1")
            row = cursor.fetchone()
            
            if not row:
                raise RuntimeError("Vault not initialized")
            
            return {
                'salt': row['salt'],
                'master_password_hash': row['master_password_hash']
            }
        finally:
            self.disconnect()
    
    def add_password_entry(self, service, username, iv, ciphertext):
        """
        Add a new encrypted password entry.
        
        Args:
            service (str): Service/website name (must be unique)
            username (str): Username or email
            iv (bytes): Initialization vector for this entry
            ciphertext (bytes): Encrypted password
            
        Raises:
            sqlite3.IntegrityError: If service already exists
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO passwords (service, username, iv, ciphertext, created_date, updated_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (service, username, iv, ciphertext, now, now))
            
            self.connection.commit()
        finally:
            self.disconnect()
    
    def get_password_entry(self, service):
        """
        Retrieve an encrypted password entry by service name.
        
        Args:
            service (str): Service/website name
            
        Returns:
            dict: Contains 'id', 'service', 'username', 'iv', 'ciphertext', 
                  'created_date', 'updated_date'
            None: If service not found
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM passwords WHERE service = ?",
                (service,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            self.disconnect()
    
    def get_all_entries(self):
        """
        Retrieve all password entries (service and username only, no secrets).
        
        Returns:
            list: List of dicts with 'id', 'service', 'username', 'created_date', 'updated_date'
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT id, service, username, created_date, updated_date FROM passwords ORDER BY service"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            self.disconnect()
    
    def delete_password_entry(self, service):
        """
        Delete a password entry by service name.
        
        Args:
            service (str): Service/website name
            
        Returns:
            bool: True if deleted, False if not found
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM passwords WHERE service = ?", (service,))
            
            deleted = cursor.rowcount > 0
            if deleted:
                self.connection.commit()
            
            return deleted
        finally:
            self.disconnect()
    
    def search_entries(self, query):
        """
        Search password entries by service or username (case-insensitive).
        
        Args:
            query (str): Search term
            
        Returns:
            list: List of matching entries (service and username only, no secrets)
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT id, service, username, created_date, updated_date 
                FROM passwords 
                WHERE service LIKE ? OR username LIKE ?
                ORDER BY service
            """, (search_term, search_term))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            self.disconnect()
    
    def update_password_entry(self, service, username=None, iv=None, ciphertext=None):
        """
        Update an existing password entry.
        
        Args:
            service (str): Service/website name (identifies the entry)
            username (str, optional): New username
            iv (bytes, optional): New IV
            ciphertext (bytes, optional): New encrypted password
            
        Returns:
            bool: True if updated, False if not found
        """
        self.connect()
        try:
            cursor = self.connection.cursor()
            
            updates = ["updated_date = ?"]
            params = [datetime.now().isoformat()]
            
            if username is not None:
                updates.append("username = ?")
                params.append(username)
            
            if iv is not None:
                updates.append("iv = ?")
                params.append(iv)
            
            if ciphertext is not None:
                updates.append("ciphertext = ?")
                params.append(ciphertext)
            
            params.append(service)
            
            query = f"UPDATE passwords SET {', '.join(updates)} WHERE service = ?"
            cursor.execute(query, params)
            
            updated = cursor.rowcount > 0
            if updated:
                self.connection.commit()
            
            return updated
        finally:
            self.disconnect()

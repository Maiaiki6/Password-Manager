"""
Login screen for master password entry and vault initialization.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from src.database import PasswordDatabase
from src.password_utils import PasswordUtils


class LoginScreen(tk.Frame):
    """Screen for master password login or first-time setup."""
    
    def __init__(self, parent, controller):
        """
        Initialize login screen.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        tk.Frame.__init__(self, parent, bg="#f0f0f0")
        self.controller = controller
        self.selected_vault_path = None
        self.grid(row=0, column=0, sticky="nsew")
        
        # Title
        title_label = tk.Label(
            self, 
            text="Password Manager",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        title_label.pack(pady=40)
        
        # Main frame container
        self.main_frame = tk.Frame(self, bg="#f0f0f0")
        self.main_frame.pack(expand=True)
        
        self._build_screen()
    
    def _create_login_ui(self, parent):
        """Create login interface."""
        # Master password label and entry
        label = tk.Label(
            parent,
            text="Master Password:",
            font=("Helvetica", 12),
            bg="#f0f0f0"
        )
        label.pack(pady=10)
        self._create_selected_vault_label(parent)
        
        self.password_entry = tk.Entry(parent, show="*", width=30, font=("Helvetica", 11))
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<Return>", lambda e: self._login())
        
        # Login button
        login_button = tk.Button(
            parent,
            text="Login",
            command=self._login,
            width=20,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        login_button.pack(pady=20)
        self._create_vault_button(parent)
        self._create_new_vault_button(parent)
        
        # Focus on password entry
        self.password_entry.focus()
    
    def _create_setup_ui(self, parent):
        """Create first-time setup interface."""
        # Instructions
        instructions = tk.Label(
            parent,
            text="No vault found. Create a master password to get started.",
            font=("Helvetica", 11),
            bg="#f0f0f0"
        )
        instructions.pack(pady=20)
        
        # Master password label and entry
        label1 = tk.Label(
            parent,
            text="Master Password:",
            font=("Helvetica", 12),
            bg="#f0f0f0"
        )
        label1.pack(pady=10)
        self._create_selected_vault_label(parent)
        
        self.password_entry = tk.Entry(parent, show="*", width=30, font=("Helvetica", 11))
        self.password_entry.pack(pady=5)
        
        # Confirm password label and entry
        label2 = tk.Label(
            parent,
            text="Confirm Master Password:",
            font=("Helvetica", 12),
            bg="#f0f0f0"
        )
        label2.pack(pady=10)
        
        self.confirm_entry = tk.Entry(parent, show="*", width=30, font=("Helvetica", 11))
        self.confirm_entry.pack(pady=5)
        self.confirm_entry.bind("<Return>", lambda e: self._create_vault())
        
        # Create vault button
        create_button = tk.Button(
            parent,
            text="Create Vault",
            command=self._create_vault,
            width=20,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        create_button.pack(pady=20)
        
        # Requirements info
        info_text = "Requirements:\n• At least 12 characters\n• Mix of uppercase, lowercase, and numbers"
        info_label = tk.Label(
            parent,
            text=info_text,
            font=("Helvetica", 9),
            bg="#f0f0f0",
            fg="#666"
        )
        info_label.pack(pady=20)
        self._create_vault_button(parent)
        self._create_new_vault_button(parent)
        
        # Focus on password entry
        self.password_entry.focus()
    
    def _login(self):
        """Handle login button click."""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showerror("Error", "Please enter your master password.")
            return
        
        session = self.controller.get_session()
        success, master_key, error = session.login(password, db_path=self.selected_vault_path)
        
        if success:
            self.password_entry.delete(0, tk.END)
            self.controller.show_frame(self.controller.vault_screen.__class__)
        else:
            messagebox.showerror("Login Failed", error)
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

    def _get_database(self):
        """Return a PasswordDatabase instance for the selected vault path or default vault."""
        return PasswordDatabase(self.selected_vault_path)

    def _choose_vault_file(self):
        """Open a file dialog to select an existing vault file."""
        file_path = filedialog.askopenfilename(
            title="Select Existing Vault",
            filetypes=[("Vault files", "*.db"), ("All files", "*")]
        )
        if file_path:
            self.selected_vault_path = file_path
            self._build_screen()

    def _build_screen(self):
        """Build the login or setup UI depending on vault existence."""
        # Clear any existing widgets in main_frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.vault_exists = self._get_database().vault_exists()
        if self.vault_exists:
            self._create_login_ui(self.main_frame)
        else:
            self._create_setup_ui(self.main_frame)

    def _choose_new_vault_file(self):
        """Open a save-as dialog to select a new vault file."""
        file_path = filedialog.asksaveasfilename(
            title="Create New Vault",
            defaultextension=".db",
            filetypes=[("Vault files", "*.db"), ("All files", "*")]
        )
        if file_path:
            self.selected_vault_path = file_path
            self._build_screen()

    def _create_vault_button(self, parent):
        choose_button = tk.Button(
            parent,
            text="Open Existing Vault",
            command=self._choose_vault_file,
            width=20,
            bg="#757575",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        choose_button.pack(pady=(10, 0))

    def _create_new_vault_button(self, parent):
        new_button = tk.Button(
            parent,
            text="Create New Vault",
            command=self._choose_new_vault_file,
            width=20,
            bg="#009688",
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        new_button.pack(pady=(10, 0))

    def _create_selected_vault_label(self, parent):
        if self.selected_vault_path:
            vault_name = Path(self.selected_vault_path).name
            label = tk.Label(
                parent,
                text=f"Selected vault: {vault_name}",
                font=("Helvetica", 10),
                bg="#f0f0f0",
                fg="#666"
            )
            label.pack(pady=(0, 10))
    
    def _create_vault(self):
        """Handle create vault button click."""
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        
        if not password or not confirm:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            self.password_entry.delete(0, tk.END)
            self.confirm_entry.delete(0, tk.END)
            self.password_entry.focus()
            return
        
        # Validate master password strength
        is_valid, feedback = PasswordUtils.validate_master_password(password)
        if not is_valid:
            messagebox.showerror("Password Too Weak", feedback)
            return
        
        # Create vault
        session = self.controller.get_session()
        success, error = session.create_vault(password, db_path=self.selected_vault_path)
        
        if success:
            messagebox.showinfo("Success", "Vault created successfully!")
            # Now log in with the new password
            success, master_key, error = session.login(password, db_path=self.selected_vault_path)
            if success:
                self.password_entry.delete(0, tk.END)
                self.confirm_entry.delete(0, tk.END)
                self.controller.show_frame(self.controller.vault_screen.__class__)
        else:
            messagebox.showerror("Error", error)
    
    def refresh(self):
        """Refresh screen on return (check if new login needed)."""
        self._build_screen()

"""
Main vault screen displaying password entries list and detail view.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from src.database import PasswordDatabase
from src.crypto import CryptoManager
from src.gui.entry_dialog import PasswordEntryDialog


class VaultScreen(tk.Frame):
    """Main vault screen with entry list and search."""
    
    def __init__(self, parent, controller):
        """
        Initialize vault screen.
        
        Args:
            parent: Parent widget
            controller: Main application controller
        """
        tk.Frame.__init__(self, parent, bg="#f0f0f0")
        self.controller = controller
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header with title and lock button
        self._create_header()
        
        # Content area with two panes
        content_frame = tk.Frame(self, bg="#f0f0f0")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Left pane: Search and list
        left_pane = tk.Frame(content_frame, bg="white")
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_pane.grid_rowconfigure(2, weight=1)
        left_pane.grid_columnconfigure(0, weight=1)
        
        # Search bar
        search_label = tk.Label(left_pane, text="Search:", font=("Helvetica", 10), bg="white")
        search_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.search_entry = tk.Entry(left_pane, font=("Helvetica", 10))
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_list())
        
        # Listbox for entries
        listbox_frame = tk.Frame(left_pane, bg="white")
        listbox_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            listbox_frame,
            font=("Helvetica", 10),
            yscrollcommand=scrollbar.set,
            height=15,
            bg="white"
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self._on_entry_select())
        
        # Right pane: Entry details
        right_pane = tk.Frame(content_frame, bg="white")
        right_pane.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_pane.grid_rowconfigure(2, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)
        
        # Detail view title
        detail_label = tk.Label(right_pane, text="Entry Details", font=("Helvetica", 12, "bold"), bg="white")
        detail_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Details frame
        self.detail_frame = tk.Frame(right_pane, bg="white")
        self.detail_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.detail_frame.grid_columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = tk.Frame(right_pane, bg="white")
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        
        add_btn = tk.Button(button_frame, text="Add Entry", command=self._add_entry, bg="#4CAF50", fg="white")
        add_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_btn = tk.Button(button_frame, text="Edit", command=self._edit_entry, bg="#2196F3", fg="white", state=tk.DISABLED)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(button_frame, text="Delete", command=self._delete_entry, bg="#f44336", fg="white", state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.current_entry = None
        self.all_entries = []
    
    def _create_header(self):
        """Create header with title and lock button."""
        header = tk.Frame(self, bg="#333333")
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        title = tk.Label(header, text="Password Vault", font=("Helvetica", 16, "bold"), bg="#333333", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        lock_btn = tk.Button(
            header,
            text="🔒 Lock",
            command=self._lock_vault,
            bg="#f44336",
            fg="white",
            relief=tk.FLAT,
            font=("Helvetica", 10),
            padx=20
        )
        lock_btn.pack(side=tk.RIGHT, padx=20, pady=15)
    
    def _add_entry(self):
        """Open dialog to add a new password entry."""
        dialog = PasswordEntryDialog(self.controller.root, self.controller, mode="add")
        self.controller.root.wait_window(dialog.top)
        
        # Refresh list after dialog closes
        self._refresh_list()
    
    def _edit_entry(self):
        """Open dialog to edit selected entry."""
        if not self.current_entry:
            messagebox.showwarning("No Selection", "Please select an entry to edit.")
            return
        
        dialog = PasswordEntryDialog(
            self.controller.root,
            self.controller,
            mode="edit",
            entry_data=self.current_entry
        )
        self.controller.root.wait_window(dialog.top)
        
        # Refresh list after dialog closes
        self._refresh_list()
    
    def _delete_entry(self):
        """Delete the selected password entry."""
        if not self.current_entry:
            messagebox.showwarning("No Selection", "Please select an entry to delete.")
            return
        
        service = self.current_entry['service']
        if messagebox.askyesno("Confirm Delete", f"Delete entry for '{service}'?"):
            session = self.controller.get_session()
            db = session.get_database()
            if db.delete_password_entry(service):
                messagebox.showinfo("Success", f"Entry for '{service}' deleted.")
                self._refresh_list()
            else:
                messagebox.showerror("Error", "Failed to delete entry.")
    
    def _lock_vault(self):
        """Lock the vault and return to login screen."""
        self.controller.on_vault_locked()
    
    def _on_entry_select(self):
        """Handle entry selection in listbox."""
        selection = self.listbox.curselection()
        if not selection:
            self.current_entry = None
            self._clear_details()
            return
        
        service = self.listbox.get(selection[0]).split(" (")[0]
        
        # Find entry in all_entries
        for entry in self.all_entries:
            if entry['service'] == service:
                self.current_entry = entry
                self._show_details(entry)
                self.edit_btn.config(state=tk.NORMAL)
                self.delete_btn.config(state=tk.NORMAL)
                break
    
    def _show_details(self, entry):
        """Display entry details."""
        # Clear previous details
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        # Service
        tk.Label(self.detail_frame, text="Service:", font=("Helvetica", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(self.detail_frame, text=entry['service'], font=("Helvetica", 10), bg="white").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # Username
        tk.Label(self.detail_frame, text="Username:", font=("Helvetica", 10, "bold"), bg="white").grid(row=1, column=0, sticky="w", pady=5)
        tk.Label(self.detail_frame, text=entry['username'], font=("Helvetica", 10), bg="white").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # Password (hidden, with copy button)
        tk.Label(self.detail_frame, text="Password:", font=("Helvetica", 10, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=5)
        
        pwd_frame = tk.Frame(self.detail_frame, bg="white")
        pwd_frame.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        tk.Label(pwd_frame, text="••••••••", font=("Helvetica", 10), bg="white").pack(side=tk.LEFT)
        
        def copy_password():
            session = self.controller.get_session()
            master_key = session.get_master_key()
            if master_key:
                try:
                    session = self.controller.get_session()
                    db = session.get_database()
                    pwd_entry = db.get_password_entry(entry['service'])
                    if pwd_entry:
                        iv = pwd_entry['iv']
                        ciphertext = pwd_entry['ciphertext']
                        pwd = CryptoManager.decrypt_password(iv, ciphertext, master_key)
                        
                        import pyperclip
                        pyperclip.copy(pwd)
                        messagebox.showinfo("Success", "Password copied to clipboard!")
                        session.update_activity()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy password: {str(e)}")
        
        copy_btn = tk.Button(pwd_frame, text="Copy", command=copy_password, font=("Helvetica", 9), bg="#2196F3", fg="white")
        copy_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Created date
        tk.Label(self.detail_frame, text="Created:", font=("Helvetica", 9), bg="white", fg="#666").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        tk.Label(self.detail_frame, text=entry['created_date'][:19], font=("Helvetica", 9), bg="white", fg="#666").grid(row=4, column=0, columnspan=2, sticky="w")
    
    def _clear_details(self):
        """Clear the details display."""
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        self.edit_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
    
    def _refresh_list(self):
        """Refresh the list of entries (with search filter)."""
        query = self.search_entry.get().strip()
        
        session = self.controller.get_session()
        db = session.get_database()
        if query:
            self.all_entries = db.search_entries(query)
        else:
            self.all_entries = db.get_all_entries()
        
        # Update listbox
        self.listbox.delete(0, tk.END)
        for entry in self.all_entries:
            display_text = f"{entry['service']} ({entry['username']})"
            self.listbox.insert(tk.END, display_text)
        
        # Clear details if no selection
        if not self.listbox.curselection():
            self._clear_details()
    
    def refresh(self):
        """Refresh screen when it becomes active."""
        self._refresh_list()
        session = self.controller.get_session()
        session.update_activity()

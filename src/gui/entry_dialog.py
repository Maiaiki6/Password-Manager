"""
Dialog for adding and editing password entries.
Includes password generation and strength indicator.
"""

import tkinter as tk
from tkinter import messagebox
from src.crypto import CryptoManager
from src.database import PasswordDatabase
from src.password_utils import PasswordUtils


class PasswordEntryDialog:
    """Dialog for adding or editing password entries."""
    
    def __init__(self, parent, controller, mode="add", entry_data=None):
        """
        Initialize entry dialog.
        
        Args:
            parent: Parent window
            controller: Main application controller
            mode: "add" or "edit"
            entry_data: Entry dict if editing (optional)
        """
        self.controller = controller
        self.mode = mode
        self.entry_data = entry_data
        
        self.top = tk.Toplevel(parent)
        self.top.title("Add Password Entry" if mode == "add" else "Edit Password Entry")
        self.top.geometry("500x550")
        self.top.resizable(False, False)
        
        # Title
        title = "Add New Password Entry" if mode == "add" else "Edit Password Entry"
        title_label = tk.Label(self.top, text=title, font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Main frame
        main_frame = tk.Frame(self.top, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Service name
        tk.Label(main_frame, text="Service/Website:", font=("Helvetica", 11, "bold"), bg="#f0f0f0").grid(row=0, column=0, sticky="w", pady=10)
        self.service_entry = tk.Entry(main_frame, font=("Helvetica", 11), width=30)
        self.service_entry.grid(row=0, column=1, sticky="ew", pady=10)
        
        if mode == "edit" and entry_data:
            self.service_entry.insert(0, entry_data['service'])
            self.service_entry.config(state=tk.DISABLED)  # Can't change service
        
        # Username
        tk.Label(main_frame, text="Username/Email:", font=("Helvetica", 11, "bold"), bg="#f0f0f0").grid(row=1, column=0, sticky="w", pady=10)
        self.username_entry = tk.Entry(main_frame, font=("Helvetica", 11), width=30)
        self.username_entry.grid(row=1, column=1, sticky="ew", pady=10)
        
        if mode == "edit" and entry_data:
            self.username_entry.insert(0, entry_data['username'])
        
        # Password
        tk.Label(main_frame, text="Password:", font=("Helvetica", 11, "bold"), bg="#f0f0f0").grid(row=2, column=0, sticky="w", pady=10)
        
        password_frame = tk.Frame(main_frame, bg="#f0f0f0")
        password_frame.grid(row=2, column=1, sticky="ew", pady=10)
        password_frame.grid_columnconfigure(0, weight=1)
        
        self.password_entry = tk.Entry(password_frame, font=("Helvetica", 11), width=30, show="*")
        self.password_entry.grid(row=0, column=0, sticky="ew", columnspan=2)
        self.password_entry.bind("<KeyRelease>", lambda e: self._update_strength())
        
        generate_btn = tk.Button(
            password_frame,
            text="Generate",
            command=self._generate_password,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            padx=10
        )
        generate_btn.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        show_btn = tk.Button(
            password_frame,
            text="👁 Show",
            command=self._toggle_password_visibility,
            bg="#9C27B0",
            fg="white",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            padx=10
        )
        show_btn.grid(row=1, column=1, sticky="e", pady=(5, 0))
        
        # Strength indicator
        tk.Label(main_frame, text="Password Strength:", font=("Helvetica", 10, "bold"), bg="#f0f0f0").grid(row=3, column=0, sticky="w", pady=10)
        
        strength_frame = tk.Frame(main_frame, bg="white")
        strength_frame.grid(row=3, column=1, sticky="ew", pady=10)
        strength_frame.grid_columnconfigure(0, weight=1)
        
        # Strength bar
        self.strength_canvas = tk.Canvas(strength_frame, height=20, bg="white", highlightthickness=0)
        self.strength_canvas.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Strength label
        self.strength_label = tk.Label(strength_frame, text="Enter a password", font=("Helvetica", 9), bg="white", fg="#666")
        self.strength_label.grid(row=1, column=0, sticky="w")
        
        # Feedback text
        self.feedback_label = tk.Label(main_frame, text="", font=("Helvetica", 9), bg="#f0f0f0", fg="#666", wraplength=350, justify=tk.LEFT)
        self.feedback_label.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        
        save_btn = tk.Button(
            button_frame,
            text="Save",
            command=self._save_entry,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.top.destroy,
            bg="#BDBDBD",
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _generate_password(self):
        """Generate a strong password."""
        password = PasswordUtils.generate_strong_password(length=16)
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, password)
        self._update_strength()
    
    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_entry.cget('show') == '*':
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='*')
    
    def _update_strength(self):
        """Update password strength indicator."""
        password = self.password_entry.get()
        
        if not password:
            self.strength_label.config(text="Enter a password", fg="#666")
            self.feedback_label.config(text="")
            self._draw_strength_bar(0, "")
            return
        
        strength_info = PasswordUtils.check_strength(password)
        score = strength_info['score']
        strength = strength_info['strength']
        feedback = strength_info['feedback']
        
        # Update strength label
        color_map = {
            'Very Weak': '#f44336',
            'Weak': '#ff9800',
            'Fair': '#ffc107',
            'Good': '#8bc34a',
            'Strong': '#4caf50',
            'Very Strong': '#1b5e20'
        }
        
        color = color_map.get(strength, '#666')
        self.strength_label.config(text=strength, fg=color)
        
        # Update feedback
        if feedback:
            feedback_text = "• " + "\n• ".join(feedback)
            self.feedback_label.config(text=feedback_text)
        else:
            self.feedback_label.config(text="Great password! 🎉")
        
        # Draw strength bar
        self._draw_strength_bar(score, color)
    
    def _draw_strength_bar(self, score, color):
        """Draw a visual strength bar."""
        self.strength_canvas.delete("all")
        
        if not color:
            color = "#d0d0d0"
        
        # Background
        self.strength_canvas.create_rectangle(0, 0, 350, 20, fill="#e0e0e0", outline="")
        
        # Filled portion (0-5 score)
        bar_width = (score / 5) * 350
        self.strength_canvas.create_rectangle(0, 0, bar_width, 20, fill=color, outline="")
    
    def _save_entry(self):
        """Save the password entry."""
        service = self.service_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not service:
            messagebox.showerror("Error", "Please enter a service name.")
            return
        
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return
        
        if not password:
            messagebox.showerror("Error", "Please enter a password.")
            return
        
        # Check password strength
        strength_info = PasswordUtils.check_strength(password)
        if not strength_info['meets_minimum']:
            messagebox.showwarning("Weak Password", "Password is too weak. Please use a stronger password.")
            return
        
        # Get master key
        session = self.controller.get_session()
        master_key = session.get_master_key()
        
        if not master_key:
            messagebox.showerror("Error", "Session expired. Please log in again.")
            self.top.destroy()
            return
        
        try:
            # Encrypt password
            encrypted = CryptoManager.encrypt_password(password, master_key)
            iv = encrypted['iv']
            ciphertext = encrypted['ciphertext']
            
            session = self.controller.get_session()
            db = session.get_database()
            
            if self.mode == "add":
                # Add new entry
                db.add_password_entry(service, username, iv, ciphertext)
                messagebox.showinfo("Success", f"Password for '{service}' added successfully!")
            else:
                # Update existing entry
                db.update_password_entry(service, username=username, iv=iv, ciphertext=ciphertext)
                messagebox.showinfo("Success", f"Password for '{service}' updated successfully!")
            
            session.update_activity()
            self.top.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entry: {str(e)}")

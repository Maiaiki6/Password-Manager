"""
Main application window orchestrator.
Manages switching between login and vault screens.
"""

import tkinter as tk
from tkinter import font as tkFont
from src.gui.login_screen import LoginScreen
from src.gui.vault_screen import VaultScreen
from src.session import SessionManager


class PasswordManagerApp:
    """Main application window."""
    
    def __init__(self, root):
        """
        Initialize the main application window.
        
        Args:
            root (tk.Tk): Root window
        """
        self.root = root
        self.root.title("Password Manager")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # Configure style
        self.root.configure(bg="#f0f0f0")
        
        # Create session manager
        self.session = SessionManager(timeout_minutes=15)
        
        # Container frame for switching screens
        self.container = tk.Frame(self.root)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        self.current_frame = None
        
        # Create frames (but don't show yet)
        self.login_screen = LoginScreen(self.container, self)
        self.vault_screen = VaultScreen(self.container, self)
        
        self.frames[LoginScreen] = self.login_screen
        self.frames[VaultScreen] = self.vault_screen
        
        # Show login screen first
        self.show_frame(LoginScreen)
    
    def show_frame(self, frame_class):
        """
        Switch to a different screen.
        
        Args:
            frame_class: The frame class to show
        """
        frame = self.frames[frame_class]
        self.current_frame = frame
        frame.tkraise()
        frame.refresh()
    
    def on_vault_locked(self):
        """Called when session times out or user locks vault."""
        self.session.logout()
        self.show_frame(LoginScreen)
    
    def get_session(self):
        """Get the session manager instance."""
        return self.session


def main():
    """Entry point for the application."""
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

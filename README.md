# Password Manager

A local password manager built in Python with a Tkinter GUI. Credentials are encrypted on disk using AES-256 and stored in a local SQLite vault file.

## Features

- Master password protected vault
- AES-256 encrypted password storage
- Add, update, delete, and search password entries
- Generate strong passwords
- Copy passwords to clipboard
- Select or create vault files
- Session timeout and lock support

## Requirements

- Python 3.10+
- `cryptography`
- `pyperclip`

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Build

```powershell
python -m PyInstaller --onefile --name password_manager main.py
```

The generated executable is available at `dist/password_manager.exe`.

## Project Structure

- `main.py` — application entry point
- `src/gui` — Tkinter user interface
- `src/crypto.py` — encryption and key derivation
- `src/database.py` — SQLite vault management
- `src/session.py` — authentication and session timeout
- `src/password_utils.py` — password generation and strength checks

## Notes

The vault file is stored locally and can be created or selected from the login screen. Keep the master password secure; it is required to unlock and decrypt stored credentials.

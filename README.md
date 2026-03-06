\# Password Manager



A secure desktop password manager built with Python and Tkinter.



\## Features

\- Master password authentication on launch

\- AES encrypted password storage via Fernet

\- Password generator with symbols, numbers, and letters

\- Search, edit, and delete saved entries

\- Copy password to clipboard from search results

\- Clean dark mode UI



\## Requirements

\- Python 3.x

\- cryptography

\- pyperclip



\## Installation

1\. Clone the repository

2\. Install dependencies: pip install -r requirements.txt

3\. Run: python main.py



\## Standalone Executable

A prebuilt Windows executable is available in the dist/ folder.

No Python installation required — just run main.exe.

Note: data.bin and master.json will be created in the same folder as the exe.

Keep these files alongside the exe to retain your saved passwords.



\## Notes

\- Your password data is stored locally in data.bin (encrypted)

\- master.json stores a hash of your master password

\- Neither file is included in this repository for security reasons


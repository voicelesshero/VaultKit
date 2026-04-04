# VaultKit
A secure personal vault for passwords, health information, and sensitive 
data. Built with Python, SQLite, and a live sync API. Designed for 
individuals who want one trustworthy place for everything that matters.

## Features

**Security**
- Master password authentication with Argon2id hashing
- AES-256-GCM encrypted local storage
- Zero knowledge cloud sync — server never sees your unencrypted data
- Session timeout with configurable duration
- HaveIBeenPwned breach checking via k-anonymity
- Auto clear clipboard 30 seconds after copying a password
- Password strength indicator
- Conflict detection — prevents an older device from overwriting a newer vault

**Vault Entry Types**
- Passwords
- Emergency info (blood type, allergies, medications, emergency contacts)
- Insurance policies
- Medications and prescriptions (brand and generic name)
- Secure notes
- Credit cards
- Identity info (passport, drivers license, SSN)
- WiFi passwords

**Sync**
- Encrypted vault sync across devices via live API
- Startup auto-sync — detects and uploads changes silently on launch
- Cross-device restore — recover your vault on a new device with your 
  master password
- Conflict detection with user prompt

**Usability**
- Profile system — enter your info once, auto-fills across all forms
- Search, edit, and delete saved entries
- Category system — Personal, Health, Finance, Family, Work
- Browseable vault with search and filter
- Password generator
- Copy to clipboard from search results
- Show/hide password toggle
- Settings — change master password, session timeout, sync management
- Clean dark mode UI

## Requirements
- Python 3.x
- See requirements.txt for full dependency list

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

## Standalone Executable
A prebuilt Windows executable is available in the Releases section.
No Python installation required — just download and run `main.exe`.

Note: `vaultkit.bin` and `master.json` will be created in the same 
folder as the exe. Keep these files to retain your vault data.

## Security Notes
- `vaultkit.bin` stores your AES-256-GCM encrypted vault
- `master.json` stores an Argon2id hash and key derivation salt
- `sync_config.json` stores your sync token — never your sync password
- Neither vault file is included in this repository
- Breach checking uses k-anonymity — your actual password never leaves 
  your device
- Cloud sync is zero knowledge — the server stores only encrypted bytes 
  it cannot read

## API
The sync backend is a Flask API deployed on Railway with PostgreSQL.
Located in the `api/` folder. Requires environment variables:
- `JWT_SECRET_KEY` — generate with `secrets.token_hex(32)`
- `FLASK_ENV=production`

## Roadmap
Native mobile apps (Android and iOS via Flutter) and Google Drive / 
OneDrive sync options are planned. See ROADMAP.md for full details.
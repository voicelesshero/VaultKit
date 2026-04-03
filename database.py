import sqlite3
import os
import hashlib
import base64

DB_PATH = "vaultkit.db"
ENCRYPTED_DB_PATH = "vaultkit.bin"


def make_key(password):
    raw = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(raw)


# ---------------------------- ENCRYPTION ------------------------------- #

def encrypt_db(cipher):
    """Encrypt the SQLite database file."""
    if not os.path.exists(DB_PATH):
        return
    with open(DB_PATH, "rb") as f:
        data = f.read()
    encrypted = cipher.encrypt(data)
    with open(ENCRYPTED_DB_PATH, "wb") as f:
        f.write(encrypted)
    os.remove(DB_PATH)


def decrypt_db(cipher):
    """Decrypt the database file for use."""
    if not os.path.exists(ENCRYPTED_DB_PATH):
        return False
    with open(ENCRYPTED_DB_PATH, "rb") as f:
        encrypted = f.read()
    decrypted = cipher.decrypt(encrypted)
    with open(DB_PATH, "wb") as f:
        f.write(decrypted)
    return True


# ---------------------------- CONNECTION ------------------------------- #

def get_connection():
    return sqlite3.connect(DB_PATH)


# ---------------------------- SETUP ------------------------------- #

def initialize_db(cipher):
    """
    Decrypt if exists, create tables if needed, always re-encrypt when done.
    Call this once at startup after master password is verified.
    """
    decrypt_db(cipher)

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT,
            date_of_birth TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_type TEXT NOT NULL,
            category TEXT DEFAULT 'Personal',
            label TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_accessed TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_value TEXT,
            FOREIGN KEY (entry_id) REFERENCES entries(id)
        )
    """)

    conn.commit()
    conn.close()
    encrypt_db(cipher)


# ---------------------------- USER ------------------------------- #

def create_user(cipher, master_hash):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (master_hash) VALUES (?)", (master_hash,))
    user_id = c.lastrowid
    c.execute("INSERT INTO profile (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    encrypt_db(cipher)
    return user_id


def get_user(cipher):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users LIMIT 1")
    user = c.fetchone()
    conn.close()
    encrypt_db(cipher)
    return user


# ---------------------------- PROFILE ------------------------------- #

def get_profile(cipher):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM profile LIMIT 1")
    profile = c.fetchone()
    conn.close()
    encrypt_db(cipher)
    return profile


def save_profile(cipher, user_id, full_name, dob, phone, email, address):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE profile SET full_name=?, date_of_birth=?, phone=?, email=?, address=?
        WHERE user_id=?
    """, (full_name, dob, phone, email, address, user_id))
    conn.commit()
    conn.close()
    encrypt_db(cipher)


# ---------------------------- ENTRIES ------------------------------- #

def add_entry(cipher, user_id, entry_type, category, label, fields_dict):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO entries (user_id, entry_type, category, label)
        VALUES (?, ?, ?, ?)
    """, (user_id, entry_type, category, label))

    entry_id = c.lastrowid

    for field_name, field_value in fields_dict.items():
        c.execute("""
            INSERT INTO fields (entry_id, field_name, field_value)
            VALUES (?, ?, ?)
        """, (entry_id, field_name, str(field_value)))

    conn.commit()
    conn.close()
    encrypt_db(cipher)
    return entry_id


def get_entry(cipher, entry_id):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM entries WHERE id=?", (entry_id,))
    entry = c.fetchone()

    c.execute("SELECT field_name, field_value FROM fields WHERE entry_id=?", (entry_id,))
    fields = dict(c.fetchall())

    # update last accessed
    c.execute("UPDATE entries SET last_accessed=datetime('now') WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    encrypt_db(cipher)
    return entry, fields


def get_all_entries(cipher, user_id):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE user_id=? ORDER BY label", (user_id,))
    entries = c.fetchall()
    conn.close()
    encrypt_db(cipher)
    return entries


def get_entries_by_type(cipher, user_id, entry_type):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE user_id=? AND entry_type=?", (user_id, entry_type))
    entries = c.fetchall()
    conn.close()
    encrypt_db(cipher)
    return entries


def get_entries_by_category(cipher, user_id, category):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE user_id=? AND category=?", (user_id, category))
    entries = c.fetchall()
    conn.close()
    encrypt_db(cipher)
    return entries


def search_entries(cipher, user_id, search_term):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE user_id=? AND label LIKE ?",
              (user_id, f"%{search_term}%"))
    entries = c.fetchall()
    conn.close()
    encrypt_db(cipher)
    return entries


def update_entry(cipher, entry_id, label=None, category=None, fields_dict=None):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()

    if label:
        c.execute("UPDATE entries SET label=?, updated_at=datetime('now') WHERE id=?",
                  (label, entry_id))
    if category:
        c.execute("UPDATE entries SET category=?, updated_at=datetime('now') WHERE id=?",
                  (category, entry_id))
    if fields_dict:
        for field_name, field_value in fields_dict.items():
            c.execute("""
                UPDATE fields SET field_value=? WHERE entry_id=? AND field_name=?
            """, (str(field_value), entry_id, field_name))

    conn.commit()
    conn.close()
    encrypt_db(cipher)


def delete_entry(cipher, entry_id):
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM fields WHERE entry_id=?", (entry_id,))
    c.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    encrypt_db(cipher)
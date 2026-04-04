import sqlite3
from config import SERVER_DB_PATH


def get_db():
    """Open a connection to the server database."""
    conn = sqlite3.connect(SERVER_DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, not just index
    return conn


def init_db():
    """Create tables if they don't exist. Called once at startup."""
    conn = get_db()
    c = conn.cursor()

    # Stores account credentials — email and hashed account password only.
    # The master password and vault contents never touch this table.
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL UNIQUE,
            password_hash TEXT  NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Stores each user's encrypted vault blob.
    # vault_data is the raw bytes of vaultkit.bin — the server never decrypts it.
    c.execute("""
        CREATE TABLE IF NOT EXISTS vaults (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL UNIQUE,
            vault_data    BLOB,
            last_modified TEXT    DEFAULT (datetime('now')),
            file_size     INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------- USER HELPERS ------------------------------- #

def create_user(email, password_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, password_hash))
    user_id = c.lastrowid
    # Create an empty vault slot for the new user right away.
    c.execute("INSERT INTO vaults (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def update_user_password(user_id, new_password_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM vaults WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# ---------------------------- VAULT HELPERS ------------------------------- #

def get_vault(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM vaults WHERE user_id = ?", (user_id,))
    vault = c.fetchone()
    conn.close()
    return vault


def save_vault(user_id, vault_data):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE vaults
        SET vault_data    = ?,
            last_modified = datetime('now'),
            file_size     = ?
        WHERE user_id = ?
    """, (vault_data, len(vault_data), user_id))
    conn.commit()
    conn.close()

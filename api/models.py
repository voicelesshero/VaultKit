import sqlite3
from config import DATABASE_URL, SERVER_DB_PATH

# When DATABASE_URL is set (Railway production), use PostgreSQL.
# Otherwise fall back to local SQLite for development.
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras


# ---------------------------- CONNECTION ------------------------------- #

def get_db():
    """Open a connection to the server database.
    Returns a connection whose cursors yield rows as dicts."""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(SERVER_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def _cursor(conn):
    """Return a dict-based cursor for whichever database is in use."""
    if USE_POSTGRES:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


# SQL placeholders and syntax differ between the two engines.
P = "%s" if USE_POSTGRES else "?"


def _now():
    return "NOW()" if USE_POSTGRES else "datetime('now')"


# ---------------------------- SCHEMA ------------------------------- #

def init_db():
    """Create tables if they don't exist. Called once at startup."""
    conn = get_db()
    c = _cursor(conn)

    if USE_POSTGRES:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                email         TEXT   NOT NULL UNIQUE,
                password_hash TEXT   NOT NULL,
                created_at    TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS vaults (
                id            SERIAL PRIMARY KEY,
                user_id       INTEGER NOT NULL UNIQUE,
                vault_data    BYTEA,
                last_modified TIMESTAMPTZ DEFAULT NOW(),
                file_size     INTEGER DEFAULT 0,
                checksum      TEXT,
                kdf_salt      TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        try:
            c.execute("ALTER TABLE vaults ADD COLUMN kdf_salt TEXT")
            conn.commit()
        except Exception:
            pass
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS vaults (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL UNIQUE,
                vault_data    BLOB,
                last_modified TEXT    DEFAULT (datetime('now')),
                file_size     INTEGER DEFAULT 0,
                checksum      TEXT,
                kdf_salt      TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        # Migrate existing SQLite databases that predate these columns.
        for col in ["checksum TEXT", "kdf_salt TEXT"]:
            try:
                c.execute(f"ALTER TABLE vaults ADD COLUMN {col}")
            except Exception:
                pass

    conn.commit()
    conn.close()


# ---------------------------- USER HELPERS ------------------------------- #

def create_user(email, password_hash):
    conn = get_db()
    c = _cursor(conn)

    if USE_POSTGRES:
        c.execute(
            f"INSERT INTO users (email, password_hash) VALUES ({P}, {P}) RETURNING id",
            (email, password_hash)
        )
        user_id = c.fetchone()["id"]
    else:
        c.execute(
            f"INSERT INTO users (email, password_hash) VALUES ({P}, {P})",
            (email, password_hash)
        )
        user_id = c.lastrowid

    c.execute(f"INSERT INTO vaults (user_id) VALUES ({P})", (user_id,))
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email):
    conn = get_db()
    c = _cursor(conn)
    c.execute(f"SELECT * FROM users WHERE email = {P}", (email,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    conn = get_db()
    c = _cursor(conn)
    c.execute(f"SELECT * FROM users WHERE id = {P}", (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_password(user_id, new_password_hash):
    conn = get_db()
    c = _cursor(conn)
    c.execute(
        f"UPDATE users SET password_hash = {P} WHERE id = {P}",
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_db()
    c = _cursor(conn)
    c.execute(f"DELETE FROM vaults WHERE user_id = {P}", (user_id,))
    c.execute(f"DELETE FROM users WHERE id = {P}", (user_id,))
    conn.commit()
    conn.close()


# ---------------------------- VAULT HELPERS ------------------------------- #

def get_vault(user_id):
    conn = get_db()
    c = _cursor(conn)
    c.execute(f"SELECT * FROM vaults WHERE user_id = {P}", (user_id,))
    vault = c.fetchone()
    conn.close()
    return dict(vault) if vault else None


def save_vault(user_id, vault_data, checksum, kdf_salt=None):
    conn = get_db()
    c = _cursor(conn)
    c.execute(
        f"""
        UPDATE vaults
        SET vault_data    = {P},
            last_modified = {_now()},
            file_size     = {P},
            checksum      = {P},
            kdf_salt      = {P}
        WHERE user_id     = {P}
        """,
        (vault_data, len(vault_data), checksum, kdf_salt, user_id)
    )
    conn.commit()
    conn.close()

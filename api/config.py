import os

# Secret key Flask uses to sign JWT tokens.
# In production this must come from an environment variable — never hardcoded.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-before-deploy")

# How long a login token stays valid before the user has to log in again.
JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24

# Path to the server-side SQLite database.
# This stores accounts and vault blobs — completely separate from vaultkit.db.
SERVER_DB_PATH = os.path.join(os.path.dirname(__file__), "server.db")

# Maximum vault file size accepted on upload (10 MB).
MAX_VAULT_SIZE_BYTES = 10 * 1024 * 1024

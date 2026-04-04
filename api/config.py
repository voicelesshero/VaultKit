import os
from dotenv import load_dotenv

# Load .env file when running locally. In production (Railway/Render)
# environment variables are set on the platform — load_dotenv() is a no-op.
load_dotenv()

FLASK_ENV = os.environ.get("FLASK_ENV", "development")
IS_PRODUCTION = FLASK_ENV == "production"

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-before-deploy")

# Refuse to start in production with a placeholder secret.
# This is a hard fail — a weak secret in production is a critical vulnerability.
if IS_PRODUCTION and JWT_SECRET_KEY == "dev-secret-change-before-deploy":
    raise RuntimeError(
        "JWT_SECRET_KEY must be set to a strong random value in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

JWT_ACCESS_TOKEN_EXPIRES_HOURS = 24

SERVER_DB_PATH = os.path.join(os.path.dirname(__file__), "server.db")

MAX_VAULT_SIZE_BYTES = 10 * 1024 * 1024

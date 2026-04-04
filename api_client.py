import requests
import json
import os
import hashlib


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# Change this to your deployed server URL when hosting publicly.
API_BASE_URL = "http://127.0.0.1:5000"
SYNC_CONFIG_PATH = "sync_config.json"
VAULT_PATH = "vaultkit.bin"


# ---------------------------- SYNC CONFIG ------------------------------- #

def load_sync_config():
    try:
        with open(SYNC_CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_sync_config(data):
    with open(SYNC_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def is_logged_in():
    return bool(load_sync_config().get("token"))


def get_token():
    return load_sync_config().get("token")


def get_account_email():
    return load_sync_config().get("email")


def get_last_synced():
    return load_sync_config().get("last_synced")


def _auth_headers():
    return {"Authorization": f"Bearer {get_token()}"}


def _update_sync_timestamps(last_modified):
    config = load_sync_config()
    config["last_synced"] = last_modified
    config["last_known_server_modified"] = last_modified
    save_sync_config(config)


# ---------------------------- AUTH ------------------------------- #

def register(email, password):
    """Create a new sync account. Returns (data_dict, status_code)."""
    try:
        r = requests.post(f"{API_BASE_URL}/auth/register",
                          json={"email": email, "password": password}, timeout=10)
        data = r.json()
        if r.status_code == 201:
            config = {"email": email, "token": data["token"]}
            save_sync_config(config)
        return data, r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach sync server."}, 0


def login(email, password):
    """Log in to sync account. Returns (data_dict, status_code)."""
    try:
        r = requests.post(f"{API_BASE_URL}/auth/login",
                          json={"email": email, "password": password}, timeout=10)
        data = r.json()
        if r.status_code == 200:
            config = load_sync_config()
            config["email"] = email
            config["token"] = data["token"]
            save_sync_config(config)
        return data, r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach sync server."}, 0


def logout():
    """Invalidate token on server and clear local sync config."""
    token = get_token()
    if token:
        try:
            requests.post(f"{API_BASE_URL}/auth/logout",
                          headers=_auth_headers(), timeout=5)
        except Exception:
            pass  # clear locally regardless
    save_sync_config({})


# ---------------------------- VAULT SYNC ------------------------------- #

def get_vault_status():
    """Check server vault metadata. Returns (data_dict, status_code).
    status_code 0 means server is unreachable."""
    try:
        r = requests.get(f"{API_BASE_URL}/vault/status",
                         headers=_auth_headers(), timeout=10)
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return None, 0


def upload_vault():
    """Upload local vaultkit.bin to server with conflict check.
    Sends as multipart/form-data — universally supported by proxies.
    Returns (data_dict, status_code)."""
    if not os.path.exists(VAULT_PATH):
        return {"error": "No local vault file found."}, 404

    config = load_sync_config()
    last_known = config.get("last_known_server_modified")

    try:
        with open(VAULT_PATH, "rb") as f:
            vault_data = f.read()

        files = {"vault": ("vaultkit.bin", vault_data, "application/octet-stream")}
        data = {}
        if last_known:
            data["last_known_modified"] = last_known

        r = requests.post(f"{API_BASE_URL}/vault", files=files, data=data,
                          headers=_auth_headers(), timeout=30)
        if r.status_code == 200:
            _update_sync_timestamps(r.json()["last_modified"])
        return r.json(), r.status_code
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach sync server."}, 0


def download_vault():
    """Download vault blob from server and overwrite local vaultkit.bin.
    Verifies the SHA256 checksum from the response header before writing.
    Returns (success: bool, error_message: str | None)."""
    try:
        r = requests.get(f"{API_BASE_URL}/vault",
                         headers=_auth_headers(), timeout=30)
        if r.status_code == 200:
            vault_bytes = r.content
            expected_checksum = r.headers.get("X-Vault-Checksum")

            if expected_checksum:
                actual_checksum = _sha256(vault_bytes)
                if actual_checksum != expected_checksum:
                    return False, "Vault download corrupted — checksum mismatch. Please try again."

            with open(VAULT_PATH, "wb") as f:
                f.write(vault_bytes)

            # Re-check status to get the authoritative last_modified timestamp.
            status, code = get_vault_status()
            if code == 200 and status:
                _update_sync_timestamps(status["last_modified"])
            return True, None
        return False, r.json().get("error", "Download failed.")
    except requests.exceptions.ConnectionError:
        return False, "Could not reach sync server."


def force_upload_after_rekey():
    """Upload vault unconditionally after a master password change.
    Skips the last_known_modified conflict field so it always overwrites
    the server copy — the local rekeyed vault is authoritative."""
    if not is_logged_in() or not os.path.exists(VAULT_PATH):
        return
    try:
        with open(VAULT_PATH, "rb") as f:
            vault_data = f.read()
        files = {"vault": ("vaultkit.bin", vault_data, "application/octet-stream")}
        r = requests.post(f"{API_BASE_URL}/vault", files=files,
                          headers=_auth_headers(), timeout=30)
        if r.status_code == 200:
            _update_sync_timestamps(r.json()["last_modified"])
    except Exception:
        pass  # rekey succeeded locally regardless; user can sync manually

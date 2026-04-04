from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import hashlib
import io
import models
from config import MAX_VAULT_SIZE_BYTES

sync_bp = Blueprint("sync", __name__)


def _get_current_user():
    """Resolve the JWT identity (email) to a user row.
    Returns None if identity is missing or user is not found."""
    email = get_jwt_identity()
    if not email:
        return None
    return models.get_user_by_email(email)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@sync_bp.route("/vault/status", methods=["GET"])
@jwt_required()
def vault_status():
    """Return metadata only — lets the client check if a sync is needed
    without downloading the full vault blob."""
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found."}), 401
    vault = models.get_vault(user["id"])

    if not vault or not vault["vault_data"]:
        return jsonify({"has_vault": False}), 200

    return jsonify({
        "has_vault": True,
        "last_modified": str(vault["last_modified"]),
        "file_size": vault["file_size"],
        "checksum": vault["checksum"],
        "kdf_salt": vault["kdf_salt"]
    }), 200


@sync_bp.route("/vault", methods=["GET"])
@jwt_required()
def download_vault():
    """Return the user's encrypted vault blob as raw bytes.
    Uses make_response with explicit bytes — send_file can apply content
    encoding that corrupts binary data. Checksum is included in a response
    header so the client can verify the file arrived intact."""
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found."}), 401
    vault = models.get_vault(user["id"])

    if not vault or not vault["vault_data"]:
        return jsonify({"error": "No vault found for this account."}), 404

    # Explicit bytes() cast handles PostgreSQL BYTEA returning a memoryview.
    vault_bytes = bytes(vault["vault_data"])
    checksum = vault["checksum"] or _sha256(vault_bytes)

    response = send_file(
        io.BytesIO(vault_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name="vaultkit.bin"
    )
    response.headers["X-Vault-Checksum"] = checksum
    if vault["kdf_salt"]:
        response.headers["X-KDF-Salt"] = vault["kdf_salt"]
    return response


@sync_bp.route("/vault", methods=["POST"])
@jwt_required()
def upload_vault():
    """Accept a new encrypted vault blob and store it.
    Expects multipart/form-data with a 'vault' file field.
    POST + multipart is universally supported by proxies and WSGI servers."""
    user = _get_current_user()
    if not user:
        return jsonify({"error": "User not found."}), 401

    if "vault" not in request.files:
        return jsonify({"error": "No vault file in request."}), 400

    vault_file = request.files["vault"]
    vault_data = vault_file.read()

    if not vault_data:
        return jsonify({"error": "No vault data received."}), 400

    if len(vault_data) > MAX_VAULT_SIZE_BYTES:
        return jsonify({"error": "Vault exceeds maximum allowed size."}), 413

    # Conflict check — if the client's last_known_modified doesn't match
    # the server, another device uploaded more recently.
    client_last_known = request.form.get("last_known_modified")
    if client_last_known:
        existing = models.get_vault(user["id"])
        if existing and existing["vault_data"] and str(existing["last_modified"]) != client_last_known:
            return jsonify({
                "error": "conflict",
                "message": "Vault was updated on another device.",
                "server_last_modified": str(existing["last_modified"])
            }), 409

    checksum = _sha256(vault_data)
    kdf_salt = request.form.get("kdf_salt")
    models.save_vault(user["id"], vault_data, checksum, kdf_salt)
    updated = models.get_vault(user["id"])

    return jsonify({
        "message": "Vault uploaded successfully.",
        "last_modified": str(updated["last_modified"]),
        "file_size": updated["file_size"],
        "checksum": checksum
    }), 200

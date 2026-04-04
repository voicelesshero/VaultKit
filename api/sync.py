from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
import hashlib
import models
from config import MAX_VAULT_SIZE_BYTES

sync_bp = Blueprint("sync", __name__)


def _get_current_user():
    """Resolve the JWT identity (email) to a user row."""
    email = get_jwt_identity()
    return models.get_user_by_email(email)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@sync_bp.route("/vault/status", methods=["GET"])
@jwt_required()
def vault_status():
    """Return metadata only — lets the client check if a sync is needed
    without downloading the full vault blob."""
    user = _get_current_user()
    vault = models.get_vault(user["id"])

    if not vault or not vault["vault_data"]:
        return jsonify({"has_vault": False}), 200

    return jsonify({
        "has_vault": True,
        "last_modified": vault["last_modified"],
        "file_size": vault["file_size"],
        "checksum": vault["checksum"]
    }), 200


@sync_bp.route("/vault", methods=["GET"])
@jwt_required()
def download_vault():
    """Return the user's encrypted vault blob as raw bytes.
    Uses make_response with explicit bytes — send_file can apply content
    encoding that corrupts binary data. Checksum is included in a response
    header so the client can verify the file arrived intact."""
    user = _get_current_user()
    vault = models.get_vault(user["id"])

    if not vault or not vault["vault_data"]:
        return jsonify({"error": "No vault found for this account."}), 404

    # Ensure we have raw bytes — sqlite3 returns BLOB as bytes, but be explicit.
    vault_bytes = bytes(vault["vault_data"])

    response = make_response(vault_bytes)
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Content-Disposition"] = "attachment; filename=vaultkit.bin"
    response.headers["Content-Length"] = str(len(vault_bytes))
    response.headers["X-Vault-Checksum"] = vault["checksum"] or _sha256(vault_bytes)
    return response


@sync_bp.route("/vault", methods=["PUT"])
@jwt_required()
def upload_vault():
    """Accept a new encrypted vault blob and store it.
    The client sends the raw bytes of vaultkit.bin — nothing is decrypted here."""
    user = _get_current_user()

    # request.stream.read() gets raw bytes regardless of Content-Type header.
    vault_data = request.stream.read()

    if not vault_data:
        return jsonify({"error": "No vault data received."}), 400

    if len(vault_data) > MAX_VAULT_SIZE_BYTES:
        return jsonify({"error": "Vault exceeds maximum allowed size."}), 413

    # Conflict check — if the client's last_known_modified doesn't match
    # the server, another device uploaded more recently.
    client_last_known = request.headers.get("X-Last-Modified")
    if client_last_known:
        existing = models.get_vault(user["id"])
        if existing and existing["vault_data"] and existing["last_modified"] != client_last_known:
            return jsonify({
                "error": "conflict",
                "message": "Vault was updated on another device.",
                "server_last_modified": existing["last_modified"]
            }), 409

    checksum = _sha256(vault_data)
    models.save_vault(user["id"], vault_data, checksum)
    updated = models.get_vault(user["id"])

    return jsonify({
        "message": "Vault uploaded successfully.",
        "last_modified": updated["last_modified"],
        "file_size": updated["file_size"],
        "checksum": checksum
    }), 200

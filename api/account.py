from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import models

account_bp = Blueprint("account", __name__)
ph = PasswordHasher()


@account_bp.route("/account/password", methods=["PATCH"])
@jwt_required()
def change_password():
    """Change the account password (not the master password).
    This only affects who can log in to the sync server — the vault
    encryption is untouched."""
    email = get_jwt_identity()
    user = models.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found."}), 401
    data = request.get_json()

    if not data or not data.get("current_password") or not data.get("new_password"):
        return jsonify({"error": "current_password and new_password are required."}), 400

    try:
        ph.verify(user["password_hash"], data["current_password"])
    except VerifyMismatchError:
        return jsonify({"error": "Current password is incorrect."}), 401

    new_hash = ph.hash(data["new_password"])
    models.update_user_password(user["id"], new_hash)

    return jsonify({"message": "Account password updated."}), 200


@account_bp.route("/account", methods=["DELETE"])
@jwt_required()
def delete_account():
    """Permanently delete the account and vault blob from the server.
    The user's local vault is not affected — this only removes the
    server-side copy."""
    email = get_jwt_identity()
    user = models.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found."}), 401
    data = request.get_json()

    if not data or not data.get("password"):
        return jsonify({"error": "Password confirmation required."}), 400

    try:
        ph.verify(user["password_hash"], data["password"])
    except VerifyMismatchError:
        return jsonify({"error": "Incorrect password."}), 401

    models.delete_user(user["id"])
    return jsonify({"message": "Account and vault data deleted from server."}), 200

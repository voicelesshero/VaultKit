from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import models

auth_bp = Blueprint("auth", __name__)
ph = PasswordHasher()


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required."}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    if models.get_user_by_email(email):
        return jsonify({"error": "An account with that email already exists."}), 409

    password_hash = ph.hash(password)
    models.create_user(email, password_hash)

    # Log them in immediately after registering.
    token = create_access_token(identity=email)
    return jsonify({"message": "Account created.", "token": token}), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required."}), 400

    email = data["email"].strip().lower()
    password = data["password"]

    user = models.get_user_by_email(email)

    # Use the same error message whether the email or password is wrong.
    # This prevents an attacker from learning which accounts exist.
    invalid_msg = {"error": "Invalid email or password."}

    if not user:
        return jsonify(invalid_msg), 401

    try:
        ph.verify(user["password_hash"], password)
    except VerifyMismatchError:
        return jsonify(invalid_msg), 401

    token = create_access_token(identity=email)
    return jsonify({"message": "Login successful.", "token": token}), 200


@auth_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    # JWT tokens are stateless — there's nothing to delete server-side.
    # The client is responsible for discarding the token.
    # Full token revocation (a blocklist) can be added later if needed.
    return jsonify({"message": "Logged out. Discard your token."}), 200

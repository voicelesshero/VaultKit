from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import re
import models

auth_bp = Blueprint("auth", __name__)
ph = PasswordHasher()

# Limiter instance — registered onto the app in app.py.
# Defined here so auth routes can reference it directly.
limiter = Limiter(key_func=get_remote_address)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def _validate(email, password):
    """Returns an error string or None if valid."""
    if not email or not password:
        return "Email and password are required."
    if not EMAIL_RE.match(email):
        return "Invalid email address."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None


@auth_bp.route("/auth/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    err = _validate(email, password)
    if err:
        return jsonify({"error": err}), 400

    if models.get_user_by_email(email):
        return jsonify({"error": "An account with that email already exists."}), 409

    password_hash = ph.hash(password)
    models.create_user(email, password_hash)

    token = create_access_token(identity=email)
    return jsonify({"message": "Account created.", "token": token}), 201


@auth_bp.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    err = _validate(email, password)
    if err:
        return jsonify({"error": err}), 400

    user = models.get_user_by_email(email)

    # Same message whether email or password is wrong —
    # prevents an attacker from learning which accounts exist.
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
    # JWT tokens are stateless — the client discards the token.
    # A server-side blocklist can be added later if needed.
    return jsonify({"message": "Logged out. Discard your token."}), 200

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
import models

emergency_bp = Blueprint("emergency", __name__)

_CORS_ORIGIN = "https://vaultkit-emergency.pages.dev"

_FIELDS = [
    "full_name", "blood_type", "allergies", "medications",
    "medical_conditions", "emergency_contact", "emergency_contact_phone",
    "primary_doctor", "doctor_phone", "hospital_preference",
    "insurance_provider", "policy_number", "critical_info",
]


# ── POST /emergency/share ─────────────────────────────────────────────────────
# Requires JWT. Accepts emergency fields as JSON. Creates or updates the share
# record for this user and returns the stable share_id UUID.

@emergency_bp.route("/emergency/share", methods=["POST"])
@jwt_required()
def create_or_update_share():
    email = get_jwt_identity()
    user = models.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json(silent=True) or {}
    fields = {f: (data.get(f) or "") for f in _FIELDS}

    share_id = models.upsert_emergency_share(user["id"], fields)
    return jsonify({"share_id": share_id}), 200


# ── GET /emergency/<share_id> ─────────────────────────────────────────────────
# No auth required. Returns emergency fields as plain JSON.
# CORS allowed from the Cloudflare emergency page only.

@emergency_bp.route("/emergency/<share_id>", methods=["GET"])
def get_share(share_id):
    share = models.get_emergency_share(share_id)
    if not share:
        return jsonify({"error": "Not found."}), 404

    payload = {f: (share.get(f) or "") for f in _FIELDS}
    response = make_response(jsonify(payload), 200)
    response.headers["Access-Control-Allow-Origin"] = _CORS_ORIGIN
    return response


# ── DELETE /emergency/share ───────────────────────────────────────────────────
# Requires JWT. Permanently deletes the user's emergency share record,
# invalidating the share_id link.

@emergency_bp.route("/emergency/share", methods=["DELETE"])
@jwt_required()
def delete_share():
    email = get_jwt_identity()
    user = models.get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found."}), 404

    models.delete_emergency_share(user["id"])
    return jsonify({"message": "Emergency share deleted."}), 200

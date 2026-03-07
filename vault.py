import json
import hashlib
import base64
from cryptography.fernet import Fernet

ENTRY_TYPES = {
    "password": ["website", "email", "password"],
    "emergency": [
        "full_name",
        "blood_type",
        "allergies",
        "medications",
        "primary_doctor",
        "doctor_phone",
        "emergency_contact",
        "emergency_contact_phone",
        "insurance_provider",
        "policy_number",
        "medical_conditions",
        "hospital_preference",
        "notes"
    ]
}

def make_key(password):
    raw = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(raw)

def get_cipher(password):
    return Fernet(make_key(password))

def load_vault(cipher):
    try:
        with open("data.bin", "rb") as f:
            return json.loads(cipher.decrypt(f.read()).decode())
    except FileNotFoundError:
        return {}

def save_vault(cipher, data):
    with open("data.bin", "wb") as f:
        f.write(cipher.encrypt(json.dumps(data, indent=4).encode()))

def add_entry(cipher, entry_type, entry_id, fields):
    data = load_vault(cipher)
    data[entry_id] = {"type": entry_type, **fields}
    save_vault(cipher, data)

def get_entry(cipher, entry_id):
    data = load_vault(cipher)
    return data.get(entry_id)

def update_entry(cipher, entry_id, fields):
    data = load_vault(cipher)
    if entry_id in data:
        data[entry_id].update(fields)
        save_vault(cipher, data)

def delete_entry(cipher, entry_id):
    data = load_vault(cipher)
    if entry_id in data:
        del data[entry_id]
        save_vault(cipher, data)

def get_all_entries(cipher):
    return load_vault(cipher)

def get_entries_by_type(cipher, entry_type):
    data = load_vault(cipher)
    return {k: v for k, v in data.items() if v.get("type") == entry_type}
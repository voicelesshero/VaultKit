from database import (
    initialize_db, create_user, get_user,
    get_profile, save_profile,
    add_entry as db_add_entry,
    get_entry as db_get_entry,
    get_all_entries as db_get_all_entries,
    get_entries_by_type as db_get_entries_by_type,
    get_entries_by_category as db_get_entries_by_category,
    search_entries as db_search_entries,
    update_entry as db_update_entry,
    delete_entry as db_delete_entry,
)

ENTRY_TYPES = {
    "password": ["website", "email", "password"],
    "emergency": [
        "full_name", "cell_phone", "home_phone",
        "blood_type", "allergies", "medications",
        "primary_doctor", "doctor_phone", "emergency_contact",
        "emergency_contact_phone", "insurance_provider", "policy_number",
        "medical_conditions", "hospital_preference", "notes"
    ],
    "insurance": [
        "policy_name", "provider", "policy_number", "group_number",
        "member_id", "primary_holder", "provider_phone", "effective_date",
        "expiration_date", "copay", "deductible", "website", "notes"
    ],
    "medication": [
        "brand_name", "generic_name", "dosage", "frequency", "doctor",
        "pharmacy", "pharmacy_phone", "rx_number", "refills", "start_date",
        "conditions_treated", "side_effects", "notes"
    ],
    "note": ["title", "category", "content"],
    "credit_card": [
        "label", "cardholder_name", "card_number", "expiry", "cvv",
        "billing_address", "card_type", "bank", "phone", "url", "pin", "notes"
    ],
    "identity": [
        "label", "full_name", "dob", "ssn", "passport_number",
        "passport_expiry", "license_number", "license_expiry",
        "license_state", "address", "phone", "email", "notes"
    ],
    "wifi": [
        "ssid", "password", "security_type", "router_brand",
        "router_ip", "admin_username", "admin_password", "location", "notes"
    ],
}

# ---------------------------- VAULT SETUP ------------------------------- #

def setup_vault(cipher, master_hash):
    """Call on first run after master password is created."""
    initialize_db(cipher)
    user = get_user(cipher)
    if not user:
        create_user(cipher, master_hash)

def load_vault(cipher):
    """Initialize database on login."""
    initialize_db(cipher)

# ---------------------------- USER / PROFILE ------------------------------- #

def get_current_user(cipher):
    return get_user(cipher)

def get_user_profile(cipher):
    return get_profile(cipher)

def update_user_profile(cipher, user_id, full_name, dob, phone, email, address):
    save_profile(cipher, user_id, full_name, dob, phone, email, address)

# ---------------------------- ENTRIES ------------------------------- #

def add_entry(cipher, entry_type, entry_id, fields_dict):
    """
    Maintains compatibility with existing form code.
    entry_id becomes the label in the new schema.
    """
    user = get_user(cipher)
    if not user:
        return
    user_id = user[0]
    category = fields_dict.pop("category", "Personal")
    db_add_entry(cipher, user_id, entry_type, category, entry_id, fields_dict)


def get_entry(cipher, label):
    """Returns a flat dict of fields for a given label, same as before."""
    user = get_user(cipher)
    if not user:
        return None
    user_id = user[0]

    from database import decrypt_db, encrypt_db, get_connection
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM entries WHERE user_id=? AND label=?", (user_id, label))
    row = c.fetchone()
    conn.close()
    encrypt_db(cipher)

    if not row:
        return None

    entry, fields = db_get_entry(cipher, row[0])
    fields["type"] = entry[2]  # entry_type column
    fields["category"] = entry[3]  # category column
    return fields


def get_all_entries(cipher):
    """Returns a dict keyed by label, same structure as before."""
    user = get_user(cipher)
    if not user:
        return {}
    user_id = user[0]

    entries = db_get_all_entries(cipher, user_id)
    result = {}

    for entry in entries:
        entry_id = entry[0]
        label = entry[4]
        _, fields = db_get_entry(cipher, entry_id)
        fields["type"] = entry[2]
        fields["category"] = entry[3]
        result[label] = fields

    return result


def update_entry(cipher, label, fields_dict):
    """Update fields for an entry by label."""
    user = get_user(cipher)
    if not user:
        return
    user_id = user[0]

    from database import decrypt_db, encrypt_db, get_connection
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM entries WHERE user_id=? AND label=?", (user_id, label))
    row = c.fetchone()
    conn.close()
    encrypt_db(cipher)

    if row:
        db_update_entry(cipher, row[0], fields_dict=fields_dict)


def delete_entry(cipher, label):
    """Delete an entry by label."""
    user = get_user(cipher)
    if not user:
        return
    user_id = user[0]

    from database import decrypt_db, encrypt_db, get_connection
    decrypt_db(cipher)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM entries WHERE user_id=? AND label=?", (user_id, label))
    row = c.fetchone()
    conn.close()
    encrypt_db(cipher)

    if row:
        db_delete_entry(cipher, row[0])


def get_entries_by_type(cipher, entry_type):
    user = get_user(cipher)
    if not user:
        return {}
    user_id = user[0]
    entries = db_get_entries_by_type(cipher, user_id, entry_type)
    result = {}
    for entry in entries:
        label = entry[4]
        _, fields = db_get_entry(cipher, entry[0])
        fields["type"] = entry[2]
        fields["category"] = entry[3]
        result[label] = fields
    return result


def search_vault(cipher, search_term):
    user = get_user(cipher)
    if not user:
        return {}
    user_id = user[0]
    entries = db_search_entries(cipher, user_id, search_term)
    result = {}
    for entry in entries:
        label = entry[4]
        _, fields = db_get_entry(cipher, entry[0])
        fields["type"] = entry[2]
        fields["category"] = entry[3]
        result[label] = fields
    return result
from tkinter import *
from tkinter import messagebox
from vault import add_entry, get_entry, update_entry

MULTILINE_FIELDS = {"notes", "side_effects", "conditions_treated"}

# ---------------------------- INSURANCE ------------------------------- #

def open_insurance_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit Insurance" if is_edit else "Add Insurance Policy")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Policy Name / Label", "policy_name"),
        ("Insurance Provider", "provider"),
        ("Policy Number", "policy_number"),
        ("Group Number", "group_number"),
        ("Member ID", "member_id"),
        ("Primary Holder", "primary_holder"),
        ("Provider Phone", "provider_phone"),
        ("Effective Date", "effective_date"),
        ("Expiration Date", "expiration_date"),
        ("Copay", "copay"),
        ("Deductible", "deductible"),
        ("Website / Portal", "website"),
        ("Notes", "notes"),
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        Label(form, text=f"{label}:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=i, column=0, sticky="ne", padx=(0, 10), pady=4)

        if key in MULTILINE_FIELDS:
            widget = Text(form, width=40, height=4, bg=ENTRY_BG, fg=ENTRY_FG,
                          insertbackground=ENTRY_FG, relief="flat", font=FONT)
            widget.grid(row=i, column=1, sticky="ew", pady=4)
            if existing and existing.get(key):
                widget.insert("1.0", existing.get(key, ""))
        else:
            widget = Entry(form, width=40, bg=ENTRY_BG, fg=ENTRY_FG,
                           insertbackground=ENTRY_FG, relief="flat", font=FONT)
            widget.grid(row=i, column=1, sticky="ew", ipady=4, pady=4)
            if existing and existing.get(key):
                widget.insert(0, existing.get(key, ""))

        entries[key] = widget

    def save_insurance():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["policy_name"]:
            messagebox.showerror("Error", "Policy name is required.")
            return

        entry_key = entry_id if is_edit else data['policy_name']

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "insurance", entry_key, {**data, "category": "Health"})

        messagebox.showinfo("Saved", "Insurance policy saved.")
        form.destroy()

    Button(form, text="Save Insurance", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_insurance).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)


# ---------------------------- MEDICATIONS ------------------------------- #

def open_medication_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit Medication" if is_edit else "Add Medication")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Brand Name", "brand_name"),
        ("Generic Name", "generic_name"),
        ("Dosage", "dosage"),
        ("Frequency", "frequency"),
        ("Prescribing Doctor", "doctor"),
        ("Pharmacy", "pharmacy"),
        ("Pharmacy Phone", "pharmacy_phone"),
        ("Prescription Number", "rx_number"),
        ("Refills Remaining", "refills"),
        ("Start Date", "start_date"),
        ("Conditions Treated", "conditions_treated"),
        ("Side Effects", "side_effects"),
        ("Notes", "notes"),
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        Label(form, text=f"{label}:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=i, column=0, sticky="ne", padx=(0, 10), pady=4)

        if key in MULTILINE_FIELDS:
            widget = Text(form, width=40, height=4, bg=ENTRY_BG, fg=ENTRY_FG,
                          insertbackground=ENTRY_FG, relief="flat", font=FONT)
            widget.grid(row=i, column=1, sticky="ew", pady=4)
            if existing and existing.get(key):
                widget.insert("1.0", existing.get(key, ""))
        else:
            widget = Entry(form, width=40, bg=ENTRY_BG, fg=ENTRY_FG,
                           insertbackground=ENTRY_FG, relief="flat", font=FONT)
            widget.grid(row=i, column=1, sticky="ew", ipady=4, pady=4)
            if existing and existing.get(key):
                widget.insert(0, existing.get(key, ""))

        entries[key] = widget

    def save_medication():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["brand_name"] and not data["generic_name"]:
            messagebox.showerror("Error", "At least one medication name is required.")
            return

        entry_key = entry_id if is_edit else (data['brand_name'] or data['generic_name'])

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "medication", entry_key, {**data, "category": "Health"})

        messagebox.showinfo("Saved", "Medication saved.")
        form.destroy()

    Button(form, text="Save Medication", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_medication).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)
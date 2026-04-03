from tkinter import *
from tkinter import messagebox
from vault import add_entry, get_entry, update_entry

MULTILINE_FIELDS = {"notes", "content"}


# ---------------------------- SECURE NOTES ------------------------------- #

def open_note_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit Note" if is_edit else "Add Secure Note")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Title", "title"),
        ("Category", "category"),
        ("Content", "content"),
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        Label(form, text=f"{label}:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=i, column=0, sticky="ne", padx=(0, 10), pady=4)

        if key in MULTILINE_FIELDS:
            widget = Text(form, width=40, height=8, bg=ENTRY_BG, fg=ENTRY_FG,
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

    def save_note():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["title"]:
            messagebox.showerror("Error", "Title is required.")
            return

        entry_key = entry_id if is_edit else data['title']

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "note", entry_key, {**data})

        messagebox.showinfo("Saved", "Note saved.")
        form.destroy()

    Button(form, text="Save Note", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_note).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)


# ---------------------------- IDENTITY INFO ------------------------------- #

def open_identity_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit Identity" if is_edit else "Add Identity Info")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Label", "label"),
        ("Full Name", "full_name"),
        ("Date of Birth", "dob"),
        ("Social Security Number", "ssn"),
        ("Passport Number", "passport_number"),
        ("Passport Expiry", "passport_expiry"),
        ("Drivers License Number", "license_number"),
        ("License Expiry", "license_expiry"),
        ("License State", "license_state"),
        ("Address", "address"),
        ("Phone Number", "phone"),
        ("Email", "email"),
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

    def save_identity():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["label"]:
            messagebox.showerror("Error", "Label is required.")
            return

        entry_key = entry_id if is_edit else data['label']

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "identity", entry_key, {**data, "category": "Personal"})

        messagebox.showinfo("Saved", "Identity info saved.")
        form.destroy()

    Button(form, text="Save Identity", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_identity).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)


# ---------------------------- WIFI ------------------------------- #

def open_wifi_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit WiFi" if is_edit else "Add WiFi Password")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Network Name (SSID)", "ssid"),
        ("Password", "password"),
        ("Security Type", "security_type"),
        ("Router Brand", "router_brand"),
        ("Router IP", "router_ip"),
        ("Admin Username", "admin_username"),
        ("Admin Password", "admin_password"),
        ("Location / Label", "location"),
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

    def save_wifi():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["ssid"]:
            messagebox.showerror("Error", "Network name is required.")
            return

        entry_key = entry_id if is_edit else data['ssid']

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "wifi", entry_key, {**data, "category": "Personal"})

        messagebox.showinfo("Saved", "WiFi saved.")
        form.destroy()

    Button(form, text="Save WiFi", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_wifi).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)
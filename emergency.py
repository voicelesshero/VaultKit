from tkinter import *
from tkinter import messagebox
from vault import add_entry, get_entry, update_entry
from profile import get_profile_defaults

# Fields that need multiline text boxes
MULTILINE_FIELDS = {"allergies", "medications", "medical_conditions", "notes"}

def open_emergency_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD):

    form = Toplevel(window)
    form.title("Emergency Info")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    profile = get_profile_defaults(cipher)

    fields = [
        ("Blood Type", "blood_type"),
        ("Allergies", "allergies"),
        ("Current Medications", "medications"),
        ("Primary Doctor", "primary_doctor"),
        ("Doctor Phone", "doctor_phone"),
        ("Emergency Contact", "emergency_contact"),
        ("Emergency Contact Phone", "emergency_contact_phone"),
        ("Insurance Provider", "insurance_provider"),
        ("Policy Number", "policy_number"),
        ("Medical Conditions", "medical_conditions"),
        ("Hospital Preference", "hospital_preference"),
        ("Notes", "notes"),
    ]

    entries = {}
    existing = get_entry(cipher, "emergency")

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

    def save_emergency():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        # Pull identifying fields silently from profile — not asked again in this form.
        data["full_name"] = profile.get("full_name", "")
        data["cell_phone"] = profile.get("cell_phone", "")
        data["home_phone"] = profile.get("home_phone", "")
        if not data["full_name"]:
            present = [k for k, v in profile.items() if v]
            detail = (f"Fields present: {present}" if present
                      else "Profile is completely empty.")
            print(f"[emergency save] profile at save time: {profile}")
            messagebox.showerror(
                "Profile Incomplete",
                "Your full name is missing from your profile.\n\n"
                "Please open Profile and save your name first.\n\n"
                f"({detail})"
            )
            return

        if existing:
            update_entry(cipher, "emergency", data)
        else:
            add_entry(cipher, "emergency", "emergency", data)

        messagebox.showinfo("Saved", "Emergency info saved successfully.")
        form.destroy()

    Button(form, text="Save Emergency Info", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_emergency).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)
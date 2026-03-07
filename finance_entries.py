from tkinter import *
from tkinter import messagebox
from vault import add_entry, get_entry, update_entry

MULTILINE_FIELDS = {"notes"}


# ---------------------------- CREDIT CARD ------------------------------- #

def open_credit_card_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None

    form = Toplevel(window)
    form.title("Edit Credit Card" if is_edit else "Add Credit Card")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Card Label", "label"),
        ("Cardholder Name", "cardholder_name"),
        ("Card Number", "card_number"),
        ("Expiration Date", "expiry"),
        ("CVV", "cvv"),
        ("Billing Address", "billing_address"),
        ("Card Type", "card_type"),
        ("Bank / Issuer", "bank"),
        ("Customer Service Phone", "phone"),
        ("Online Banking URL", "url"),
        ("PIN", "pin"),
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

    def save_card():
        data = {}
        for key, widget in entries.items():
            if key in MULTILINE_FIELDS:
                data[key] = widget.get("1.0", END).strip()
            else:
                data[key] = widget.get()

        if not data["label"]:
            messagebox.showerror("Error", "Card label is required.")
            return

        entry_key = entry_id if is_edit else f"card_{data['label'].lower().replace(' ', '_')}"

        if is_edit:
            update_entry(cipher, entry_key, data)
        else:
            add_entry(cipher, "credit_card", entry_key, {**data, "category": "Finance"})

        messagebox.showinfo("Saved", "Credit card saved.")
        form.destroy()

    Button(form, text="Save Card", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_card).grid(
        row=len(fields), column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)
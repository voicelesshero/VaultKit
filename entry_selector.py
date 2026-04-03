from tkinter import *
from emergency import open_emergency_form
from health_entries import open_insurance_form, open_medication_form
from personal_entries import open_note_form, open_identity_form, open_wifi_form
from finance_entries import open_credit_card_form
from password_entry_form import open_password_form

ENTRY_TYPES = [
    ("🔑  Password",         "password"),
    ("🏥  Emergency Info",   "emergency"),
    ("🏨  Insurance Policy", "insurance"),
    ("💊  Medication",       "medication"),
    ("📝  Secure Note",      "note"),
    ("💳  Credit Card",      "credit_card"),
    ("🪪  Identity Info",    "identity"),
    ("📶  WiFi Password",    "wifi"),
]

def open_entry_selector(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                        BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD):

    selector = Toplevel(window)
    selector.title("Add New Entry")
    selector.config(padx=40, pady=40, bg=BG_COLOR)
    selector.resizable(False, False)

    Label(selector, text="What would you like to add?", bg=BG_COLOR, fg=LABEL_FG,
          font=FONT_BOLD).grid(row=0, column=0, pady=(0, 16))

    theme = (window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD)

    def select(entry_type):
        selector.destroy()
        if entry_type == "password":
            open_password_form(*theme)
        elif entry_type == "emergency":
            open_emergency_form(*theme)
        elif entry_type == "insurance":
            open_insurance_form(*theme)
        elif entry_type == "medication":
            open_medication_form(*theme)
        elif entry_type == "note":
            open_note_form(*theme)
        elif entry_type == "credit_card":
            open_credit_card_form(*theme)
        elif entry_type == "identity":
            open_identity_form(*theme)
        elif entry_type == "wifi":
            open_wifi_form(*theme)

    for i, (label, entry_type) in enumerate(ENTRY_TYPES):
        btn = Button(selector, text=label, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat",
                     font=FONT, cursor="hand2", anchor="w",
                     command=lambda t=entry_type: select(t))
        btn.grid(row=i + 1, column=0, sticky="ew", pady=3, ipady=6)
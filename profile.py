from tkinter import *
from tkinter import messagebox
from vault import get_current_user, get_user_profile, update_user_profile


def open_profile_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                      BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD,
                      first_run=False, on_complete=None):

    form = Toplevel(window)
    form.title("Profile Setup" if first_run else "Edit Profile")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    if first_run:
        Label(form, text="Let's set up your profile",
              bg=BG_COLOR, fg=ENTRY_FG, font=FONT_BOLD).grid(
            row=0, column=0, columnspan=4, pady=(0, 4))
        Label(form, text="This info will auto-fill your vault entries. You can update it anytime.",
              bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).grid(
            row=1, column=0, columnspan=4, pady=(0, 16))
        start_row = 2
    else:
        start_row = 0

    # pre-fill from existing profile
    existing = get_user_profile(cipher)
    profile_map = {}
    if existing:
        dob_stored = existing[3] or ""
        addr_stored = existing[6] or ""
        dob_parts = dob_stored.split("|") if dob_stored else []
        addr_parts = addr_stored.split("|") if addr_stored else []
        phone_stored = existing[4] or ""
        phone_parts = phone_stored.split("|") if phone_stored else []
        # Backwards compat: single old value becomes cell_phone
        profile_map = {
            "full_name": existing[2] or "",
            "dob_month": dob_parts[0] if len(dob_parts) > 0 else "",
            "dob_day": dob_parts[1] if len(dob_parts) > 1 else "",
            "dob_year": dob_parts[2] if len(dob_parts) > 2 else "",
            "cell_phone": phone_parts[0] if len(phone_parts) > 0 else "",
            "home_phone": phone_parts[1] if len(phone_parts) > 1 else "",
            "work_phone": phone_parts[2] if len(phone_parts) > 2 else "",
            "email": existing[5] or "",
            "street": addr_parts[0] if len(addr_parts) > 0 else "",
            "apt": addr_parts[1] if len(addr_parts) > 1 else "",
            "city": addr_parts[2] if len(addr_parts) > 2 else "",
            "state": addr_parts[3] if len(addr_parts) > 3 else "",
            "zip": addr_parts[4] if len(addr_parts) > 4 else "",
        }

    entries = {}
    r = start_row

    # Full Name
    Label(form, text="Full Name:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["full_name"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                                  insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["full_name"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=4)
    entries["full_name"].insert(0, profile_map.get("full_name", ""))
    r += 1

    # Date of Birth
    Label(form, text="Date of Birth:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    dob_frame = Frame(form, bg=BG_COLOR)
    dob_frame.grid(row=r, column=1, columnspan=3, sticky="w", pady=4)

    entries["dob_month"] = Entry(dob_frame, width=4, bg=ENTRY_BG, fg=ENTRY_FG,
                                  insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["dob_month"].pack(side="left", ipady=4)
    entries["dob_month"].insert(0, profile_map.get("dob_month", ""))
    Label(dob_frame, text="MM", bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).pack(side="left", padx=(2, 8))

    entries["dob_day"] = Entry(dob_frame, width=4, bg=ENTRY_BG, fg=ENTRY_FG,
                                insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["dob_day"].pack(side="left", ipady=4)
    entries["dob_day"].insert(0, profile_map.get("dob_day", ""))
    Label(dob_frame, text="DD", bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).pack(side="left", padx=(2, 8))

    entries["dob_year"] = Entry(dob_frame, width=6, bg=ENTRY_BG, fg=ENTRY_FG,
                                 insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["dob_year"].pack(side="left", ipady=4)
    entries["dob_year"].insert(0, profile_map.get("dob_year", ""))
    Label(dob_frame, text="YYYY", bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).pack(side="left", padx=(2, 0))
    r += 1

    # Cell Phone
    Label(form, text="Cell Phone:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["cell_phone"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                                   insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["cell_phone"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=4)
    entries["cell_phone"].insert(0, profile_map.get("cell_phone", ""))
    r += 1

    # Home Phone
    Label(form, text="Home Phone:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["home_phone"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                                   insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["home_phone"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=4)
    entries["home_phone"].insert(0, profile_map.get("home_phone", ""))
    r += 1

    # Work Phone
    Label(form, text="Work Phone:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["work_phone"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                                   insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["work_phone"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=4)
    entries["work_phone"].insert(0, profile_map.get("work_phone", ""))
    r += 1

    # Primary Email
    Label(form, text="Primary Email:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=(4, 0))
    entries["email"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                              insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["email"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=(4, 0))
    entries["email"].insert(0, profile_map.get("email", ""))
    r += 1
    Label(form, text="used for auto-fill and sync account setup",
          bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 8)).grid(
        row=r, column=1, columnspan=3, sticky="w", pady=(0, 6))
    r += 1

    # Street Address
    Label(form, text="Street:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["street"] = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                               insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["street"].grid(row=r, column=1, columnspan=3, sticky="ew", ipady=4, pady=4)
    entries["street"].insert(0, profile_map.get("street", ""))
    r += 1

    # Apt
    Label(form, text="Apt / Unit:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    entries["apt"] = Entry(form, width=10, bg=ENTRY_BG, fg=ENTRY_FG,
                            insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["apt"].grid(row=r, column=1, sticky="w", ipady=4, pady=4)
    entries["apt"].insert(0, profile_map.get("apt", ""))
    r += 1

    # City / State / Zip
    Label(form, text="City / State / Zip:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=r, column=0, sticky="e", padx=(0, 10), pady=4)
    addr_frame = Frame(form, bg=BG_COLOR)
    addr_frame.grid(row=r, column=1, columnspan=3, sticky="w", pady=4)

    entries["city"] = Entry(addr_frame, width=16, bg=ENTRY_BG, fg=ENTRY_FG,
                             insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["city"].pack(side="left", ipady=4, padx=(0, 4))
    entries["city"].insert(0, profile_map.get("city", ""))

    entries["state"] = Entry(addr_frame, width=4, bg=ENTRY_BG, fg=ENTRY_FG,
                              insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["state"].pack(side="left", ipady=4, padx=(0, 4))
    entries["state"].insert(0, profile_map.get("state", ""))

    entries["zip"] = Entry(addr_frame, width=7, bg=ENTRY_BG, fg=ENTRY_FG,
                            insertbackground=ENTRY_FG, relief="flat", font=FONT)
    entries["zip"].pack(side="left", ipady=4)
    entries["zip"].insert(0, profile_map.get("zip", ""))
    r += 1

    def save_profile():
        user = get_current_user(cipher)
        if not user:
            return

        dob = f"{entries['dob_month'].get()}|{entries['dob_day'].get()}|{entries['dob_year'].get()}"
        phone = (f"{entries['cell_phone'].get()}|{entries['home_phone'].get()}|"
                 f"{entries['work_phone'].get()}")
        address = (f"{entries['street'].get()}|{entries['apt'].get()}|"
                   f"{entries['city'].get()}|{entries['state'].get()}|{entries['zip'].get()}")

        update_user_profile(
            cipher,
            user[0],
            entries["full_name"].get(),
            dob,
            phone,
            entries["email"].get(),
            address,
        )
        if first_run:
            messagebox.showinfo("Profile Saved", "Profile saved. Welcome to VaultKit!")
        else:
            messagebox.showinfo("Profile Updated", "Profile updated successfully.")
        form.destroy()
        if on_complete:
            on_complete()

    def skip():
        form.destroy()
        if on_complete:
            on_complete()

    Button(form, text="Save Profile", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_profile).grid(
        row=r, column=0, columnspan=3 if not first_run else 2,
        sticky="ew", pady=(16, 0), ipady=6)

    if first_run:
        Button(form, text="Skip for Now", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
               font=FONT_BOLD, cursor="hand2", command=skip).grid(
            row=r, column=2, columnspan=2, sticky="ew", padx=(8, 0), pady=(16, 0), ipady=6)


def get_profile_defaults(cipher):
    """
    Returns a dict of profile values for auto-filling entry forms.
    """
    existing = get_user_profile(cipher)
    if not existing:
        return {}

    stored_addr = existing[6] or ""
    stored_dob = existing[3] or ""
    stored_phone = existing[4] or ""
    addr_parts = stored_addr.split("|") if stored_addr else []
    dob_parts = stored_dob.split("|") if stored_dob else []
    phone_parts = stored_phone.split("|") if stored_phone else []

    street = addr_parts[0] if len(addr_parts) > 0 else ""
    apt = addr_parts[1] if len(addr_parts) > 1 else ""
    city = addr_parts[2] if len(addr_parts) > 2 else ""
    state = addr_parts[3] if len(addr_parts) > 3 else ""
    zip_code = addr_parts[4] if len(addr_parts) > 4 else ""

    full_address = f"{street}{' ' + apt if apt else ''}, {city}, {state} {zip_code}".strip(", ")

    month = dob_parts[0] if len(dob_parts) > 0 else ""
    day = dob_parts[1] if len(dob_parts) > 1 else ""
    year = dob_parts[2] if len(dob_parts) > 2 else ""
    full_dob = f"{month}/{day}/{year}".strip("/")

    cell_phone = phone_parts[0] if len(phone_parts) > 0 else ""
    home_phone = phone_parts[1] if len(phone_parts) > 1 else ""
    work_phone = phone_parts[2] if len(phone_parts) > 2 else ""

    return {
        "full_name": existing[2] or "",
        "dob": full_dob,
        "cell_phone": cell_phone,
        "home_phone": home_phone,
        "work_phone": work_phone,
        "phone": cell_phone,   # alias — forms that use "phone" get cell by default
        "email": existing[5] or "",
        "address": full_address,
        "street": street,
        "apt": apt,
        "city": city,
        "state": state,
        "zip": zip_code,
    }
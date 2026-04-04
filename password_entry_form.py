from tkinter import *
from tkinter import messagebox
from random import choice, randint, shuffle
import pyperclip
import threading
from vault import add_entry, get_entry, update_entry
from hibp import check_and_notify
from profile import get_profile_defaults


def check_password_strength(password):
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!#$%&()*+" for c in password)
    score = sum([length >= 8, length >= 12, has_upper, has_lower, has_digit, has_symbol])
    if score <= 2:
        return "Weak", "#e74c3c"
    elif score <= 3:
        return "Fair", "#e67e22"
    elif score <= 4:
        return "Strong", "#f1c40f"
    else:
        return "Very Strong", "#27ae60"


def open_password_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                       BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, entry_id=None):

    is_edit = entry_id is not None
    existing = get_entry(cipher, entry_id) if is_edit else None
    profile = get_profile_defaults(cipher)

    form = Toplevel(window)
    form.title("Edit Password" if is_edit else "Add Password")
    form.config(padx=40, pady=40, bg=BG_COLOR)
    form.resizable(False, False)

    fields = [
        ("Website", "website"),
        ("Email / Username", "email"),
        ("Password", "password"),
        ("Category", "category"),
    ]

    entries = {}

    for i, (label, key) in enumerate(fields):
        Label(form, text=f"{label}:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=i, column=0, sticky="e", padx=(0, 10), pady=4)

        if key == "password":
            pw_frame = Frame(form, bg=BG_COLOR)
            pw_frame.grid(row=i, column=1, columnspan=2, sticky="ew", pady=4)

            pw_var = StringVar()
            pw_entry = Entry(pw_frame, textvariable=pw_var, width=28, bg=ENTRY_BG,
                             fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat",
                             font=FONT, show="*")
            pw_entry.pack(side="left", ipady=4)
            if existing and existing.get("password"):
                pw_entry.insert(0, existing["password"])
            entries["password"] = pw_entry

            def toggle_pw():
                pw_entry.config(show="" if pw_entry.cget("show") == "*" else "*")
                toggle_btn.config(text="🙈" if pw_entry.cget("show") == "" else "👁")

            toggle_btn = Button(pw_frame, text="👁", bg=ENTRY_BG, fg=LABEL_FG,
                                relief="flat", font=FONT, cursor="hand2", command=toggle_pw)
            toggle_btn.pack(side="left", padx=(4, 0))

        elif key == "category":
            cat_var = StringVar()
            cat_var.set(existing.get("category", "Personal") if existing else "Personal")
            cat_menu = OptionMenu(form, cat_var, "Personal", "Health", "Finance", "Family", "Work")
            cat_menu.config(bg=ENTRY_BG, fg=ENTRY_FG, activebackground=BTN_ACCENT,
                            activeforeground=BTN_FG, relief="flat", font=FONT,
                            highlightthickness=0)
            cat_menu["menu"].config(bg=ENTRY_BG, fg=ENTRY_FG, font=FONT)
            cat_menu.grid(row=i, column=1, columnspan=2, sticky="ew", pady=4)
            entries["category"] = cat_var

        else:
            widget = Entry(form, width=35, bg=ENTRY_BG, fg=ENTRY_FG,
                           insertbackground=ENTRY_FG, relief="flat", font=FONT)
            widget.grid(row=i, column=1, columnspan=2, sticky="ew", ipady=4, pady=4)
            if existing and existing.get(key):
                widget.insert(0, existing[key])
            elif key == "email" and profile.get("email"):
                widget.insert(0, profile["email"])
            entries[key] = widget

    strength_label = Label(form, text="", bg=BG_COLOR, font=FONT)
    strength_label.grid(row=len(fields), column=1, sticky="w", pady=(0, 4))

    def update_strength(*args):
        pwd = entries["password"].get()
        if pwd:
            label, color = check_password_strength(pwd)
            strength_label.config(text=f"Strength: {label}", fg=color)
        else:
            strength_label.config(text="")

    pw_var.trace_add("write", update_strength)
    update_strength()  # populate immediately if password is pre-filled (edit mode)

    btn_row = len(fields) + 1

    def generate_password():
        letters = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        numbers = list("0123456789")
        symbols = list("!#$%&()*+")
        pwd_list = ([choice(letters) for _ in range(randint(8, 10))] +
                    [choice(symbols) for _ in range(randint(2, 4))] +
                    [choice(numbers) for _ in range(randint(2, 4))])
        shuffle(pwd_list)
        password = "".join(pwd_list)
        entries["password"].delete(0, END)
        entries["password"].insert(0, password)
        pyperclip.copy(password)
        timer = threading.Timer(30, lambda: pyperclip.copy(""))
        timer.daemon = True
        timer.start()
        update_strength()

    def check_breach():
        check_and_notify(entries["password"].get())

    Button(form, text="Generate", bg=BTN_ACCENT, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=generate_password).grid(
        row=btn_row, column=1, sticky="ew", padx=(0, 4), ipady=5)

    Button(form, text="Check Breach", bg="#8e44ad", fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=check_breach).grid(
        row=btn_row, column=2, sticky="ew", ipady=5)

    def save_password():
        website = entries["website"].get()
        email = entries["email"].get()
        password = entries["password"].get()
        category = entries["category"].get()

        if not website or not password:
            messagebox.showerror("Error", "Website and password are required.")
            return

        if is_edit:
            update_entry(cipher, entry_id, {"email": email, "password": password,
                                             "category": category})
        else:
            add_entry(cipher, "password", website,
                      {"email": email, "password": password, "category": category})

        messagebox.showinfo("Saved", f"Password for {website} saved.")
        form.destroy()

    Button(form, text="Save Password", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_password).grid(
        row=btn_row + 1, column=0, columnspan=3, sticky="ew", pady=(12, 0), ipady=6)
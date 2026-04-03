from random import choice, randint, shuffle
from tkinter import *
from tkinter import messagebox, simpledialog
import pyperclip
import json
import os
import sys
import threading
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from vault import (add_entry, get_entry, update_entry, delete_entry,
                   get_all_entries, get_entries_by_type, load_vault,
                   setup_vault, search_vault, get_current_user, get_user_profile)
from categories import open_category_view
from session import SessionManager
from entry_selector import open_entry_selector
from emergency import open_emergency_form
from profile import open_profile_form, get_profile_defaults

ph = PasswordHasher()

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ---------------------------- THEME ------------------------------- #
BG_COLOR = "#2b2b2b"
ENTRY_BG = "#3c3c3c"
ENTRY_FG = "#f0f0f0"
LABEL_FG = "#cccccc"
BTN_BG = "#4a90d9"
BTN_FG = "#ffffff"
BTN_ACCENT = "#3a7abf"
FONT = ("Helvetica", 11)
FONT_BOLD = ("Helvetica", 11, "bold")

# ---------------------------- ENCRYPTION ------------------------------- #
cipher = None

def make_key(password):
    import hashlib
    import base64
    raw = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(raw)

# ---------------------------- MASTER PASSWORD ------------------------------- #
def hash_password(password):
    return ph.hash(password)

def verify_password(stored_hash, entered_password):
    try:
        ph.verify(stored_hash, entered_password)
        return True
    except VerifyMismatchError:
        return False

def check_master_password():
    global cipher
    try:
        with open("master.json", "r") as f:
            stored = json.load(f)

        entered = simpledialog.askstring("Login", "Enter master password:", show="*")
        if entered is None:
            window.destroy()
            return False

        if not verify_password(stored["master"], entered):
            messagebox.showerror("Access Denied", "Incorrect master password.")
            window.destroy()
            return False

        cipher = Fernet(make_key(entered))
        load_vault(cipher)
        return True

    except FileNotFoundError:
        messagebox.showinfo("Welcome", "No master password found. Let's create one.")
        new_pass = simpledialog.askstring("Setup", "Create a master password:", show="*")
        if not new_pass:
            window.destroy()
            return False

        confirm = simpledialog.askstring("Setup", "Confirm master password:", show="*")
        if new_pass != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            window.destroy()
            return False

        with open("master.json", "w") as f:
            json.dump({"master": hash_password(new_pass)}, f)

        cipher = Fernet(make_key(new_pass))
        setup_vault(cipher, hash_password(new_pass))
        messagebox.showinfo("Success", "Master password set. Welcome!")
        return True

# ---------------------------- FUNCTIONS ------------------------------- #
def verify_master(entered):
    try:
        with open("master.json", "r") as f:
            stored = json.load(f)
        return verify_password(stored["master"], entered)
    except FileNotFoundError:
        return False

def find_password(website=None):
    if not website:
        messagebox.showinfo("Search", "Please enter a website to search.")
        return

    entry = get_entry(cipher, website)

    if not entry:
        messagebox.showinfo(title="Not Found", message=f"No data found for '{website}'.")
        return

    email = entry.get("email", "")
    password = entry.get("password", "")

    dialog = Toplevel(window)
    dialog.title(website)
    dialog.config(padx=30, pady=30, bg=BG_COLOR)
    dialog.resizable(False, False)

    Label(dialog, text=f"Website:  {website}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
    Label(dialog, text=f"Email:       {email}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=1, column=0, columnspan=3, sticky="w", pady=(0, 4))
    Label(dialog, text=f"Password: {password}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=2, column=0, columnspan=3, sticky="w", pady=(0, 16))

    def copy_and_clear():
        pyperclip.copy(password)
        messagebox.showinfo("Copied", "Password copied to clipboard. Will clear in 30 seconds.")
        timer = threading.Timer(30, lambda: pyperclip.copy(""))
        timer.daemon = True
        timer.start()

    Button(dialog, text="Copy Password", bg="#27ae60", fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=copy_and_clear).grid(
        row=3, column=0, columnspan=3, sticky="ew", ipady=4, pady=(0, 8))

    Button(dialog, text="Edit", bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2",
           command=lambda: edit_entry_dialog(dialog, website, email, password)).grid(
        row=4, column=0, padx=(0, 8), ipady=4, sticky="ew")

    Button(dialog, text="Delete", bg="#c0392b", fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2",
           command=lambda: delete_entry_dialog(dialog, website)).grid(
        row=4, column=1, padx=(0, 8), ipady=4, sticky="ew")

    Button(dialog, text="Cancel", bg=ENTRY_BG, fg=LABEL_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=dialog.destroy).grid(row=4, column=2, ipady=4, sticky="ew")


def edit_entry_dialog(parent, website, current_email, current_password):
    parent.destroy()

    edit_win = Toplevel(window)
    edit_win.title(f"Edit - {website}")
    edit_win.config(padx=30, pady=30, bg=BG_COLOR)
    edit_win.resizable(False, False)

    Label(edit_win, text="Email:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=0, column=0, sticky="e", padx=(0, 10), pady=6)
    Label(edit_win, text="Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=1, column=0, sticky="e", padx=(0, 10), pady=6)

    new_email = Entry(edit_win, width=30, bg=ENTRY_BG, fg=ENTRY_FG,
                      insertbackground=ENTRY_FG, relief="flat", font=FONT)
    new_email.insert(0, current_email)
    new_email.grid(row=0, column=1, ipady=5)

    new_password = Entry(edit_win, width=30, bg=ENTRY_BG, fg=ENTRY_FG,
                         insertbackground=ENTRY_FG, relief="flat", font=FONT)
    new_password.insert(0, current_password)
    new_password.grid(row=1, column=1, ipady=5)

    def save_edit():
        update_entry(cipher, website, {"email": new_email.get(), "password": new_password.get()})
        messagebox.showinfo("Updated", f"{website} has been updated.")
        edit_win.destroy()

    Button(edit_win, text="Save Changes", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=save_edit).grid(
        row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)


def delete_entry_dialog(parent, website):
    parent.destroy()
    confirm = messagebox.askyesno("Delete",
                                   f"Are you sure you want to delete {website}? This cannot be undone.")
    if not confirm:
        return
    delete_entry(cipher, website)
    messagebox.showinfo("Deleted", f"{website} has been removed.")


# ---------------------------- UI SETUP ------------------------------- #
window = Tk()
window.title("VaultKit")
window.config(padx=40, pady=40, bg=BG_COLOR)
window.withdraw()

if not check_master_password():
    exit()

window.deiconify()
session = SessionManager(window, verify_master)

def on_profile_complete():
    refresh_greeting()

profile = get_user_profile(cipher)
if profile and not profile[2]:
    open_profile_form(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                      BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD,
                      first_run=True, on_complete=on_profile_complete)

# ---------------------------- HEADER ------------------------------- #
header_frame = Frame(window, bg=BG_COLOR)
header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 20))

canvas = Canvas(header_frame, width=60, height=60, bg=BG_COLOR, highlightthickness=0)
logo_img = PhotoImage(file=resource_path("logo3.png"))
logo_img_resized = logo_img.subsample(5, 5)
canvas.create_image(30, 30, image=logo_img_resized)
canvas.pack(side="left")

title_frame = Frame(header_frame, bg=BG_COLOR)
title_frame.pack(side="left", expand=True)

Label(title_frame, text="VaultKit", bg=BG_COLOR, fg=ENTRY_FG,
      font=("Helvetica", 14, "bold")).pack()

def get_first_name():
    p = get_user_profile(cipher)
    if p and p[2]:
        return p[2].split()[0]
    return None

first_name = get_first_name()
greeting_text = f"Hi, {first_name}" if first_name else "Welcome"

greeting_label = Label(title_frame, text=greeting_text, bg=BG_COLOR,
                       fg=LABEL_FG, font=("Helvetica", 10))
greeting_label.pack()

def refresh_greeting():
    name = get_first_name()
    greeting_label.config(text=f"Hi, {name}" if name else "Welcome")

settings_btn = Button(header_frame, text="⚙", bg=BG_COLOR, fg=LABEL_FG, relief="flat",
                      font=("Helvetica", 14), cursor="hand2",
                      command=lambda: [open_profile_form(window, cipher, BG_COLOR, ENTRY_BG,
                                                         ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG,
                                                         BTN_ACCENT, FONT, FONT_BOLD),
                                       window.after(500, refresh_greeting)])
settings_btn.pack(side="right")

# ---------------------------- SEARCH BAR ------------------------------- #
search_frame = Frame(window, bg=ENTRY_BG, highlightthickness=1,
                     highlightbackground=BTN_ACCENT)
search_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 14), ipady=4)

Label(search_frame, text="🔍", bg=ENTRY_BG, fg=LABEL_FG,
      font=("Helvetica", 11)).pack(side="left", padx=(10, 4))

search_var = StringVar()
search_entry = Entry(search_frame, textvariable=search_var, bg=ENTRY_BG, fg=ENTRY_FG,
                     insertbackground=ENTRY_FG, relief="flat", font=FONT, width=28)
search_entry.pack(side="left", ipady=4)

Button(search_frame, text="Search", bg=BTN_BG, fg=BTN_FG, relief="flat",
       font=FONT_BOLD, cursor="hand2",
       command=lambda: find_password(search_var.get())).pack(
    side="right", padx=4, pady=2, ipady=3)

# ---------------------------- PRIMARY ACTION ------------------------------- #
Button(window, text="Open My Vault", bg=BTN_BG, fg=BTN_FG, relief="flat",
       font=FONT_BOLD, activebackground=BTN_ACCENT, activeforeground=BTN_FG,
       cursor="hand2",
       command=lambda: open_category_view(window, cipher, BG_COLOR, ENTRY_BG,
                                          ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG,
                                          BTN_ACCENT, FONT, FONT_BOLD)).grid(
    row=2, column=0, columnspan=3, sticky="ew", ipady=10, pady=(0, 8))

# ---------------------------- SECONDARY ACTIONS ------------------------------- #
Button(window, text="Add Entry", bg="#27ae60", fg=BTN_FG, relief="flat",
       font=FONT_BOLD, activebackground="#219a52", activeforeground=BTN_FG,
       cursor="hand2",
       command=lambda: open_entry_selector(window, cipher, BG_COLOR, ENTRY_BG,
                                           ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG,
                                           BTN_ACCENT, FONT, FONT_BOLD)).grid(
    row=3, column=0, columnspan=2, sticky="ew", ipady=8, padx=(0, 4))

Button(window, text="Emergency", bg="#c0392b", fg=BTN_FG, relief="flat",
       font=FONT_BOLD, activebackground="#a93226", activeforeground=BTN_FG,
       cursor="hand2",
       command=lambda: open_emergency_form(window, cipher, BG_COLOR, ENTRY_BG,
                                           ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG,
                                           BTN_ACCENT, FONT, FONT_BOLD)).grid(
    row=3, column=2, sticky="ew", ipady=8, padx=(4, 0))

window.mainloop()
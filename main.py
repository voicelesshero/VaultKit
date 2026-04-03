from random import choice, randint, shuffle
from tkinter import *
from tkinter import messagebox, simpledialog
import pyperclip
import json
import hashlib
import base64
import os
import sys
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from vault import add_entry, get_entry, update_entry, delete_entry, get_all_entries, get_entries_by_type, load_vault, setup_vault, search_vault
import threading
from categories import open_category_view
from session import SessionManager
from hibp import check_and_notify
from entry_selector import open_entry_selector

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
cipher = None  # holds the Fernet cipher once master password is verified

def make_key(password):
    import hashlib
    import base64
    raw = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(raw)

def encrypt_data(data: dict) -> bytes:
    json_bytes = json.dumps(data, indent=4).encode()
    return cipher.encrypt(json_bytes)

def decrypt_data(encrypted_bytes: bytes) -> dict:
    decrypted = cipher.decrypt(encrypted_bytes)
    return json.loads(decrypted.decode())

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

# ---------------------------- PASSWORD GENERATOR ------------------------------- #
def generate_password():
    letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
               'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    numbers = ['0','1','2','3','4','5','6','7','8','9']
    symbols = ['!','#','$','%','&','(',')','+']

    password_letters = [choice(letters) for _ in range(randint(8, 10))]
    password_symbols = [choice(symbols) for _ in range(randint(2, 4))]
    password_numbers = [choice(numbers) for _ in range(randint(2, 4))]

    password_list = password_letters + password_symbols + password_numbers
    shuffle(password_list)

    password = "".join(password_list)
    password_entry.delete(0, END)
    password_entry.insert(0, password)
    try:
        update_strength()
    except NameError:
        pass
    pyperclip.copy(password)

    timer = threading.Timer(30, lambda: pyperclip.copy(""))
    timer.daemon = True
    timer.start()
# ---------------------------- SAVE PASSWORD ------------------------------- #
def save():
    website = website_entry.get()
    email = email_entry.get()
    password = password_entry.get()
    category = category_var.get()

    if len(website) == 0 or len(password) == 0:
        messagebox.showinfo(title="ERROR", message="Please make sure you haven't left any fields empty.")
        return

    add_entry(cipher, "password", website, {"email": email, "password": password, "category": category})

    website_entry.delete(0, END)
    email_entry.delete(0, END)
    password_entry.delete(0, END)
    category_var.set("Personal")

# ---------------------------- SEARCH / EDIT / DELETE ------------------------------- #
def find_password():
    website = website_entry.get()
    entry = get_entry(cipher, website)

    if not entry:
        messagebox.showinfo(title="ERROR", message="No data for this website.")
        return

    email = entry.get("email", "")
    password = entry.get("password", "")

    dialog = Toplevel(window)
    dialog.title(website)
    dialog.config(padx=30, pady=30, bg=BG_COLOR)
    dialog.resizable(False, False)

    Label(dialog, text=f"Website:  {website}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
    Label(dialog, text=f"Email:       {email}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 4))
    Label(dialog, text=f"Password: {password}", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 16))

    def copy_and_clear():
        pyperclip.copy(password)
        messagebox.showinfo("Copied", "Password copied to clipboard. Will clear in 30 seconds.")
        timer = threading.Timer(30, lambda: pyperclip.copy(""))
        timer.daemon = True
        timer.start()

    Button(dialog, text="Copy Password", bg="#27ae60", fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=copy_and_clear).grid(row=3, column=0, columnspan=3, sticky="ew", ipady=4,
                                                        pady=(0, 8))

    Button(dialog, text="Edit", bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=lambda: edit_entry_dialog(dialog, website, email, password)).grid(row=4, column=0, padx=(0, 8), ipady=4, sticky="ew")

    Button(dialog, text="Delete", bg="#c0392b", fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=lambda: delete_entry_dialog(dialog, website)).grid(row=4, column=1, padx=(0, 8), ipady=4, sticky="ew")

    Button(dialog, text="Cancel", bg=ENTRY_BG, fg=LABEL_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=dialog.destroy).grid(row=4, column=2, ipady=4, sticky="ew")


def edit_entry_dialog(parent, website, current_email, current_password):
    parent.destroy()

    edit_win = Toplevel(window)
    edit_win.title(f"Edit - {website}")
    edit_win.config(padx=30, pady=30, bg=BG_COLOR)
    edit_win.resizable(False, False)

    Label(edit_win, text="Email:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=0, column=0, sticky="e", padx=(0, 10), pady=6)
    Label(edit_win, text="Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)

    new_email = Entry(edit_win, width=30, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT)
    new_email.insert(0, current_email)
    new_email.grid(row=0, column=1, ipady=5)

    new_password = Entry(edit_win, width=30, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT)
    new_password.insert(0, current_password)
    new_password.grid(row=1, column=1, ipady=5)

    def save_edit():
        update_entry(cipher, website, {"email": new_email.get(), "password": new_password.get()})
        messagebox.showinfo("Updated", f"{website} has been updated.")
        edit_win.destroy()

    Button(edit_win, text="Save Changes", bg=BTN_BG, fg=BTN_FG, relief="flat", font=FONT_BOLD,
           cursor="hand2", command=save_edit).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)

def delete_entry_dialog(parent, website):
    parent.destroy()
    confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete {website}? This cannot be undone.")
    if not confirm:
        return
    delete_entry(cipher, website)
    messagebox.showinfo("Deleted", f"{website} has been removed.")

# ---------------------------- UI SETUP ------------------------------- #
window = Tk()
window.title("Vault Kit")
window.config(padx=40, pady=40, bg=BG_COLOR)
window.withdraw()

if not check_master_password():
    exit()


window.deiconify()
session = SessionManager(window, verify_master)


canvas = Canvas(width=300, height=300, bg=BG_COLOR, highlightthickness=0)
logo_img = PhotoImage(file=resource_path("logo3.png"))
canvas.create_image(150, 150, image=logo_img)
canvas.grid(row=0, column=0, columnspan=3, pady=(0, 20))

# Labels
Label(text="Website:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=1, column=0, sticky="e", padx=(0, 10), pady=6)
Label(text="Email/Username:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=2, column=0, sticky="e", padx=(0, 10), pady=6)
Label(text="Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=3, column=0, sticky="e", padx=(0, 10), pady=6)
Label(text="Category:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(row=5, column=0, sticky="e", padx=(0, 10), pady=6)

# Entries
website_entry = Entry(width=22, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT)
website_entry.grid(row=1, column=1, sticky="ew", ipady=5)
website_entry.focus()

email_entry = Entry(width=36, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT)
email_entry.grid(row=2, column=1, columnspan=2, sticky="ew", ipady=5)

password_entry = Entry(width=22, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
password_entry.grid(row=3, column=1, sticky="ew", ipady=5)

# Strength label sits on row 4, spanning under the password field
strength_label = Label(text="", bg=BG_COLOR, font=FONT)
strength_label.grid(row=4, column=1, sticky="w", pady=(0, 4))

# Category dropdown on row 5
category_var = StringVar(window)
category_var.set("Personal")

category_menu = OptionMenu(window, category_var, "Personal", "Health", "Finance", "Family", "Work")
category_menu.config(bg=ENTRY_BG, fg=ENTRY_FG, activebackground=BTN_ACCENT, activeforeground=BTN_FG,
                     relief="flat", font=FONT, highlightthickness=0)
category_menu["menu"].config(bg=ENTRY_BG, fg=ENTRY_FG, font=FONT)
category_menu.grid(row=5, column=1, sticky="ew", pady=6)

# Password strength trace
def update_strength(*args):
    pwd = password_entry.get()
    if pwd:
        label, color = check_password_strength(pwd)
        strength_label.config(text=f"Strength: {label}", fg=color)
    else:
        strength_label.config(text="")

password_var = StringVar()
password_entry.config(textvariable=password_var)
password_var.trace_add("write", update_strength)

# Toggle button
def toggle_password():
    if password_entry.cget("show") == "*":
        password_entry.config(show="")
        toggle_btn.config(text="🙈")
    else:
        password_entry.config(show="*")
        toggle_btn.config(text="👁")

toggle_btn = Button(text="👁", bg=ENTRY_BG, fg=LABEL_FG, relief="flat", font=FONT,
                    cursor="hand2", command=toggle_password)
toggle_btn.grid(row=3, column=1, sticky="e", padx=(0, 4))

# Buttons
search_btn = Button(text="Search", bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD,
                    activebackground=BTN_BG, activeforeground=BTN_FG, cursor="hand2", command=find_password)
search_btn.grid(row=1, column=2, sticky="ew", padx=(8, 0), ipady=5)

gen_btn = Button(text="Generate", bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD,
                 activebackground=BTN_BG, activeforeground=BTN_FG, cursor="hand2", command=generate_password)
gen_btn.grid(row=3, column=2, sticky="ew", padx=(8, 0), ipady=5)

hibp_btn = Button(text="Check Breach", bg="#8e44ad", fg=BTN_FG, relief="flat", font=FONT_BOLD,
                  activebackground="#7d3c98", activeforeground=BTN_FG, cursor="hand2",
                  command=lambda: check_and_notify(password_entry.get()))
hibp_btn.grid(row=4, column=2, sticky="ew", padx=(8, 0), ipady=5)

add_btn = Button(text="Save Password", bg=BTN_BG, fg=BTN_FG, relief="flat", font=FONT_BOLD,
                 activebackground=BTN_ACCENT, activeforeground=BTN_FG, cursor="hand2", command=save)
add_btn.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)

add_entry_btn = Button(text="Add New Entry", bg="#27ae60", fg=BTN_FG, relief="flat", font=FONT_BOLD,
                       activebackground="#219a52", activeforeground=BTN_FG, cursor="hand2",
                       command=lambda: open_entry_selector(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD,
                       on_password_selected=lambda: website_entry.focus()))
add_entry_btn.grid(row=7, column=1, columnspan=2, sticky="ew", pady=(8, 0), ipady=6)

vault_btn = Button(text="View Vault", bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD,
                   activebackground=BTN_BG, activeforeground=BTN_FG, cursor="hand2",
                   command=lambda: open_category_view(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD))
vault_btn.grid(row=8, column=1, columnspan=2, sticky="ew", pady=(8, 0), ipady=6)


window.mainloop()
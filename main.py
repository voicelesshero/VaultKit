from random import choice, randint, shuffle
from tkinter import *
from tkinter import messagebox, simpledialog
import pyperclip
import json
import os
import sys
import threading
import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from database import make_key
import api_client
from vault import (add_entry, get_entry, update_entry, delete_entry,
                   get_all_entries, get_entries_by_type, load_vault,
                   load_vault_after_download, setup_vault, search_vault,
                   get_current_user, get_user_profile)
from categories import open_category_view
from session import SessionManager
from entry_selector import open_entry_selector
from emergency import open_emergency_form
from profile import open_profile_form, get_profile_defaults
from settings import open_settings

ph = PasswordHasher()

# Holds a reference to build_sync_ui() while the settings window is open.
# startup_sync_check calls this (on the main thread) after a background upload.
sync_refresh_callback = None

def _set_sync_refresh(fn):
    global sync_refresh_callback
    sync_refresh_callback = fn

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
    """Entry point for first-run and login routing.

    Routes based on which local files exist:
      master.json present          → normal login
      master.json missing,
        sync_config.json present   → restore from sync (token + kdf_salt already saved)
      nothing exists               → welcome dialog (create / sign-in / offline)
    """
    has_master = os.path.exists("master.json")
    has_sync   = os.path.exists("sync_config.json")

    if has_master:
        return _do_login()
    elif has_sync:
        return _do_restore_from_sync()
    else:
        return _do_welcome()


# ------------------------------------------------------------------ #
# Login — master.json exists                                          #
# ------------------------------------------------------------------ #
def _do_login():
    global cipher
    with open("master.json", "r") as f:
        stored = json.load(f)

    entered = simpledialog.askstring("VaultKit", "Enter master password:", show="*")
    if entered is None:
        window.destroy()
        return False

    if not verify_password(stored["master"], entered):
        messagebox.showerror("Access Denied", "Incorrect master password.")
        window.destroy()
        return False

    salt = bytes.fromhex(stored["kdf_salt"])
    cipher = make_key(entered, salt)

    # If the vault file is missing but the user has a sync account, download now.
    if not os.path.exists("vaultkit.bin") and api_client.is_logged_in():
        status, code = api_client.get_vault_status()
        if code == 200 and status and status.get("has_vault"):
            success, err = api_client.download_vault()
            if not success:
                messagebox.showwarning(
                    "Sync",
                    f"Could not download vault from server: {err}\n\n"
                    "Opening with empty vault. You can sync manually from Settings."
                )

    load_vault(cipher)
    return True


# ------------------------------------------------------------------ #
# Restore — sync_config.json exists but master.json is missing        #
# ------------------------------------------------------------------ #
def _do_restore_from_sync():
    global cipher
    sync_cfg = api_client.load_sync_config()
    server_kdf_salt = sync_cfg.get("kdf_salt")

    # kdf_salt may not be cached locally yet — fetch live if needed.
    if api_client.is_logged_in() and not server_kdf_salt:
        status, code = api_client.get_vault_status()
        if code == 200 and status and status.get("kdf_salt"):
            server_kdf_salt = status["kdf_salt"]
            sync_cfg["kdf_salt"] = server_kdf_salt
            api_client.save_sync_config(sync_cfg)

    if not api_client.is_logged_in() or not server_kdf_salt:
        # sync_config exists but token is expired / missing kdf_salt.
        # Fall through to welcome so the user can sign in again.
        return _do_welcome()

    messagebox.showinfo(
        "Restore Vault",
        "No local vault found.\nEnter your master password to restore from sync."
    )
    entered = simpledialog.askstring("Restore", "Enter master password:", show="*")
    if not entered:
        window.destroy()
        return False

    kdf_salt = bytes.fromhex(server_kdf_salt)
    cipher = make_key(entered, kdf_salt)

    status, code = api_client.get_vault_status()
    if code == 200 and status and status.get("has_vault"):
        success, err = api_client.download_vault()
        if not success:
            messagebox.showerror("Restore Failed", err or "Could not download vault.")
            window.destroy()
            return False
    else:
        messagebox.showerror("Restore Failed", "No vault found on server.")
        window.destroy()
        return False

    with open("master.json", "w") as f:
        json.dump({"master": hash_password(entered), "kdf_salt": server_kdf_salt}, f)

    load_vault(cipher)
    messagebox.showinfo("Restored", "Vault restored successfully.")
    return True


# ------------------------------------------------------------------ #
# Sign-in flow — authenticate with sync, then decrypt vault           #
# ------------------------------------------------------------------ #
def _do_sign_in_to_account():
    """Prompt for sync credentials, fetch kdf_salt, then prompt for
    master password and download vault. Returns True on success."""
    dialog = Toplevel(window)
    dialog.title("Sign In to Sync Account")
    dialog.config(padx=40, pady=30, bg=BG_COLOR)
    dialog.resizable(False, False)
    dialog.grab_set()

    Label(dialog, text="Sync Email:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=0, column=0, sticky="e", padx=(0, 10), pady=6)
    email_entry = Entry(dialog, width=30, bg=ENTRY_BG, fg=ENTRY_FG,
                        insertbackground=ENTRY_FG, relief="flat", font=FONT)
    email_entry.grid(row=0, column=1, ipady=5, pady=6)

    Label(dialog, text="Sync Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
        row=1, column=0, sticky="e", padx=(0, 10), pady=6)
    sync_pw_entry = Entry(dialog, width=30, bg=ENTRY_BG, fg=ENTRY_FG,
                          insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
    sync_pw_entry.grid(row=1, column=1, ipady=5, pady=6)

    status_label = Label(dialog, text="", bg=BG_COLOR, fg="#e74c3c", font=FONT)
    status_label.grid(row=2, column=0, columnspan=2, pady=(4, 0))

    result = {"success": False}

    def attempt_sign_in():
        email    = email_entry.get().strip()
        sync_pw  = sync_pw_entry.get()

        if not email or not sync_pw:
            status_label.config(text="Email and password are required.")
            return

        status_label.config(text="Signing in...", fg=LABEL_FG)
        dialog.update_idletasks()

        data, code = api_client.login(email, sync_pw)
        if code != 200:
            status_label.config(
                text=data.get("error", "Sign in failed."), fg="#e74c3c")
            return

        # Fetch kdf_salt from server so we can derive the vault key.
        vault_status, vcode = api_client.get_vault_status()
        if vcode != 200 or not vault_status:
            status_label.config(text="Could not reach server. Try again.", fg="#e74c3c")
            return

        server_kdf_salt = vault_status.get("kdf_salt")
        if not server_kdf_salt:
            status_label.config(
                text="No vault found for this account.", fg="#e74c3c")
            return

        # Persist kdf_salt locally so future restores work without sign-in.
        cfg = api_client.load_sync_config()
        cfg["kdf_salt"] = server_kdf_salt
        api_client.save_sync_config(cfg)

        dialog.destroy()

        # Now prompt for the master password to decrypt the downloaded vault.
        entered = simpledialog.askstring(
            "Master Password",
            "Sync account verified.\nEnter your master password to decrypt your vault:",
            show="*"
        )
        if not entered:
            window.destroy()
            return

        global cipher
        kdf_salt = bytes.fromhex(server_kdf_salt)
        cipher = make_key(entered, kdf_salt)

        if vault_status.get("has_vault"):
            success, err = api_client.download_vault()
            if not success:
                messagebox.showerror("Restore Failed", err or "Could not download vault.")
                window.destroy()
                return
        else:
            messagebox.showerror("No Vault", "No vault found on server for this account.")
            window.destroy()
            return

        with open("master.json", "w") as f:
            json.dump({"master": hash_password(entered), "kdf_salt": server_kdf_salt}, f)

        load_vault(cipher)
        messagebox.showinfo("Welcome Back", "Vault restored successfully.")
        result["success"] = True

    Button(dialog, text="Sign In", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=attempt_sign_in).grid(
        row=3, column=0, columnspan=2, sticky="ew", pady=(14, 4), ipady=6)

    Button(dialog, text="Cancel", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
           font=FONT, cursor="hand2", command=dialog.destroy).grid(
        row=4, column=0, columnspan=2, sticky="ew", ipady=4)

    dialog.wait_window()
    return result["success"]


# ------------------------------------------------------------------ #
# Welcome — no local files at all                                     #
# ------------------------------------------------------------------ #
def _do_welcome():
    """Show a three-option welcome dialog for first-run scenarios."""
    result = {"choice": None}

    dialog = Toplevel(window)
    dialog.title("Welcome to VaultKit")
    dialog.config(padx=50, pady=40, bg=BG_COLOR)
    dialog.resizable(False, False)
    dialog.grab_set()

    Label(dialog, text="Welcome to VaultKit", bg=BG_COLOR, fg=ENTRY_FG,
          font=FONT_BOLD).pack(pady=(0, 6))
    Label(dialog, text="Your secure personal vault.", bg=BG_COLOR, fg=LABEL_FG,
          font=FONT).pack(pady=(0, 24))

    def choose(option):
        result["choice"] = option
        dialog.destroy()

    Button(dialog, text="Create New Vault",
           bg=BTN_BG, fg=BTN_FG, relief="flat", font=FONT_BOLD, cursor="hand2",
           command=lambda: choose("create")).pack(fill="x", pady=(0, 8), ipady=8)

    Button(dialog, text="Sign In to Existing Account",
           bg=BTN_ACCENT, fg=BTN_FG, relief="flat", font=FONT_BOLD, cursor="hand2",
           command=lambda: choose("signin")).pack(fill="x", pady=(0, 8), ipady=8)

    Button(dialog, text="Use Without Sync",
           bg=ENTRY_BG, fg=LABEL_FG, relief="flat", font=FONT, cursor="hand2",
           command=lambda: choose("offline")).pack(fill="x", ipady=6)

    dialog.wait_window()

    if result["choice"] == "signin":
        return _do_sign_in_to_account()

    if result["choice"] in ("create", "offline"):
        return _do_create_new_vault()

    # User closed the dialog.
    window.destroy()
    return False


# ------------------------------------------------------------------ #
# Create new vault — first-time setup                                 #
# ------------------------------------------------------------------ #
def _do_create_new_vault():
    global cipher

    new_pass = simpledialog.askstring("Setup", "Create a master password:", show="*")
    if not new_pass:
        window.destroy()
        return False

    confirm = simpledialog.askstring("Setup", "Confirm master password:", show="*")
    if new_pass != confirm:
        messagebox.showerror("Error", "Passwords do not match.")
        window.destroy()
        return False

    kdf_salt = os.urandom(16)
    with open("master.json", "w") as f:
        json.dump({"master": hash_password(new_pass), "kdf_salt": kdf_salt.hex()}, f)

    cipher = make_key(new_pass, kdf_salt)
    setup_vault(cipher, hash_password(new_pass))
    messagebox.showinfo("Success", "Master password set. Welcome to VaultKit!")
    return True

# ---------------------------- FUNCTIONS ------------------------------- #
def update_cipher(new_key):
    global cipher
    cipher = new_key
    # After a master password change the vault is rekeyed locally.
    # Force-upload to overwrite the server copy so no device can download
    # a blob encrypted with the old key. Runs in background — non-blocking.
    threading.Thread(target=api_client.force_upload_after_rekey, daemon=True).start()

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

# Register the sync re-authentication prompt now that the window exists.
# Called by api_client from a background thread when a 401 is received.
def _reauth_prompt(email):
    """Show a 'session expired' dialog on the main thread, block the calling
    background thread until the user responds, return password or None."""
    result = {"password": None}
    event = threading.Event()

    def show():
        dialog = Toplevel(window)
        dialog.title("Sync Session Expired")
        dialog.config(padx=30, pady=24, bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.grab_set()

        Label(dialog, text="Your sync session has expired.",
              bg=BG_COLOR, fg=ENTRY_FG, font=FONT_BOLD).pack(pady=(0, 4))
        Label(dialog, text=f"Re-enter your sync password for:",
              bg=BG_COLOR, fg=LABEL_FG, font=FONT).pack()
        Label(dialog, text=email, bg=BG_COLOR, fg=BTN_ACCENT,
              font=FONT_BOLD).pack(pady=(0, 12))

        pw_entry = Entry(dialog, width=28, bg=ENTRY_BG, fg=ENTRY_FG,
                         insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
        pw_entry.pack(ipady=5, pady=(0, 4))
        pw_entry.focus_set()

        err_label = Label(dialog, text="", bg=BG_COLOR, fg="#e74c3c", font=FONT)
        err_label.pack(pady=(0, 10))

        def confirm():
            pw = pw_entry.get()
            if not pw:
                err_label.config(text="Password is required.")
                return
            result["password"] = pw
            dialog.destroy()
            event.set()

        def cancel():
            dialog.destroy()
            event.set()

        Button(dialog, text="Reconnect", bg=BTN_BG, fg=BTN_FG, relief="flat",
               font=FONT_BOLD, cursor="hand2", command=confirm).pack(
            fill="x", pady=(0, 6), ipady=6)
        Button(dialog, text="Cancel", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
               font=FONT, cursor="hand2", command=cancel).pack(fill="x", ipady=4)

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        pw_entry.bind("<Return>", lambda e: confirm())

    window.after(0, show)
    event.wait()          # block background thread until dialog closes
    return result["password"]

api_client.set_reauth_prompt(_reauth_prompt)


def _ts(value):
    """Normalise a timestamp string for comparison.
    Strips timezone suffix so SQLite and PostgreSQL timestamps compare cleanly."""
    return str(value or "").replace("+00:00", "").replace("Z", "").strip()


def startup_sync_check():
    """Run in a background thread after login.
    - Server newer than last sync → prompt to download
    - Local vault modified after last sync → upload silently
    - No vault on server yet → upload silently"""
    if not api_client.is_logged_in():
        return

    status, code = api_client.get_vault_status()

    if code == 0 or status is None:
        return  # server unreachable — offline use continues normally

    if code == 401:
        return  # token expired — user will be prompted via Settings > Sync

    if not status.get("has_vault"):
        api_client.upload_vault()
        return

    server_modified = _ts(status.get("last_modified"))
    last_synced = _ts(api_client.get_last_synced())

    if server_modified > last_synced:
        # Server is newer — prompt user on main thread.
        def prompt():
            # Save local profile before confirming — download will overwrite vaultkit.bin.
            saved_profile = None
            try:
                saved_profile = get_user_profile(cipher)
            except Exception:
                pass
            answer = messagebox.askyesno(
                "Vault Updated",
                "Your vault was updated on another device.\n\n"
                "Download the latest version?\n"
                "(Your local copy will be replaced.)"
            )
            if answer:
                success, err = api_client.download_vault()
                if success:
                    load_vault_after_download(cipher, saved_profile)
                    messagebox.showinfo("Synced", "Vault updated successfully.")
                else:
                    messagebox.showerror("Sync Failed", err or "Could not download vault.")
        window.after(0, prompt)

    elif os.path.exists("vaultkit.bin"):
        # Check if local vault was modified after the last sync.
        local_mtime = _ts(
            datetime.datetime.fromtimestamp(
                os.path.getmtime("vaultkit.bin"), datetime.UTC
            ).strftime("%Y-%m-%d %H:%M:%S")
        )
        if local_mtime > last_synced:
            api_client.upload_vault()
            if sync_refresh_callback:
                window.after(0, sync_refresh_callback)


threading.Thread(target=startup_sync_check, daemon=True).start()

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
                      command=lambda: open_settings(window, cipher, BG_COLOR, ENTRY_BG,
                                                    ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG,
                                                    BTN_ACCENT, FONT, FONT_BOLD,
                                                    on_rekey=update_cipher,
                                                    on_sync_refresh=lambda fn: _set_sync_refresh(fn)))
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
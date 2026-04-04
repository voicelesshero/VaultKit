from tkinter import *
from tkinter import messagebox
import json
import os
import threading
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from profile import open_profile_form
from database import make_key, rekey_vault
import api_client
import session as session_module

ph = PasswordHasher()
VERSION = "1.5.1"


def open_settings(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                  BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD, on_rekey=None):

    win = Toplevel(window)
    win.title("Settings")
    win.config(padx=40, pady=40, bg=BG_COLOR)
    win.resizable(False, False)

    theme = (window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
             BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD)

    def section_label(text, row):
        Label(win, text=text, bg=BG_COLOR, fg=BTN_ACCENT,
              font=FONT_BOLD).grid(row=row, column=0, columnspan=2,
                                   sticky="w", pady=(16, 4))
        Frame(win, bg=BTN_ACCENT, height=1).grid(
            row=row + 1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

    def setting_btn(text, bg, row, command):
        Button(win, text=text, bg=bg, fg=BTN_FG, relief="flat",
               font=FONT, cursor="hand2", anchor="w",
               command=command).grid(row=row, column=0, columnspan=2,
                                     sticky="ew", ipady=6, pady=2)

    # ---------------------------- PROFILE ------------------------------- #
    section_label("Profile", 0)

    setting_btn("Edit Profile", ENTRY_BG, 2,
                lambda: [win.destroy(), open_profile_form(*theme)])

    # ---------------------------- SECURITY ------------------------------- #
    section_label("Security", 3)

    def change_master_password():
        dialog = Toplevel(window)
        dialog.title("Change Master Password")
        dialog.config(padx=30, pady=30, bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.grab_set()

        Label(dialog, text="Current Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=0, column=0, sticky="e", padx=(0, 10), pady=6)
        Label(dialog, text="New Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=1, column=0, sticky="e", padx=(0, 10), pady=6)
        Label(dialog, text="Confirm New:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
            row=2, column=0, sticky="e", padx=(0, 10), pady=6)

        current_entry = Entry(dialog, width=28, bg=ENTRY_BG, fg=ENTRY_FG,
                              insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
        current_entry.grid(row=0, column=1, ipady=5, pady=6)
        current_entry.focus_set()

        new_entry = Entry(dialog, width=28, bg=ENTRY_BG, fg=ENTRY_FG,
                          insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
        new_entry.grid(row=1, column=1, ipady=5, pady=6)

        confirm_entry = Entry(dialog, width=28, bg=ENTRY_BG, fg=ENTRY_FG,
                              insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
        confirm_entry.grid(row=2, column=1, ipady=5, pady=6)

        def submit():
            current = current_entry.get()
            new_pass = new_entry.get()
            confirm = confirm_entry.get()

            try:
                with open("master.json", "r") as f:
                    stored = json.load(f)
            except FileNotFoundError:
                messagebox.showerror("Error", "master.json not found.")
                return

            try:
                ph.verify(stored["master"], current)
            except VerifyMismatchError:
                messagebox.showerror("Access Denied", "Incorrect current password.")
                current_entry.delete(0, END)
                current_entry.focus_set()
                return

            if not new_pass:
                messagebox.showerror("Error", "New password cannot be empty.")
                new_entry.focus_set()
                return

            if new_pass != confirm:
                messagebox.showerror("Error", "Passwords do not match.")
                confirm_entry.delete(0, END)
                confirm_entry.focus_set()
                return

            new_salt = os.urandom(16)
            new_key = make_key(new_pass, new_salt)

            try:
                rekey_vault(cipher, new_key)
            except Exception:
                messagebox.showerror("Error", "Failed to re-encrypt vault. Password not changed.")
                return

            with open("master.json", "w") as f:
                json.dump({"master": ph.hash(new_pass), "kdf_salt": new_salt.hex()}, f)

            if on_rekey:
                on_rekey(new_key)

            messagebox.showinfo("Success", "Master password updated successfully.")
            dialog.destroy()
            win.destroy()

        Button(dialog, text="Update Password", bg=BTN_BG, fg=BTN_FG, relief="flat",
               font=FONT_BOLD, cursor="hand2", command=submit).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)

        current_entry.bind("<Return>", lambda e: new_entry.focus_set())
        new_entry.bind("<Return>", lambda e: confirm_entry.focus_set())
        confirm_entry.bind("<Return>", lambda e: submit())

    setting_btn("Change Master Password", ENTRY_BG, 5, change_master_password)

    # session timeout
    Label(win, text="Session Timeout:", bg=BG_COLOR, fg=LABEL_FG,
          font=FONT).grid(row=6, column=0, sticky="w", pady=(8, 2))

    timeout_var = IntVar()
    timeout_var.set(session_module.TIMEOUT_MINUTES)

    timeout_menu = OptionMenu(win, timeout_var, 5, 10, 15, 30, 60)
    timeout_menu.config(bg=ENTRY_BG, fg=ENTRY_FG, activebackground=BTN_ACCENT,
                        activeforeground=BTN_FG, relief="flat", font=FONT,
                        highlightthickness=0)
    timeout_menu["menu"].config(bg=ENTRY_BG, fg=ENTRY_FG, font=FONT)
    timeout_menu.grid(row=6, column=1, sticky="ew", pady=(8, 2))

    def save_timeout():
        session_module.TIMEOUT_MINUTES = timeout_var.get()
        session_module.TIMEOUT_SECONDS = timeout_var.get() * 60
        messagebox.showinfo("Saved", f"Session timeout set to {timeout_var.get()} minutes.")

    Button(win, text="Apply Timeout", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT, cursor="hand2", command=save_timeout).grid(
        row=7, column=0, columnspan=2, sticky="ew", ipady=5, pady=(4, 0))

    # ---------------------------- SYNC ------------------------------- #
    section_label("Sync", 8)

    sync_frame = Frame(win, bg=BG_COLOR)
    sync_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(0, 4))

    def build_sync_ui():
        for widget in sync_frame.winfo_children():
            widget.destroy()

        if api_client.is_logged_in():
            email = api_client.get_account_email() or ""
            last_synced = api_client.get_last_synced() or "Never"

            Label(sync_frame, text=email, bg=BG_COLOR, fg=ENTRY_FG,
                  font=FONT).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
            Label(sync_frame, text=f"Last synced: {last_synced}",
                  bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

            def do_sync():
                def run():
                    data, code = api_client.upload_vault()
                    def show():
                        if code == 200:
                            build_sync_ui()
                            messagebox.showinfo("Synced", "Vault synced successfully.")
                        elif code == 409:
                            answer = messagebox.askyesno(
                                "Conflict",
                                "Your vault was updated on another device.\n\n"
                                "Download the latest version?\n"
                                "(Your local changes will be replaced.)"
                            )
                            if answer:
                                success, err = api_client.download_vault()
                                if success:
                                    build_sync_ui()
                                    messagebox.showinfo("Synced", "Vault updated. Please restart VaultKit.")
                                else:
                                    messagebox.showerror("Sync Failed", err or "Download failed.")
                        elif code == 0:
                            messagebox.showerror("Sync Failed", "Could not reach sync server.")
                        else:
                            messagebox.showerror("Sync Failed", data.get("error", "Unknown error."))
                    win.after(0, show)
                threading.Thread(target=run, daemon=True).start()

            def do_logout():
                if messagebox.askyesno("Sign Out", "Sign out of sync account?\nYour local vault will not be affected."):
                    api_client.logout()
                    build_sync_ui()

            Button(sync_frame, text="Sync Now", bg=BTN_BG, fg=BTN_FG, relief="flat",
                   font=FONT, cursor="hand2", command=do_sync).grid(
                row=2, column=0, sticky="ew", ipady=5, padx=(0, 4))
            Button(sync_frame, text="Sign Out", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
                   font=FONT, cursor="hand2", command=do_logout).grid(
                row=2, column=1, sticky="ew", ipady=5)

        else:
            Label(sync_frame,
                  text="Sync your encrypted vault across devices.",
                  bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9)).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

            def open_auth_dialog(mode):
                dialog = Toplevel(win)
                dialog.title("Create Sync Account" if mode == "register" else "Sign In to Sync")
                dialog.config(padx=30, pady=30, bg=BG_COLOR)
                dialog.resizable(False, False)
                dialog.grab_set()

                Label(dialog, text="Email:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
                    row=0, column=0, sticky="e", padx=(0, 10), pady=6)
                Label(dialog, text="Password:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).grid(
                    row=1, column=0, sticky="e", padx=(0, 10), pady=6)

                email_var = StringVar()
                email_entry = Entry(dialog, textvariable=email_var, width=28, bg=ENTRY_BG,
                                    fg=ENTRY_FG, insertbackground=ENTRY_FG, relief="flat", font=FONT)
                email_entry.grid(row=0, column=1, ipady=5, pady=6)

                # Pre-fill email from profile — cipher is already in scope from open_settings
                from profile import get_profile_defaults
                defaults = get_profile_defaults(cipher)
                if defaults.get("email"):
                    email_var.set(defaults["email"])

                pw_entry = Entry(dialog, width=28, bg=ENTRY_BG, fg=ENTRY_FG,
                                 insertbackground=ENTRY_FG, relief="flat", font=FONT, show="*")
                pw_entry.grid(row=1, column=1, ipady=5, pady=6)
                pw_entry.focus_set() if defaults.get("email") else email_entry.focus_set()

                def submit():
                    email = email_var.get().strip()
                    password = pw_entry.get()
                    if not email or not password:
                        messagebox.showerror("Error", "Email and password are required.")
                        return

                    def run():
                        if mode == "register":
                            data, code = api_client.register(email, password)
                        else:
                            data, code = api_client.login(email, password)

                        def show():
                            if code in (200, 201):
                                # Upload vault immediately on first login/register
                                api_client.upload_vault()
                                dialog.destroy()
                                build_sync_ui()
                                messagebox.showinfo(
                                    "Sync Active",
                                    "Sync account connected. Vault uploaded."
                                )
                            else:
                                messagebox.showerror("Error", data.get("error", "Something went wrong."))
                        dialog.after(0, show)
                    threading.Thread(target=run, daemon=True).start()

                btn_text = "Create Account" if mode == "register" else "Sign In"
                Button(dialog, text=btn_text, bg=BTN_BG, fg=BTN_FG, relief="flat",
                       font=FONT_BOLD, cursor="hand2", command=submit).grid(
                    row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)

                email_entry.bind("<Return>", lambda e: pw_entry.focus_set())
                pw_entry.bind("<Return>", lambda e: submit())

            Button(sync_frame, text="Create Sync Account", bg=BTN_BG, fg=BTN_FG,
                   relief="flat", font=FONT, cursor="hand2",
                   command=lambda: open_auth_dialog("register")).grid(
                row=1, column=0, sticky="ew", ipady=5, padx=(0, 4))
            Button(sync_frame, text="Sign In", bg=ENTRY_BG, fg=LABEL_FG,
                   relief="flat", font=FONT, cursor="hand2",
                   command=lambda: open_auth_dialog("login")).grid(
                row=1, column=1, sticky="ew", ipady=5)

    build_sync_ui()

    # ---------------------------- ABOUT ------------------------------- #
    section_label("About", 11)

    Label(win, text=f"VaultKit  v{VERSION}", bg=BG_COLOR, fg=ENTRY_FG,
          font=FONT).grid(row=13, column=0, sticky="w", pady=2)

    Label(win, text="Secure personal vault for passwords,\nhealth info, and sensitive data.",
          bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9),
          justify="left").grid(row=14, column=0, columnspan=2, sticky="w", pady=(2, 8))

    def open_github():
        import webbrowser
        webbrowser.open("https://github.com/voicelesshero/vaultkit")

    Button(win, text="View on GitHub", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
           font=FONT, cursor="hand2", command=open_github).grid(
        row=15, column=0, columnspan=2, sticky="ew", ipady=5)
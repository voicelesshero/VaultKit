from tkinter import *
from tkinter import messagebox, simpledialog
import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from profile import open_profile_form
import session as session_module

ph = PasswordHasher()
VERSION = "1.5.0"


def open_settings(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                  BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD):

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
                lambda: [win.destroy(),
                         open_profile_form(*theme)])

    # ---------------------------- SECURITY ------------------------------- #
    section_label("Security", 3)

    def change_master_password():
        dialog = Toplevel(window)
        dialog.title("Change Master Password")
        dialog.config(padx=30, pady=30, bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.grab_set()  # modal

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

            with open("master.json", "w") as f:
                json.dump({"master": ph.hash(new_pass)}, f)

            messagebox.showinfo("Success", "Master password updated. Please restart VaultKit.")
            dialog.destroy()
            win.destroy()

        Button(dialog, text="Update Password", bg=BTN_BG, fg=BTN_FG, relief="flat",
               font=FONT_BOLD, cursor="hand2", command=submit).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0), ipady=6)

        # tab between fields naturally
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
        messagebox.showinfo("Saved",
                            f"Session timeout set to {timeout_var.get()} minutes.")

    Button(win, text="Apply Timeout", bg=BTN_BG, fg=BTN_FG, relief="flat",
           font=FONT, cursor="hand2", command=save_timeout).grid(
        row=7, column=0, columnspan=2, sticky="ew", ipady=5, pady=(4, 0))

    # ---------------------------- ABOUT ------------------------------- #
    section_label("About", 8)

    Label(win, text=f"VaultKit  v{VERSION}", bg=BG_COLOR, fg=ENTRY_FG,
          font=FONT).grid(row=10, column=0, sticky="w", pady=2)

    Label(win, text="Secure personal vault for passwords,\nhealth info, and sensitive data.",
          bg=BG_COLOR, fg=LABEL_FG, font=("Helvetica", 9),
          justify="left").grid(row=11, column=0, columnspan=2, sticky="w", pady=(2, 8))

    def open_github():
        import webbrowser
        webbrowser.open("https://github.com/voicelesshero/vaultkit")

    Button(win, text="View on GitHub", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
           font=FONT, cursor="hand2", command=open_github).grid(
        row=12, column=0, columnspan=2, sticky="ew", ipady=5)
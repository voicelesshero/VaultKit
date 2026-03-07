import hashlib
import urllib.request
from tkinter import messagebox


def check_password_breach(password):
    """
    Checks a password against the HaveIBeenPwned database using k-anonymity.
    The actual password is never sent to the API — only the first 5 characters
    of its SHA1 hash are transmitted.

    Returns: (breached: bool, count: int)
    """

    # Step 1: hash the password with SHA1
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()

    # Step 2: split into prefix (first 5 chars) and suffix (the rest)
    prefix = sha1[:5]
    suffix = sha1[5:]

    # Step 3: send only the prefix to the API
    url = f"https://api.pwnedpasswords.com/range/{prefix}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PersonalVaultApp"})
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode("utf-8")
    except Exception:
        return None, 0  # API unreachable, don't block the user

    # Step 4: check if our suffix appears in the returned list
    for line in body.splitlines():
        returned_suffix, count = line.split(":")
        if returned_suffix == suffix:
            return True, int(count)

    return False, 0


def check_and_notify(password):
    """
    Runs a breach check and shows an appropriate message to the user.
    Call this after saving or generating a password.
    """
    breached, count = check_password_breach(password)

    if breached is None:
        # API was unreachable, fail silently
        return

    if breached:
        messagebox.showwarning(
            "Password Compromised",
            f"This password has appeared in {count:,} known data breaches.\n\n"
            f"It is strongly recommended you use a different password."
        )
    else:
        messagebox.showinfo(
            "Password Safe",
            "This password has not been found in any known data breaches."
        )
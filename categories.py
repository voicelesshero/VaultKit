from tkinter import *
from tkinter import ttk, messagebox
from vault import get_all_entries, delete_entry, update_entry
from password_entry_form import open_password_form
from emergency import open_emergency_form
from health_entries import open_insurance_form, open_medication_form
from personal_entries import open_note_form, open_identity_form, open_wifi_form
from finance_entries import open_credit_card_form

CATEGORIES = ["All", "Personal", "Health", "Finance", "Family", "Work"]

ENTRY_TYPE_LABELS = {
    "password": "Password",
    "emergency": "Emergency Info",
    "insurance": "Insurance",
    "medication": "Medication",
    "note": "Secure Note",
    "credit_card": "Credit Card",
    "identity": "Identity",
    "wifi": "WiFi",
}

def open_category_view(window, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG, BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD):

    view = Toplevel(window)
    view.title("Vault - All Entries")
    view.config(padx=30, pady=30, bg=BG_COLOR)
    view.geometry("600x500")
    view.resizable(True, True)

    # --- Top bar: search and category filter ---
    top_frame = Frame(view, bg=BG_COLOR)
    top_frame.pack(fill="x", pady=(0, 16))

    Label(top_frame, text="Search:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).pack(side="left", padx=(0, 8))

    search_var = StringVar()
    search_entry = Entry(top_frame, textvariable=search_var, width=25, bg=ENTRY_BG, fg=ENTRY_FG,
                         insertbackground=ENTRY_FG, relief="flat", font=FONT)
    search_entry.pack(side="left", ipady=4, padx=(0, 16))

    Label(top_frame, text="Category:", bg=BG_COLOR, fg=LABEL_FG, font=FONT).pack(side="left", padx=(0, 8))

    category_var = StringVar()
    category_var.set("All")
    category_menu = OptionMenu(top_frame, category_var, *CATEGORIES)
    category_menu.config(bg=ENTRY_BG, fg=ENTRY_FG, activebackground=BTN_ACCENT,
                         activeforeground=BTN_FG, relief="flat", font=FONT, highlightthickness=0)
    category_menu["menu"].config(bg=ENTRY_BG, fg=ENTRY_FG, font=FONT)
    category_menu.pack(side="left")

    # --- Results list ---
    list_frame = Frame(view, bg=BG_COLOR)
    list_frame.pack(fill="both", expand=True)

    scrollbar = Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    columns = ("Name", "Type", "Category")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
    scrollbar.config(command=tree.yview)

    tree.heading("Name", text="Name")
    tree.heading("Type", text="Type")
    tree.heading("Category", text="Category")

    tree.column("Name", width=220)
    tree.column("Type", width=160)
    tree.column("Category", width=120)

    # style the treeview to match dark theme
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=ENTRY_BG, foreground=ENTRY_FG,
                     fieldbackground=ENTRY_BG, font=FONT, rowheight=28)
    style.configure("Treeview.Heading", background=BTN_ACCENT, foreground=BTN_FG,
                     font=FONT_BOLD)
    style.map("Treeview", background=[("selected", BTN_BG)])

    tree.pack(fill="both", expand=True)

    # --- Load and filter entries ---
    def on_double_click(event):
        selected = tree.selection()
        if not selected:
            return
        entry_id = selected[0]
        data = get_all_entries(cipher)
        entry = data.get(entry_id)
        if not entry:
            return

        detail_win = Toplevel(view)
        detail_win.title(entry_id)
        detail_win.config(padx=30, pady=30, bg=BG_COLOR)
        detail_win.resizable(False, False)

        row = 0
        for key, value in entry.items():
            if key == "type":
                continue
            Label(detail_win, text=f"{key.replace('_', ' ').title()}:", bg=BG_COLOR,
                  fg=LABEL_FG, font=FONT).grid(row=row, column=0, sticky="ne", padx=(0, 10), pady=4)
            Label(detail_win, text=value, bg=BG_COLOR, fg=ENTRY_FG, font=FONT,
                  wraplength=300, justify="left").grid(row=row, column=1, sticky="w", pady=4)
            row += 1

        theme_args = (view, cipher, BG_COLOR, ENTRY_BG, ENTRY_FG, LABEL_FG,
                      BTN_BG, BTN_FG, BTN_ACCENT, FONT, FONT_BOLD)

        _form_map = {
            "password":    lambda: open_password_form(*theme_args, entry_id=entry_id),
            "emergency":   lambda: open_emergency_form(*theme_args),
            "insurance":   lambda: open_insurance_form(*theme_args, entry_id=entry_id),
            "medication":  lambda: open_medication_form(*theme_args, entry_id=entry_id),
            "note":        lambda: open_note_form(*theme_args, entry_id=entry_id),
            "credit_card": lambda: open_credit_card_form(*theme_args, entry_id=entry_id),
            "identity":    lambda: open_identity_form(*theme_args, entry_id=entry_id),
            "wifi":        lambda: open_wifi_form(*theme_args, entry_id=entry_id),
        }
        entry_type = entry.get("type", "password")
        open_form = _form_map.get(entry_type)

        btn_frame = Frame(detail_win, bg=BG_COLOR)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        if open_form:
            def on_edit(fn=open_form):
                detail_win.destroy()
                fn()
            Button(btn_frame, text="Edit", bg=BTN_ACCENT, fg=BTN_FG, relief="flat",
                   font=FONT_BOLD, cursor="hand2", command=on_edit).pack(
                side="left", expand=True, fill="x", padx=(0, 4), ipady=4)

        Button(btn_frame, text="Close", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
               font=FONT_BOLD, cursor="hand2", command=detail_win.destroy).pack(
            side="left", expand=True, fill="x", ipady=4)

    tree.bind("<Double-1>", on_double_click)

    def load_entries():
        tree.delete(*tree.get_children())
        data = get_all_entries(cipher)
        search_term = search_var.get().lower()
        selected_category = category_var.get()

        for entry_id, entry in data.items():
            entry_type = entry.get("type", "password")
            entry_category = entry.get("category", "Personal")
            type_label = ENTRY_TYPE_LABELS.get(entry_type, entry_type.capitalize())

            # apply category filter
            if selected_category != "All" and entry_category != selected_category:
                continue

            # apply search filter
            if search_term and search_term not in entry_id.lower():
                continue

            tree.insert("", "end", iid=entry_id, values=(entry_id, type_label, entry_category))

    load_entries()

    # reload on search or category change
    search_var.trace("w", lambda *args: load_entries())
    category_var.trace("w", lambda *args: load_entries())

    # --- Bottom buttons ---
    btn_frame = Frame(view, bg=BG_COLOR)
    btn_frame.pack(fill="x", pady=(16, 0))

    def on_delete():
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Select Entry", "Please select an entry first.")
            return
        entry_id = selected[0]
        confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete '{entry_id}'?")
        if confirm:
            delete_entry(cipher, entry_id)
            load_entries()

    Button(btn_frame, text="Delete Selected", bg="#c0392b", fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=on_delete).pack(side="left", padx=(0, 8), ipady=4)

    Button(btn_frame, text="Refresh", bg=BTN_ACCENT, fg=BTN_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=load_entries).pack(side="left", ipady=4)

    Button(btn_frame, text="Close", bg=ENTRY_BG, fg=LABEL_FG, relief="flat",
           font=FONT_BOLD, cursor="hand2", command=view.destroy).pack(side="right", ipady=4)
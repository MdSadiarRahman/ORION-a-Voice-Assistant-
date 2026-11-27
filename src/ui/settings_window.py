"""
VoiceMate Laptop Agent - Settings Window UI Module.
Allows managing application permissions and address book contacts.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from src.helpers.app_helper import AppHelper
from src.helpers.app_preference_helper import AppPreferenceHelper
from src.helpers.contact_helper import ContactHelper

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("VoiceMate - সেটিংস")
        self.geometry("560x520")
        self.minsize(450, 400)
        self.configure(bg="#1E1E2E")

        # Tabbed interface
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Tab 1: App Permissions
        self.tab_apps = tk.Frame(notebook, bg="#181825")
        notebook.add(self.tab_apps, text="অ্যাপ পারমিশন")
        self._build_apps_tab()

        # Tab 2: Contacts
        self.tab_contacts = tk.Frame(notebook, bg="#181825")
        notebook.add(self.tab_contacts, text="কন্টাক্ট তালিকা")
        self._build_contacts_tab()

    def _build_apps_tab(self):
        lbl = tk.Label(
            self.tab_apps,
            text="অ্যাসিস্ট্যান্ট দিয়ে যে অ্যাপগুলো খুলতে চান তা নির্বাচন করুন:",
            fg="#CDD6F4", bg="#181825", font=("Segoe UI", 10, "bold")
        )
        lbl.pack(anchor="w", padx=10, pady=8)

        container = tk.Frame(self.tab_apps, bg="#181825")
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container, bg="#11111B", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#11111B")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar.pack(side="right", fill="y")

        apps = AppHelper.get_all_installed_apps()
        self.app_vars = {}
        for app in apps:
            var = tk.BooleanVar(value=AppPreferenceHelper.is_app_allowed(app.name))
            self.app_vars[app.name] = var
            chk = tk.Checkbutton(
                scrollable_frame,
                text=app.name,
                variable=var,
                command=lambda name=app.name, v=var: self._on_app_toggle(name, v),
                fg="#CDD6F4", bg="#11111B", selectcolor="#313244",
                activebackground="#11111B", activeforeground="#89B4FA",
                font=("Segoe UI", 9)
            )
            chk.pack(anchor="w", padx=8, pady=3)

    def _on_app_toggle(self, app_name: str, var: tk.BooleanVar):
        AppPreferenceHelper.set_app_permission(app_name, var.get())

    def _build_contacts_tab(self):
        lbl = tk.Label(
            self.tab_contacts,
            text="কন্টাক্ট লিস্ট (নাম ও ফোন নাম্বার):",
            fg="#CDD6F4", bg="#181825", font=("Segoe UI", 10, "bold")
        )
        lbl.pack(anchor="w", padx=10, pady=8)

        # Add Contact Form
        form_frame = tk.Frame(self.tab_contacts, bg="#181825")
        form_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(form_frame, text="নাম:", fg="#CDD6F4", bg="#181825").grid(row=0, column=0, padx=4, pady=2)
        self.entry_name = tk.Entry(form_frame, width=15)
        self.entry_name.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(form_frame, text="ফোন:", fg="#CDD6F4", bg="#181825").grid(row=0, column=2, padx=4, pady=2)
        self.entry_phone = tk.Entry(form_frame, width=15)
        self.entry_phone.grid(row=0, column=3, padx=4, pady=2)

        btn_add = tk.Button(
            form_frame, text="যোগ করুন",
            bg="#A6E3A1", fg="#11111B", font=("Segoe UI", 9, "bold"),
            command=self._add_contact
        )
        btn_add.grid(row=0, column=4, padx=8, pady=2)

        # Contacts listbox
        list_frame = tk.Frame(self.tab_contacts, bg="#11111B")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.contact_listbox = tk.Listbox(
            list_frame, bg="#11111B", fg="#CDD6F4", font=("Segoe UI", 10),
            selectbackground="#45475A"
        )
        self.contact_listbox.pack(side="left", fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.contact_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.contact_listbox.config(yscrollcommand=scrollbar.set)

        self._refresh_contacts()

    def _refresh_contacts(self):
        self.contact_listbox.delete(0, tk.END)
        for c in ContactHelper.get_all_contacts():
            self.contact_listbox.insert(tk.END, f"{c.get('name')} - {c.get('phone')} ({c.get('relation', '')})")

    def _add_contact(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        if not name or not phone:
            messagebox.showwarning("সতর্কতা", "দয়া করে নাম এবং ফোন নাম্বার লিখুন।")
            return
        ContactHelper.add_contact(name, phone)
        self.entry_name.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self._refresh_contacts()
        messagebox.showinfo("সফল", f"{name} কন্টাক্ট তালিকায় যোগ করা হয়েছে।")

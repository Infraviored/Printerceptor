import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import csv
import json
import pathlib
from rapidfuzz import process, fuzz
from .win32_utils import force_focus
from .config import CUSTOMERS_FILE

class CustomerOverlay:
    def __init__(self, root, customers, job_file_path):
        self.root = tk.Toplevel(root)
        self.customers = customers
        self.file_path = job_file_path
        self.selected_customer = None
        self.search_var = None
        self.tree = None
        self.filtered_customers = [] 
        self.sort_col = "Nachname"
        self.sort_desc = False
        
        self.setup_ui()
        
    def setup_ui(self):
        job_name = self.file_path.stem
        self.root.title(f"Zuweisung: {job_name}")
        
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#007acc"
        
        self.root.configure(bg=bg_color)
        self.root.geometry("900x850") # Wider for columns
        self.root.attributes("-topmost", True)
        
        # Center UI
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (900 // 2)
        y = (screen_height // 2) - (850 // 2)
        self.root.geometry(f"900x850+{x}+{y}")

        # Header with Count and Import Button
        top_bar = tk.Frame(self.root, bg="#2d2d2d")
        top_bar.pack(fill="x", padx=0, pady=0)
        
        self.count_label = tk.Label(top_bar, text=f"Kunden in Datenbank: {len(self.customers)}", 
                                    bg="#2d2d2d", fg="#aaaaaa", font=("Segoe UI", 10))
        self.count_label.pack(side="left", padx=10, pady=5)
        
        import_btn = tk.Button(top_bar, text="➕ Kunde / CSV Import", bg="#3e3e3e", fg="white",
                               font=("Segoe UI", 10), borderwidth=0, padx=10,
                               command=self.open_add_menu)
        import_btn.pack(side="right", padx=10, pady=5)

        # Title
        tk.Label(self.root, text=f"Kunde auswählen: {job_name}", 
                 bg=bg_color, fg=accent_color, font=("Segoe UI", 16, "bold")).pack(pady=20)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        
        search_entry = tk.Entry(self.root, textvariable=self.search_var, bg="#333333", fg=fg_color, 
                               insertbackground="white", border=0, font=("Segoe UI", 18))
        search_entry.pack(fill="x", padx=30, pady=10)

        # Treeview for Tabular View
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#252526", foreground="white", 
                        fieldbackground="#252526", borderwidth=0, font=("Segoe UI", 11), rowheight=30)
        style.map("Treeview", background=[('selected', accent_color)])
        style.configure("Treeview.Heading", background="#333333", foreground="white", relief="flat", font=("Segoe UI", 11, "bold"))

        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        columns = ("Nachname", "Vorname", "Adresse", "Telefon")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", style="Treeview")
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=150)
        
        self.tree.column("Adresse", width=300) # Give more space to address
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Confirm Button
        btn = tk.Button(self.root, text="Auswahl bestätigen (Enter)", bg=accent_color, fg="white", 
                        font=("Segoe UI", 16, "bold"), borderwidth=0, command=self.confirm)
        btn.pack(fill="x", padx=30, pady=30)
        
        self.root.bind("<Return>", lambda e: self.confirm())
        self.tree.bind("<Double-Button-1>", lambda e: self.confirm())
        
        # Focus Fixes
        self.root.update_idletasks()
        force_focus(self.root.winfo_id())
        self.root.after(100, search_entry.focus_set)
        
        self.update_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def sort_by(self, col):
        if self.sort_col == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col = col
            self.sort_desc = False
        self.update_list()

    def update_list(self, *args):
        search_term = self.search_var.get().strip().lower()
        
        if not search_term:
            self.filtered_customers = list(self.customers)
            
            # Sorting logic (Only when NOT searching)
            def sort_helper(value):
                v = str(value).lower().strip()
                return v if v else "\uffff"

            key_map = {
                "Nachname": lambda c: sort_helper(c.get('nachname', '')),
                "Vorname": lambda c: sort_helper(c.get('vorname', '')),
                "Adresse": lambda c: sort_helper(f"{c.get('street','')} {c.get('zip','')} {c.get('city','')}".strip()),
                "Telefon": lambda c: sort_helper(c.get('phone', ''))
            }
            self.filtered_customers.sort(key=key_map[self.sort_col], reverse=self.sort_desc)
        else:
            # Fuzzy match only on name or address (USER REQUEST)
            choices = []
            for c in self.customers:
                choices.append(f"{c.get('vorname','')} {c.get('nachname','')} {c.get('street','')} {c.get('city','')}")
            
            # process.extract returns results already sorted by score DESC
            results = process.extract(search_term, choices, scorer=fuzz.partial_ratio, limit=50)
            self.filtered_customers = [self.customers[idx] for text, score, idx in results if score > 35]

        # Clear and fill Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for p in self.filtered_customers:
            address = f"{p.get('street','')} {p.get('zip','')} {p.get('city','')}".strip()
            self.tree.insert("", tk.END, values=(
                p.get('nachname', ''),
                p.get('vorname', ''),
                address,
                p.get('phone', '')
            ))
            
        # Auto-highlight top result
        all_items = self.tree.get_children()
        if all_items:
            self.tree.selection_set(all_items[0])
            self.tree.focus(all_items[0])

    def confirm(self):
        selection = self.tree.selection()
        if selection:
            item_idx = self.tree.index(selection[0])
            self.selected_customer = self.filtered_customers[item_idx]
        elif len(self.filtered_customers) > 0:
            self.selected_customer = self.filtered_customers[0]
        
        if self.selected_customer:
            self.on_close()

    def open_add_menu(self):
        AddCustomerDialog(self.root, self.on_customers_updated)

    def on_customers_updated(self, updated_list):
        self.customers = updated_list
        self.count_label.config(text=f"Kunden in Datenbank: {len(self.customers)}")
        self.update_list()

    def on_close(self):
        self.root.destroy()

class AddCustomerDialog:
    def __init__(self, parent, callback):
        self.root = tk.Toplevel(parent)
        self.callback = callback
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Kunde hinzufügen / CSV Import")
        self.root.geometry("500x750")
        self.root.configure(bg="#1e1e1e")
        self.root.attributes("-topmost", True)
        
        # Center
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (750 // 2)
        self.root.geometry(f"500x750+{x}+{y}")
        
        fg_color = "white"
        bg_color = "#1e1e1e"
        
        tk.Label(self.root, text="Neuen Kunden anlegen", bg=bg_color, fg="#007acc", font=("Segoe UI", 16, "bold")).pack(pady=15)
        
        form_frame = tk.Frame(self.root, bg=bg_color)
        form_frame.pack(fill="x", padx=30)
        
        def add_field(label_text, var_name):
            tk.Label(form_frame, text=label_text, bg=bg_color, fg="#aaaaaa", font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
            ent = tk.Entry(form_frame, bg="#333333", fg=fg_color, borderwidth=0, font=("Segoe UI", 12))
            ent.pack(fill="x")
            setattr(self, var_name, ent)

        add_field("Vorname", "vorname_ent")
        add_field("Nachname", "nachname_ent")
        add_field("Firma / Organisation", "org_ent")
        add_field("Telefon", "phone_ent")
        add_field("Straße", "street_ent")
        add_field("ZIP / PLZ", "zip_ent")
        add_field("Ort / Stadt", "city_ent")
        
        tk.Button(self.root, text="💾 Speichern", bg="#007acc", fg="white", font=("Segoe UI", 12, "bold"), 
                  borderwidth=0, pady=10, command=self.save_manual).pack(fill="x", padx=30, pady=20)
        
        tk.Frame(self.root, height=1, bg="#444444").pack(fill="x", padx=30, pady=10)
        
        tk.Label(self.root, text="Google / Standard CSV Import", bg=bg_color, fg="#007acc", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        tk.Button(self.root, text="📁 CSV Datei wählen", bg="#3e3e3e", fg="white", font=("Segoe UI", 12), 
                  borderwidth=0, pady=10, command=self.import_csv).pack(fill="x", padx=30, pady=10)

    def save_manual(self):
        customer = {
            "vorname": self.vorname_ent.get().strip(),
            "nachname": self.nachname_ent.get().strip(),
            "organization": self.org_ent.get().strip(),
            "phone": self.phone_ent.get().strip(),
            "street": self.street_ent.get().strip(),
            "zip": self.zip_ent.get().strip(),
            "city": self.city_ent.get().strip()
        }
        
        if not customer["vorname"] and not customer["nachname"] and not customer["organization"]:
            messagebox.showerror("Fehler", "Mindestens Vorname, Nachname oder Firma erforderlich!")
            return
            
        self.add_and_save([customer])
        self.root.destroy()

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
            
        new_customers = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customer = {
                        "vorname": row.get("First Name", row.get("vorname", row.get("Name", ""))),
                        "nachname": row.get("Last Name", row.get("nachname", "")),
                        "organization": row.get("Organization Name", row.get("organization", "")),
                        "phone": row.get("Phone 1 - Value", row.get("phone", "")),
                        "street": row.get("Address 1 - Street", row.get("street", row.get("Address", ""))),
                        "zip": row.get("Address 1 - Postal Code", row.get("zip", "")),
                        "city": row.get("Address 1 - City", row.get("city", row.get("Ort", "")))
                    }
                    if any([customer["vorname"], customer["nachname"], customer["organization"]]):
                        new_customers.append(customer)
            
            if new_customers:
                self.add_and_save(new_customers)
                messagebox.showinfo("Erfolg", f"{len(new_customers)} Kunden importiert.")
                self.root.destroy()
            else:
                messagebox.showwarning("Info", "Keine gültigen Kunden in der Datei gefunden.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Importieren: {e}")

    def add_and_save(self, new_data):
        try:
            if pathlib.Path(CUSTOMERS_FILE).exists():
                with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
                    current = json.load(f)
            else:
                current = []
        except:
            current = []
            
        current.extend(new_data)
        
        with open(CUSTOMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
            
        self.callback(current)

class PrintConfirmationDialog:
    def __init__(self, root):
        self.root = tk.Toplevel(root)
        self.print_requested = False
        self.setup_ui()
        
    def setup_ui(self):
        self.root.title("Drucken?")
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        
        self.root.configure(bg=bg_color)
        self.root.geometry("400x250")
        self.root.attributes("-topmost", True)
        
        # Center
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (400 // 2)
        y = (screen_height // 2) - (250 // 2)
        self.root.geometry(f"400x250+{x}+{y}")

        tk.Label(self.root, text="Rechnung drucken?", 
                 bg=bg_color, fg=fg_color, font=("Segoe UI", 18, "bold")).pack(pady=40)
        
        btn_frame = tk.Frame(self.root, bg=bg_color)
        btn_frame.pack(fill="x", padx=20)
        
        # JA Button
        ja_btn = tk.Button(btn_frame, text="JA", bg="#28a745", fg="white", 
                           font=("Segoe UI", 16, "bold"), width=7, command=self.set_ja)
        ja_btn.pack(side="left", expand=True, padx=10)
        
        # NEIN Button
        nein_btn = tk.Button(btn_frame, text="NEIN", bg="#dc3545", fg="white", 
                             font=("Segoe UI", 16, "bold"), width=7, command=self.set_nein)
        nein_btn.pack(side="left", expand=True, padx=10)
        
        # Force focus to window
        self.root.update_idletasks()
        force_focus(self.root.winfo_id())
        
        self.root.bind("<Return>", lambda e: self.set_ja())
        self.root.bind("<Escape>", lambda e: self.set_nein())

    def set_ja(self):
        self.print_requested = True
        self.root.destroy()
        
    def set_nein(self):
        self.print_requested = False
        self.root.destroy()

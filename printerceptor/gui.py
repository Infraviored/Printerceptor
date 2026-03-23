import tkinter as tk
from tkinter import messagebox, filedialog
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
        self.list_box = None
        self.filtered_customers = [] # Track currently shown list
        
        self.setup_ui()
        
    def setup_ui(self):
        job_name = self.file_path.stem
        self.root.title(f"Zuweisung: {job_name}")
        
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#007acc"
        
        self.root.configure(bg=bg_color)
        self.root.geometry("750x850") # Wide enough for full names and phone
        self.root.attributes("-topmost", True)
        
        # Center UI
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (750 // 2)
        y = (screen_height // 2) - (850 // 2)
        self.root.geometry(f"750x850+{x}+{y}")

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

        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Größeres Listbox Font
        self.list_box = tk.Listbox(frame, bg="#252526", fg=fg_color, font=("Segoe UI", 14), 
                                  borderwidth=0, highlightthickness=0, selectbackground=accent_color)
        self.list_box.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame, orient="vertical", bg="#333333")
        scrollbar.pack(side="right", fill="y")
        self.list_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.list_box.yview)

        # Confirm Button (Groß)
        btn = tk.Button(self.root, text="Auswahl bestätigen (Enter)", bg=accent_color, fg="white", 
                        font=("Segoe UI", 16, "bold"), borderwidth=0, command=self.confirm)
        btn.pack(fill="x", padx=30, pady=30)
        
        self.root.bind("<Return>", lambda e: self.confirm())
        self.list_box.bind("<Double-Button-1>", lambda e: self.confirm())
        
        # Focus Fixes
        self.root.update_idletasks() # HWND ready
        force_focus(self.root.winfo_id())
        self.root.after(100, search_entry.focus_set)
        
        self.update_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_list(self, *args):
        search_term = self.search_var.get().strip().lower()
        self.list_box.delete(0, tk.END)
        
        # Display helper for customers
        def get_customer_string(c):
            # Combine all available info for searching
            elements = [
                c.get('vorname', ''), 
                c.get('nachname', ''), 
                c.get('organization', ''), 
                c.get('phone', ''),
                c.get('city', ''),
                c.get('street', ''),
                c.get('zip', '')
            ]
            return " | ".join([str(e) for e in elements if e])

        if not search_term:
            self.filtered_customers = self.customers
        else:
            choices = [get_customer_string(c) for c in self.customers]
            results = process.extract(search_term, choices, scorer=fuzz.partial_ratio, limit=20)
            self.filtered_customers = [self.customers[idx] for text, score, idx in results if score > 20]
        
        for p in self.filtered_customers:
            name = f"{p.get('vorname','')} {p.get('nachname','')}".strip()
            org = f" ({p['organization']})" if p.get('organization') else ""
            location = f" - {p.get('street','')}, {p.get('zip','')} {p.get('city','')}".strip(" - ,")
            phone = f" [📞 {p['phone']}]" if p.get('phone') else ""
            
            display_text = f"{name}{org}{location}{phone}"
            self.list_box.insert(tk.END, display_text)
            
        # Highlight top result
        if self.list_box.size() > 0:
            self.list_box.selection_clear(0, tk.END)
            self.list_box.selection_set(0)
            self.list_box.see(0)

    def confirm(self):
        selection = self.list_box.curselection()
        if selection:
            self.selected_customer = self.filtered_customers[selection[0]]
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
                    # Map based on provided Google format and common fallbacks
                    customer = {
                        "vorname": row.get("First Name", row.get("vorname", row.get("Name", ""))),
                        "nachname": row.get("Last Name", row.get("nachname", "")),
                        "organization": row.get("Organization Name", row.get("organization", "")),
                        "phone": row.get("Phone 1 - Value", row.get("phone", "")),
                        "street": row.get("Address 1 - Street", row.get("street", row.get("Address", ""))),
                        "zip": row.get("Address 1 - Postal Code", row.get("zip", "")),
                        "city": row.get("Address 1 - City", row.get("city", row.get("Ort", "")))
                    }
                    
                    # Store everything we have (USER REQUEST)
                    # We can store extra columns as generic metadata if they exist
                    # For now, we've mapped the core ones. If other columns are needed, they stay in 'row' but we only save what's used.
                    
                    # Basic validation: must have some name or org
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

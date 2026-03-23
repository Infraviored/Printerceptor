import tkinter as tk
from rapidfuzz import process, fuzz
from .win32_utils import force_focus

class CustomerOverlay:
    def __init__(self, root, customers, job_file_path):
        self.root = tk.Toplevel(root)
        self.customers = customers
        self.file_path = job_file_path
        self.selected_customer = None
        self.search_var = None
        self.list_box = None
        
        self.setup_ui()
        
    def setup_ui(self):
        job_name = self.file_path.stem
        self.root.title(f"Target Customer Match - {job_name}")
        
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#007acc"
        
        self.root.configure(bg=bg_color)
        self.root.geometry("500x600")
        self.root.attributes("-topmost", True)
        
        # Center UI
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (600 // 2)
        self.root.geometry(f"500x600+{x}+{y}")

        tk.Label(self.root, text=f"Match Customer for: {job_name}", bg=bg_color, fg=accent_color, font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        
        search_entry = tk.Entry(self.root, textvariable=self.search_var, bg="#333333", fg=fg_color, 
                               insertbackground="white", border=0, font=("Segoe UI", 14))
        search_entry.pack(fill="x", padx=20, pady=10)

        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.list_box = tk.Listbox(frame, bg="#252526", fg=fg_color, font=("Segoe UI", 11), 
                                  borderwidth=0, highlightthickness=0, selectbackground=accent_color)
        self.list_box.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.list_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.list_box.yview)

        btn = tk.Button(self.root, text="Confirm Selection", bg=accent_color, fg="white", 
                        font=("Segoe UI", 12, "bold"), borderwidth=0, command=self.confirm)
        btn.pack(fill="x", padx=20, pady=20)
        
        self.root.bind("<Return>", lambda e: self.confirm())
        self.list_box.bind("<Double-Button-1>", lambda e: self.confirm())
        
        # Focus Fixes
        self.root.update_idletasks() # HWND ready
        force_focus(self.root.winfo_id())
        self.root.after(100, search_entry.focus_set)
        
        self.update_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        self.list_box.delete(0, tk.END)
        
        if not search_term:
            filtered = self.customers
        else:
            choices = [f"{c['name']} | {c['address']} | {c['city']}" for c in self.customers]
            results = process.extract(search_term, choices, scorer=fuzz.partial_ratio, limit=10)
            filtered = [self.customers[idx] for text, score, idx in results if score > 30]
        
        for person in filtered:
            display_text = f"{person['name']} - {person['address']}, {person['city']}"
            self.list_box.insert(tk.END, display_text)

    def confirm(self):
        selection = self.list_box.curselection()
        if selection:
            display_text = self.list_box.get(selection[0])
            for c in self.customers:
                if f"{c['name']} - {c['address']}, {c['city']}" == display_text:
                    self.selected_customer = c
                    break
            self.on_close()

    def on_close(self):
        self.root.destroy()

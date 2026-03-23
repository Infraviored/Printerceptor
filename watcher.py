import time
import pathlib
import json
import threading
import queue
import tkinter as tk
from tkinter import ttk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fpdf import FPDF
from rapidfuzz import process, fuzz

# Configuration
WATCH_DIR = pathlib.Path("claw").absolute()
OUTPUT_DIR = pathlib.Path("output_pdfs").absolute()
ARCHIVE_DIR = pathlib.Path("archive").absolute()
CUSTOMERS_FILE = pathlib.Path("customers.json").absolute()

# Ensure directories exist
WATCH_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

class CustomerOverlay:
    def __init__(self, customers):
        self.customers = customers
        self.selected_customer = None
        self.root = None
        self.search_var = None
        self.list_box = None
        
    def show(self, job_name):
        self.root = tk.Tk()
        self.root.title(f"Target Customer Match - {job_name}")
        
        # --- UI DESIGN: Sleek Overlay ---
        # Dark theme
        bg_color = "#1e1e1e"
        fg_color = "#ffffff"
        accent_color = "#007acc"
        
        self.root.configure(bg=bg_color)
        self.root.geometry("500x600")
        self.root.attributes("-topmost", True) # Always on top
        self.root.overrideredirect(False) # Keep window decorations for easy moving
        
        # Centering the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (600 // 2)
        self.root.geometry(f"500x600+{x}+{y}")

        # Search Bar
        tk.Label(self.root, text=f"Match Customer for: {job_name}", bg=bg_color, fg=accent_color, font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_list)
        
        search_entry = tk.Entry(self.root, textvariable=self.search_var, bg="#333333", fg=fg_color, 
                               insertbackground="white", border=0, font=("Segoe UI", 14))
        search_entry.pack(fill="x", padx=20, pady=10)
        
        # Force focus so user can type immediately
        self.root.focus_force()
        search_entry.focus_set()
        search_entry.focus_force()

        # List Box for matches
        frame = tk.Frame(self.root, bg=bg_color)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.list_box = tk.Listbox(frame, bg="#252526", fg=fg_color, font=("Segoe UI", 11), 
                                  borderwidth=0, highlightthickness=0, selectbackground=accent_color)
        self.list_box.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.list_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.list_box.yview)

        # Confirm Button
        btn = tk.Button(self.root, text="Confirm Selection", bg=accent_color, fg="white", 
                        font=("Segoe UI", 12, "bold"), borderwidth=0, command=self.confirm)
        btn.pack(fill="x", padx=20, pady=20)
        
        # Key bindings
        self.root.bind("<Return>", lambda e: self.confirm())
        self.list_box.bind("<Double-Button-1>", lambda e: self.confirm())
        
        self.update_list()
        self.root.mainloop()
        return self.selected_customer

    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        self.list_box.delete(0, tk.END)
        
        if not search_term:
            filtered = self.customers
        else:
            # Fuzzy match across Name and Address
            choices = [f"{c['name']} | {c['address']} | {c['city']}" for c in self.customers]
            results = process.extract(search_term, choices, scorer=fuzz.partial_ratio, limit=10)
            
            # Reconstruct filtered list based on fuzzy scores
            filtered = []
            for text, score, idx in results:
                if score > 30: # Minimum match threshold
                    filtered.append(self.customers[idx])
        
        for person in filtered:
            display_text = f"{person['name']} - {person['address']}, {person['city']}"
            self.list_box.insert(tk.END, display_text)

    def confirm(self):
        selection = self.list_box.curselection()
        if selection:
            # Retrieve the original index from the data tags (saved in the display order)
            display_text = self.list_box.get(selection[0])
            # Find the actual customer object
            for c in self.customers:
                if f"{c['name']} - {c['address']}, {c['city']}" == display_text:
                    self.selected_customer = c
                    break
            self.root.destroy()

class ClawFileHandler(FileSystemEventHandler):
    def __init__(self, customers):
        self.customers = customers

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".txt"):
            return
            
        file_path = pathlib.Path(event.src_path)
        print(f"New print job detected: {file_path.name}")
        self.process_file(file_path)

    def process_file(self, file_path):
        time.sleep(1) # Wait for write completion
        
        try:
            # 1. Read input text
            encodings = ["utf-16", "utf-8", "cp1252", "latin-1"]
            text = None
            for enc in encodings:
                try:
                    content = file_path.read_text(encoding=enc)
                    if content.strip():
                        print(f"Successfully read with {enc}")
                        text = content
                        break
                except: continue
            
            if not text:
                print(f"Failed to read {file_path}")
                return

            # 2. Trigger Overlay for Client selection
            overlay = CustomerOverlay(self.customers)
            print("Action required: Please select a customer in the overlay.")
            customer = overlay.show(file_path.stem)
            
            if not customer:
                print("No customer selected. Aborting PDF generation.")
                return

            # 3. Render PDF with Selected Customer
            # Final filename format: YYYY_MM_DD-HH_MM-Name_name
            timestamp = time.strftime("%Y_%m_%d-%H_%M")
            safe_name = customer['name'].replace(" ", "_").replace("/", "-")
            final_filename = f"{timestamp}-{safe_name}"
            
            self.create_pdf_with_selection(text, final_filename, customer)
            
            # 4. Archive
            archive_path = ARCHIVE_DIR / file_path.name
            if archive_path.exists():
                archive_path = ARCHIVE_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
            
            file_path.replace(archive_path)
            print(f"Completed and archived: {file_path.name}")
            
        except Exception as e:
            print(f"Processing error: {e}")

    def create_pdf_with_selection(self, text, base_filename, customer):
        pdf = FPDF()
        pdf.add_page()
        
        # Selected Customer Header
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 7, f"{customer['name']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 5, f"{customer['address']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"{customer['city']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Courier", size=10)
        pdf.multi_cell(0, 5, text)
        
        output_path = OUTPUT_DIR / f"{base_filename}.pdf"
        pdf.output(str(output_path))
        print(f"Successfully generated: {output_path.name}")

def start_watcher():
    # Load Customers
    with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
        customers = json.load(f)
    
    event_handler = ClawFileHandler(customers)
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    
    print(f"WATCHER ACTIVE - Listening in {WATCH_DIR}")
    print("When a file appears, a selection overlay will pop up.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()

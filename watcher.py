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
import ctypes
from ctypes import wintypes

# Win32 API setup for focus stealing
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def force_focus(hwnd):
    """
    Direct Win32 hack to force focus to a window.
    """
    try:
        # 1. Show and bring to top
        user32.ShowWindow(hwnd, 5) # SW_SHOW
        user32.SetForegroundWindow(hwnd)
        
        # 2. Aggressive focus (AttachThreadInput hack)
        # Get the thread IDs
        foreground_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        current_thread = kernel32.GetCurrentThreadId()
        
        if foreground_thread != current_thread:
            user32.AttachThreadInput(current_thread, foreground_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(current_thread, foreground_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            
        print(f"Win32 focus triggered for HWND: {hwnd}")
    except Exception as e:
        print(f"Win32 focus error: {e}")

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
        
        # UI DESIGN: Dark theme
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
        search_entry.focus_set() # Example 1: Use immediate focus

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
        # Win32 Focus Hack: Grab focus from background
        self.root.update_idletasks() # Ensure HWND is ready
        hwnd = self.root.winfo_id()
        force_focus(hwnd)
        
        # Internal Entry Focus: Focus to text field
        self.root.after(150, search_entry.focus_set)
        
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

class ClawWatcherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide main root window
        self.job_queue = queue.Queue()
        self.customers = self.load_customers()
        
        # Start background poll for queue
        self.check_queue()
        
        # Start monitoring thread
        self.thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.thread.start()
        
    def load_customers(self):
        try:
            with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading customers: {e}")
            return []

    def check_queue(self):
        try:
            while True:
                job_path = self.job_queue.get_nowait()
                self.process_job(job_path)
        except queue.Empty:
            pass
        self.root.after(200, self.check_queue)

    def process_job(self, file_path):
        time.sleep(1) # File settling
        
        # Robust Reading
        encodings = ["utf-16", "utf-8", "cp1252", "latin-1"]
        text = None
        for enc in encodings:
            try:
                content = file_path.read_text(encoding=enc)
                if content.strip():
                    text = content
                    break
            except: continue
        
        if not text:
            print(f"Skipping empty file: {file_path}")
            return

        # Show Blocking Overlay
        print(f"Processing {file_path.name} - Waiting for user selection...")
        overlay = CustomerOverlay(self.root, self.customers, file_path)
        self.root.wait_window(overlay.root)
        
        customer = overlay.selected_customer
        if not customer:
            print("Job cancelled by user.")
            return

        # Generate output filename
        timestamp = time.strftime("%Y_%m_%d-%H_%M")
        safe_name = customer['name'].replace(" ", "_").replace("/", "-")
        final_filename = f"{timestamp}-{safe_name}.pdf"
        
        self.create_pdf(text, final_filename, customer)
        
        # Archive original
        archive_path = ARCHIVE_DIR / file_path.name
        if archive_path.exists():
            archive_path = ARCHIVE_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
        
        file_path.replace(archive_path)
        print(f"Done: {final_filename}")

    def create_pdf(self, text, final_filename, customer):
        pdf = FPDF()
        pdf.add_page()
        
        # Bold Header
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 7, f"{customer['name']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 5, f"{customer['address']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"{customer['city']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Courier", size=10)
        pdf.multi_cell(0, 5, text)
        
        output_path = OUTPUT_DIR / final_filename
        pdf.output(str(output_path))

    def start_monitoring(self):
        class Handler(FileSystemEventHandler):
            def __init__(self, q):
                self.q = q
            def on_created(self, event):
                if not event.is_directory and event.src_path.lower().endswith(".txt"):
                    self.q.put(pathlib.Path(event.src_path))
        
        observer = Observer()
        observer.schedule(Handler(self.job_queue), str(WATCH_DIR), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            observer.stop()
        observer.join()

    def run(self):
        print(f"Watcher started on: {WATCH_DIR}")
        self.root.mainloop()

if __name__ == "__main__":
    app = ClawWatcherApp()
    app.run()

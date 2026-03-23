import time
import pathlib
import json
import threading
import queue
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import WATCH_DIR, CUSTOMERS_FILE, setup_directories, load_user_config
from .processor import extract_text, create_pdf, archive_job
from .gui import CustomerOverlay

class ClawWatcherApp:
    def __init__(self):
        setup_directories()
        self.user_settings = load_user_config()
        self.root = tk.Tk()
        self.root.withdraw() # Hide root window
        self.job_queue = queue.Queue()
        self.customers = self.load_customers()
        
        # Start monitoring in a background thread
        self.thread = threading.Thread(target=self.start_monitoring, daemon=True)
        self.thread.start()
        
        # Start checking the queue
        self.check_queue()
        
    def load_customers(self):
        try:
            with open(CUSTOMERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading customers from {CUSTOMERS_FILE}: {e}")
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
        text = extract_text(file_path) # Now handles PDF and TXT
        if not text:
            print(f"Skipping unreadable or empty file: {file_path}")
            return

        # Show Blocking Overlay
        print(f"Processing {file_path.name} - Waiting for user selection...")
        overlay = CustomerOverlay(self.root, self.customers, file_path)
        self.root.wait_window(overlay.root)
        
        customer = overlay.selected_customer
        if not customer:
            print("Job cancelled by user.")
            return

        # Generate output PDF (our reformatted output)
        final_filename = create_pdf(text, file_path.stem, customer)
        
        # Archive the original
        if self.user_settings.get("archive_original", True):
            archive_job(file_path)
        else:
            print(f"Archiving is disabled for {file_path.name}")
        
        print(f"Workflow complete: {final_filename}")

    def start_monitoring(self):
        # We need the local ref to user settings in the handler
        supported = [ext.lower() for ext in self.user_settings.get("supported_formats", [".txt"])]
        
        class Handler(FileSystemEventHandler):
            def __init__(self, q, formats):
                self.q = q
                self.formats = formats
            def on_created(self, event):
                if not event.is_directory:
                    ext = pathlib.Path(event.src_path).suffix.lower()
                    if ext in self.formats:
                        self.q.put(pathlib.Path(event.src_path))
        
        observer = Observer()
        observer.schedule(Handler(self.job_queue, supported), str(WATCH_DIR), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            observer.stop()
        observer.join()

    def run(self):
        print(f"Printerceptor Active. Watching: {WATCH_DIR}...")
        print(f"Listening for: {', '.join(self.user_settings.get('supported_formats', ['.txt']))}")
        self.root.mainloop()

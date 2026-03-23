import time
import pathlib
import json
import threading
import queue
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import WATCH_DIR, CUSTOMERS_FILE, setup_directories
from .processor import read_robust, create_pdf, archive_job
from .gui import CustomerOverlay

class ClawWatcherApp:
    def __init__(self):
        setup_directories()
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
        text = read_robust(file_path)
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

        # Generate output PDF
        final_filename = create_pdf(text, file_path.stem, customer)
        
        # Archive
        archive_job(file_path)
        print(f"Workflow complete: {final_filename}")

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
        print(f"Printerceptor Active. Watching: {WATCH_DIR}...")
        self.root.mainloop()

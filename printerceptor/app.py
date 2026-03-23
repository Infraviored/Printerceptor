import time
import pathlib
import json
import threading
import queue
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import BON_INPUT_DIR, RECHNUNG_OUTPUT_DIR, CUSTOMERS_FILE, setup_directories, load_user_config
from .processor import extract_text, create_pdf, archive_job
from .gui import CustomerOverlay, PrintConfirmationDialog
from .win32_utils import silent_print_file

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
            print(f"Fehler beim Laden der Kunden von {CUSTOMERS_FILE}: {e}")
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
            print(f"Überspringe unlesbare oder leere Datei: {file_path}")
            return

        # 1. Show Customer Selector (Blocking)
        print(f"Kunde auswählen für {file_path.name}...")
        overlay = CustomerOverlay(self.root, self.customers, file_path)
        self.root.wait_window(overlay.root)
        
        customer = overlay.selected_customer
        if not customer:
            print("Vorgangsabbruch durch Benutzer.")
            return

        # 2. AUTO-PRINT BON (Original)
        if self.user_settings.get("auto_print_bon", True):
            bon_printer = self.user_settings.get("bon_printer")
            if bon_printer:
                silent_print_file(file_path, bon_printer)
        else:
            print("Automatischer Bon-Druck ist deaktiviert.")

        # 3. GENERATE REFORMATTED PDF (Rechnung)
        final_pdf_path = create_pdf(text, file_path.stem, customer)
        processed_pdf_path = RECHNUNG_OUTPUT_DIR / final_pdf_path
        
        # 4. ASK: RECHNUNG DRUCKEN?
        confirm_dialog = PrintConfirmationDialog(self.root)
        self.root.wait_window(confirm_dialog.root)
        
        if confirm_dialog.print_requested:
            rechnung_printer = self.user_settings.get("rechnung_printer")
            if rechnung_printer:
                # Print the newly generated PDF
                silent_print_file(processed_pdf_path, rechnung_printer)
            else:
                print("Rechnungs-Drucker nicht konfiguriert.")
        
        # 5. Archive the original raw file
        if self.user_settings.get("archive_original", True):
            archive_job(file_path)
        
        print(f"Workflow abgeschlossen: {final_pdf_path}")

    def start_monitoring(self):
        formats = [ext.lower() for ext in self.user_settings.get("supported_formats", [".txt", ".pdf"])]
        
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
        observer.schedule(Handler(self.job_queue, formats), str(BON_INPUT_DIR), recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            observer.stop()
        observer.join()

    def run(self):
        print(f"Printerceptor modular gestartet. Verzeichnis: {BON_INPUT_DIR}...")
        print(f"Formate: {', '.join(self.user_settings.get('supported_formats', ['.txt', '.pdf']))}")
        self.root.mainloop()

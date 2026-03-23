import time
import pathlib
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fpdf import FPDF

# Configuration
WATCH_DIR = pathlib.Path("claw").absolute()
OUTPUT_DIR = pathlib.Path("output_pdfs").absolute()
ARCHIVE_DIR = pathlib.Path("archive").absolute()

# Ensure directories exist
WATCH_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

class ClawFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = pathlib.Path(event.src_path)
        # Check for both .txt and .txt-temporary (some printers create both)
        if file_path.suffix.lower() == ".txt":
            print(f"Detected new file: {file_path.name}")
            self.process_file(file_path)

    def process_file(self, file_path):
        # Give the printer a moment to finish writing
        time.sleep(0.5)
        
        try:
            # Try multiple encodings for robustness (Windows printers often use UTF-16 or CP1252)
            encodings = ["utf-8", "utf-16", "cp1252", "latin-1"]
            text = None
            
            for enc in encodings:
                try:
                    text = file_path.read_text(encoding=enc)
                    # If we found non-empty text, success!
                    if text.strip():
                        print(f"Succeesfully read with {enc}")
                        break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if text is None:
                # Fallback to ignore errors if all else fails
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                print("Warning: Used fallback encoding (errors ignored)")

            print(f"Processing content of: {file_path.name}...")
            
            # --- POST-PROCESSING ---
            # You can add regex, LLM, or other logic here.
            processed_text = self.your_post_processing_logic(text)
            
            # Re-render as PDF if desired
            self.create_pdf_from_text(processed_text, file_path.stem)
            
            # Move to archive
            archive_path = ARCHIVE_DIR / file_path.name
            # If exists, append timestamp
            if archive_path.exists():
                archive_path = ARCHIVE_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
            
            file_path.replace(archive_path)
            print(f"Finished. File archived to '{archive_path.name}'.")
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    def your_post_processing_logic(self, text):
        """
        Your custom logic here!
        Example: Capitalize all headers or extract data.
        """
        print("--- Text Sample ---")
        print(text[:200] + ("..." if len(text) > 200 else ""))
        print("-------------------")
        return text

    def create_pdf_from_text(self, text, base_filename):
        pdf = FPDF()
        pdf.add_page()
        
        # Add Header (Dominic Hare)
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 7, "Dominic Hare", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 5, "Landsbergerstr. 29A", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, "86946 Issing", new_x="LMARGIN", new_y="NEXT")
        
        # Spacer
        pdf.ln(10)
        
        # Intercepted Body Text (Monospaced)
        pdf.set_font("Courier", size=10)
        pdf.multi_cell(0, 5, text)
        
        output_path = OUTPUT_DIR / f"{base_filename}_clean.pdf"
        pdf.output(str(output_path))
        print(f"PDF generated: {output_path.name}")

def start_watcher():
    event_handler = ClawFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    
    print(f"Watching for new files in: {WATCH_DIR}")
    print("Press Ctrl+C to stop.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()

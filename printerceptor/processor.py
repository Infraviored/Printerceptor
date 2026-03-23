import time
import pathlib
from fpdf import FPDF
from .config import OUTPUT_DIR, ARCHIVE_DIR

def read_robust(file_path):
    """
    Attempt multiple common Windows encodings to read the text file.
    """
    time.sleep(1) # Settle time
    encodings = ["utf-16", "utf-8", "cp1252", "latin-1"]
    
    for enc in encodings:
        try:
            content = file_path.read_text(encoding=enc)
            if content.strip():
                print(f"Succeesfully read with {enc}")
                return content
        except: continue
    return None

def create_pdf(text, job_name, customer):
    """
    Renders text and selected customer to a timestamped PDF.
    """
    timestamp = time.strftime("%Y_%m_%d-%H_%M")
    safe_name = customer['name'].replace(" ", "_").replace("/", "-")
    final_filename = f"{timestamp}-{safe_name}.pdf"
    
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
    return final_filename

def archive_job(file_path):
    """
    Safely moves the original text file to the archive directory.
    """
    archive_path = ARCHIVE_DIR / file_path.name
    if archive_path.exists():
        archive_path = ARCHIVE_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
    
    file_path.replace(archive_path)
    print(f"Archived original: {file_path.name}")

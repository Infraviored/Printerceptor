import time
import pathlib
from fpdf import FPDF
from pypdf import PdfReader
from .config import RECHNUNG_OUTPUT_DIR, ARCHIVE_DIR

def extract_text(file_path):
    """
    Main extraction dispatcher: Handles TXT (robust) and PDF extraction.
    """
    ext = file_path.suffix.lower()
    
    if ext == ".txt":
        return read_txt_robust(file_path)
    elif ext == ".pdf":
        return extract_pdf_txt(file_path)
    return None

def read_txt_robust(file_path):
    """
    Attempt multiple common Windows encodings for TXT files.
    """
    time.sleep(1) # Settle time
    encodings = ["utf-16", "utf-8", "cp1252", "latin-1"]
    
    for enc in encodings:
        try:
            content = file_path.read_text(encoding=enc)
            if content.strip():
                print(f"Succeesfully read TXT with {enc}")
                return content
        except: continue
    return None

def extract_pdf_txt(file_path):
    """
    Extracts text from a PDF file using pypdf.
    """
    time.sleep(1) # File lock settle
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        if full_text.strip():
            print(f"Successfully extracted text from PDF: {file_path.name}")
            return full_text
    except Exception as e:
        print(f"Error extracting from {file_path.name}: {e}")
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
    
    output_path = RECHNUNG_OUTPUT_DIR / final_filename
    pdf.output(str(output_path))
    return final_filename

def archive_job(file_path):
    """
    Safely moves the original (txt or pdf) to the archive directory.
    """
    archive_path = ARCHIVE_DIR / file_path.name
    if archive_path.exists():
        archive_path = ARCHIVE_DIR / f"{file_path.stem}_{int(time.time())}{file_path.suffix}"
    
    file_path.replace(archive_path)
    print(f"Archived original: {file_path.name}")

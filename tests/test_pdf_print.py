import pathlib
import json
import time
from printerceptor.win32_utils import silent_print_file
from printerceptor.config import load_user_config
from fpdf import FPDF

def test_pdf_print():
    """
    Test specifically if silent PDF printing works.
    (This is different from TXT printing which usually works via Notepad).
    """
    config = load_user_config()
    printer_name = config.get("rechnung_printer") or config.get("bon_printer")
    
    if not printer_name:
        print("Fehler: Kein Drucker in config.json gefunden!")
        return

    print(f"Test-PDF-Druck auf: {printer_name}")
    
    # Generate a tiny PDF to test
    test_pdf = pathlib.Path("test_pdf_structure.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="PRINTERCEPTOR PDF TEST", ln=1)
    pdf.output(str(test_pdf))
    
    print(f"Sende PDF-Druckbefehl für: {test_pdf.name}...")
    success = silent_print_file(test_pdf, printer_name, config.get("sumatra_path"))
    
    if success:
        print("\nBefehl gesendet. Falls kein Dialog kommt, ist alles OK.")
        print("Falls Fehler 31 kommt: Ihr Standard-PDF-Programm (z.B. Edge) erlaubt kein 'printto'.")
    else:
        print("\nFehler beim Senden des PDF-Druckbefehls.")

if __name__ == "__main__":
    test_pdf_print()

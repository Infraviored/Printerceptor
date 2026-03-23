import pathlib
import json
import time
from printerceptor.win32_utils import silent_print_file
from printerceptor.config import load_user_config

def run_test_print():
    # 1. Load config
    config = load_user_config()
    printer_name = config.get("original_printer")
    
    if not printer_name:
        print("Fehler: Kein 'original_printer' in config.json gefunden!")
        return

    print(f"Test-Druck auf: {printer_name}")
    
    # 2. Create a temporary hello world file
    test_file = pathlib.Path("test_hello_world.txt")
    test_content = f"""
    ========================================
    PRINTERCEPTOR TEST DRUCK
    ========================================
    Zeitpunkt: {time.strftime('%Y-%m-%d %H:%M:%S')}
    Drucker:   {printer_name}
    
    Hallo Welt! 
    Dieser Druck wurde automatisch ausgelöst.
    ========================================
    """
    test_file.write_text(test_content, encoding="utf-8")
    
    # 3. Trigger Print
    print("Sende Druckbefehl...")
    success = silent_print_file(test_file, printer_name)
    
    if success:
        print("\nBefehl gesendet. Bitte am Drucker prüfen.")
        print("Hinweis: Falls sich ein Programm öffnet, ist die Datei-Zuordnung (Verb 'printto') in Windows nicht korrekt konfiguriert.")
    else:
        print("\nFehler beim Senden des Druckbefehls.")

    # Cleanup optional
    # time.sleep(5)
    # test_file.unlink()

if __name__ == "__main__":
    run_test_print()

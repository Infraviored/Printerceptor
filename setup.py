import win32print
import json
import pathlib
import os

# Configuration Paths - Moved to config subdirectory
CONFIG_DIR = pathlib.Path("config")
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "supported_formats": [".txt", ".pdf"],
        "archive_original": True,
        "fuzzy_threshold": 30
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def run_setup():
    """
    Main Printerceptor Setup Routine
    """
    print("\n========================================")
    print("      PRINTERCEPTOR SYSTEM SETUP")
    print("========================================\n")
    
    config = load_config()

    # 1. Printer selection
    printers = [p[2] for p in win32print.EnumPrinters(2)]
    
    if printers:
        print("--- Drucker Auswahl ---")
        for i, name in enumerate(printers):
            print(f"[{i}] {name}")

        try:
            p1_idx = input(f"\nHaupt-Drucker Index (Aktuell: {config.get('original_printer', 'Keiner')}): ")
            if p1_idx.strip():
                config["original_printer"] = printers[int(p1_idx)]
                
            p2_idx = input(f"Zweit-Drucker Index (Aktuell: {config.get('secondary_printer', 'Keiner')}): ")
            if p2_idx.strip():
                config["secondary_printer"] = printers[int(p2_idx)]
        except (ValueError, IndexError):
            print("Ungültige Eingabe - Drucker-Einstellungen nicht geändert.")
    
    # 2. Add future settings hooks here
    print("\n--- Weitere Einstellungen ---")
    threshold = input(f"Fuzzy-Suche Empfindlichkeit (0-100, Aktuell: {config.get('fuzzy_threshold', 30)}): ")
    if threshold.strip():
        config["fuzzy_threshold"] = int(threshold)

    save_config(config)
    print("\n[OK] Setup abgeschlossen und gespeichert.")
    print(f"Datei: {CONFIG_FILE.name} in Ordner /config/")

if __name__ == "__main__":
    run_setup()

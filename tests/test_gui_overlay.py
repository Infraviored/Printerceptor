import tkinter as tk
import pathlib
import json
import os
import sys

# Ensure root directory is in path (so modular imports work)
# This script should be run from the root: python tests/test_gui_overlay.py
sys.path.append(os.getcwd())

try:
    from printerceptor.gui import CustomerOverlay
except ImportError:
    print("Error: Could not import printerceptor.gui. Please run from root directory.")
    sys.exit(1)

def run_gui_test():
    """Opens the customer selection UI directly for debugging."""
    root = tk.Tk()
    root.withdraw() # Hide the main root window
    
    customers_file = pathlib.Path("customers.json")
    if not customers_file.exists():
        print(f"Error: {customers_file} not found.")
        return
        
    print(f"Loading {customers_file}...")
    with open(customers_file, 'r', encoding='utf-8') as f:
        customers = json.load(f)
        
    dummy_job = pathlib.Path("data/bon_input/2026_03_23-22_TEST_JOB.txt")
    
    print("UI is opening... please check your taskbar.")
    overlay = CustomerOverlay(root, customers, dummy_job)
    root.wait_window(overlay.root)
    
    if overlay.selected_customer:
        print(f"\nSelect result: {overlay.selected_customer}")
    else:
        print("\nUI was closed without selection.")

if __name__ == "__main__":
    run_gui_test()

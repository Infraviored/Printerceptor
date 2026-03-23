import ctypes
import pathlib
import win32api
import win32print
import subprocess

# Native Windows APIs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def force_focus(hwnd):
    """
    Direct Win32 hack to force focus to a window.
    """
    try:
        # Show and bring to top
        user32.ShowWindow(hwnd, 5) # SW_SHOW
        user32.SetForegroundWindow(hwnd)
        
        # Aggressive focus (AttachThreadInput hack)
        # We try to attach our thread to the foreground one
        foreground_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        current_thread = kernel32.GetCurrentThreadId()
        
        if foreground_thread != current_thread:
            user32.AttachThreadInput(current_thread, foreground_thread, True)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            user32.AttachThreadInput(current_thread, foreground_thread, False)
        else:
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)
            
        print(f"Win32 focus triggered for HWND: {hwnd}")
    except Exception as e:
        print(f"Win32 focus error: {e}")

def silent_print_file(file_path, printer_name, sumatra_path=None):
    """
    Triggers a silent print of a file to a specific Windows printer.
    Uses SumatraPDF for PDFs or 'printto' verb for other files.
    """
    try:
        if not printer_name:
            print("Kein Drucker konfiguriert, überspringe Druck.")
            return False
            
        print(f"Drucke {file_path.name} auf '{printer_name}'...")
        file_path = pathlib.Path(file_path) # Ensure it's a Path object
        
        # Use SumatraPDF for PDFs (much more reliable for silent printing)
        if file_path.suffix.lower() == ".pdf" and sumatra_path:
            cmd = [sumatra_path, "-print-to", printer_name, "-silent", str(file_path)]
            subprocess.run(cmd, check=True)
            return True
        else:
            # Fallback to verb "printto" for TXT etc. Or if sumatra_path missing
            win32api.ShellExecute(0, "printto", str(file_path), f'"{printer_name}"', ".", 0)
            return True
    except Exception as e:
        print(f"Fehler beim Drucken auf {printer_name}: {e}")
        return False

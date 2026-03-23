import ctypes

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

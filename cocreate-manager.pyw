import time
import datetime
import win32gui
import win32process
import win32api
import win32event
import winerror
import sys
import psutil
import threading
import pystray
import os
import win32com.client
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw
import json

INITIAL_UTC_YEAR = datetime.datetime.now(datetime.UTC).year

DOCUMENTS_FOLDER = os.path.expanduser("~\\Documents")
SETTINGS_FILE = os.path.join(DOCUMENTS_FOLDER, "cocreate_manager_settings.json")

TARGET_EXE = ""
TARGET_YEAR = 2013
AUTO_LAUNCHER_EXE = ""
AUTO_LAUNCH_INTERVAL = 60

running = True

def load_settings():
    global TARGET_EXE, TARGET_YEAR, AUTO_LAUNCHER_EXE, AUTO_LAUNCH_INTERVAL
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                TARGET_EXE = settings.get("TARGET_EXE", "")
                TARGET_YEAR = settings.get("TARGET_YEAR", 2013)
                AUTO_LAUNCHER_EXE = settings.get("AUTO_LAUNCHER_EXE", "")
                AUTO_LAUNCH_INTERVAL = settings.get("AUTO_LAUNCH_INTERVAL", 60)
        except Exception:
            pass

def get_active_window_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return None

def change_system_year(target_year):
    now = datetime.datetime.now(datetime.UTC)
    if now.year == target_year:
        return

    win_day_of_week = (now.weekday() + 1) % 7
    
    try:
        win32api.SetSystemTime(
            target_year,
            now.month,
            win_day_of_week,
            now.day,
            now.hour,
            now.minute,
            now.second,
            now.microsecond // 1000
        )
    except Exception:
        pass

def monitor_app_focus():
    global running
    app_is_focused = False

    while running:
        if not TARGET_EXE:
            time.sleep(1)
            continue

        active_app = get_active_window_process_name()

        if active_app == TARGET_EXE.lower():
            if not app_is_focused:
                change_system_year(TARGET_YEAR)
                app_is_focused = True
        else:
            if app_is_focused:
                change_system_year(INITIAL_UTC_YEAR)
                app_is_focused = False
        
        time.sleep(0.5)
    
    change_system_year(INITIAL_UTC_YEAR)

def auto_launcher_task():
    global running
    last_launch_time = 0
    
    while running:
        if AUTO_LAUNCHER_EXE and AUTO_LAUNCH_INTERVAL > 0:
            current_time = time.time()
            if current_time - last_launch_time >= AUTO_LAUNCH_INTERVAL:
                try:
                    directory = os.path.dirname(AUTO_LAUNCHER_EXE) or None
                    win32api.ShellExecute(0, "runas", AUTO_LAUNCHER_EXE, None, directory, 1)
                except Exception:
                    pass
                last_launch_time = current_time
                
        time.sleep(1)

def open_settings_ui():
    def run_gui():
        global TARGET_EXE, TARGET_YEAR, AUTO_LAUNCHER_EXE, AUTO_LAUNCH_INTERVAL
        
        root = tk.Tk()
        root.title("Cocreate Manager Settings")
        root.geometry("400x380")
        root.attributes("-topmost", True)
        
        exe_var = tk.StringVar(value=TARGET_EXE)
        year_var = tk.IntVar(value=TARGET_YEAR)
        launcher_var = tk.StringVar(value=AUTO_LAUNCHER_EXE)
        interval_var = tk.IntVar(value=AUTO_LAUNCH_INTERVAL)

        def browse_target():
            filepath = filedialog.askopenfilename(
                title="Select Target Executable or Shortcut",
                filetypes=[("Executables & Shortcuts", "*.exe;*.lnk"), ("All Files", "*.*")]
            )
            if filepath:
                if filepath.lower().endswith(".lnk"):
                    try:
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(filepath)
                        filepath = shortcut.Targetpath
                    except Exception:
                        pass
                filename = os.path.basename(filepath)
                exe_var.set(filename)
                
        def browse_launcher():
            filepath = filedialog.askopenfilename(
                title="Select App to Auto-Launch",
                filetypes=[("Executables & Shortcuts", "*.exe;*.bat;*.cmd;*.lnk"), ("All Files", "*.*")]
            )
            if filepath:
                launcher_var.set(filepath)

        def save_settings():
            global TARGET_EXE, TARGET_YEAR, AUTO_LAUNCHER_EXE, AUTO_LAUNCH_INTERVAL
            TARGET_EXE = exe_var.get()
            AUTO_LAUNCHER_EXE = launcher_var.get()
            
            try:
                TARGET_YEAR = year_var.get()
                AUTO_LAUNCH_INTERVAL = interval_var.get()
            except tk.TclError:
                pass
            
            try:
                with open(SETTINGS_FILE, "w") as f:
                    json.dump({
                        "TARGET_EXE": TARGET_EXE, 
                        "TARGET_YEAR": TARGET_YEAR,
                        "AUTO_LAUNCHER_EXE": AUTO_LAUNCHER_EXE,
                        "AUTO_LAUNCH_INTERVAL": AUTO_LAUNCH_INTERVAL
                    }, f)
            except Exception:
                pass

            root.destroy()

        # CoCreate Manager Settings
        tk.Label(root, text="--- CoCreate Manager ---", font=("Helvetica", 10, "bold")).pack(pady=(10, 0))
        tk.Label(root, text="Target Executable Name (e.g., cocreate.exe):").pack(pady=(5, 0))
        exe_frame = tk.Frame(root)
        exe_frame.pack(pady=2)
        tk.Entry(exe_frame, textvariable=exe_var, width=25).pack(side=tk.LEFT, padx=5)
        tk.Button(exe_frame, text="Browse", command=browse_target).pack(side=tk.LEFT)

        tk.Label(root, text="Target Year:").pack(pady=(5, 0))
        tk.Entry(root, textvariable=year_var, width=10).pack(pady=2)

        # Auto Launcher Settings
        tk.Label(root, text="--- Auto Launcher ---", font=("Helvetica", 10, "bold")).pack(pady=(15, 0))
        tk.Label(root, text="Auto-Launch App Path:").pack(pady=(5, 0))
        launcher_frame = tk.Frame(root)
        launcher_frame.pack(pady=2)
        tk.Entry(launcher_frame, textvariable=launcher_var, width=25).pack(side=tk.LEFT, padx=5)
        tk.Button(launcher_frame, text="Browse", command=browse_launcher).pack(side=tk.LEFT)
        
        tk.Label(root, text="Launch Interval (Seconds):").pack(pady=(5, 0))
        tk.Entry(root, textvariable=interval_var, width=10).pack(pady=2)

        tk.Button(root, text="Save & Apply", command=save_settings).pack(pady=15)
        
        root.mainloop()

    threading.Thread(target=run_gui, daemon=True).start()

def create_icon_image():
    image = Image.new('RGB', (64, 64), color=(0, 128, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
    return image

def on_settings(icon, item):
    open_settings_ui()

def on_quit(icon, item):
    global running
    running = False
    icon.stop()

def main():
    mutex_name = "Global\\CocreateManager_SingleInstance_Mutex"
    mutex = win32event.CreateMutex(None, False, mutex_name)
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        sys.exit(0)

    load_settings()
    
    monitor_thread = threading.Thread(target=monitor_app_focus)
    monitor_thread.start()
    
    auto_launch_thread = threading.Thread(target=auto_launcher_task)
    auto_launch_thread.start()

    menu = pystray.Menu(
        pystray.MenuItem('Settings', on_settings),
        pystray.MenuItem('Quit', on_quit)
    )
    icon = pystray.Icon("CocreateManager", create_icon_image(), "Cocreate Manager", menu)
    
    icon.run()
    monitor_thread.join()
    auto_launch_thread.join()

if __name__ == "__main__":
    main()
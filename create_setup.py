import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

# Config
APP_NAME = "FacePro"
APP_VERSION = "1.0"
SOURCE_DIR = "dist/FacePro"
SETUP_FILENAME = f"{APP_NAME}_Setup_v{APP_VERSION}.exe"

INSTALLER_SCRIPT_CONTENT = r"""
import os
import sys
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import shutil
import winshell
import pythoncom  # <--- VACIB
from win32com.client import Dispatch

APP_NAME = "FacePro"
DEFAULT_INSTALL_DIR = os.path.join(os.environ['LOCALAPPDATA'], APP_NAME)

def create_shortcut(target_path, shortcut_path):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    shortcut.IconLocation = target_path
    shortcut.save()

class InstallerApp(tk.Tk):
    # ... (init qalir) ...
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} Installer")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Header
        header = tk.Label(self, text=f"Install {APP_NAME}", font=("Segoe UI", 16, "bold"), bg="#2b2b2b", fg="white", pady=15)
        header.pack(fill="x")
        
        # Content
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        lbl = tk.Label(frame, text="Destination Folder:")
        lbl.pack(anchor="w")
        
        self.path_var = tk.StringVar(value=DEFAULT_INSTALL_DIR)
        path_entry = ttk.Entry(frame, textvariable=self.path_var)
        path_entry.pack(fill="x", pady=(5, 10))
        
        # Progress
        self.progress = ttk.Progressbar(frame, mode='determinate')
        self.progress.pack(fill="x", pady=20)
        
        self.status_lbl = tk.Label(frame, text="Ready to install", fg="gray")
        self.status_lbl.pack()
        
        # Buttons
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill="x", side="bottom")
        
        self.install_btn = ttk.Button(btn_frame, text="Install", command=self.start_install)
        self.install_btn.pack(side="right", padx=20)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right")
        
    def start_install(self):
        self.install_btn.config(state="disabled")
        target_dir = self.path_var.get()
        threading.Thread(target=self.run_installation, args=(target_dir,), daemon=True).start()
        
    def run_installation(self, target_dir):
        try:
            pythoncom.CoInitialize()  # <--- Thread üçün COM başlat
            
            self.status_lbl.config(text="Extracting files...")
            
            # Get path to embedded zip (it's attached to the end of this exe or inside _internal)
            # In onefile mode, resources are in sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                payload_path = os.path.join(sys._MEIPASS, "payload.zip")
            else:
                payload_path = "payload.zip"
            
            if not os.path.exists(payload_path):
                raise Exception("Payload not found!")
                
            # Create dir
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir) # Clean install
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract
            with zipfile.ZipFile(payload_path, 'r') as zf:
                files = zf.namelist()
                total = len(files)
                for i, file in enumerate(files):
                    zf.extract(file, target_dir)
                    # Update progress
                    percent = (i / total) * 100
                    self.progress['value'] = percent
                    self.update_idletasks()
            
            self.progress['value'] = 100
            self.status_lbl.config(text="Creating shortcuts...")
            
            # Create Shortcut
            exe_path = os.path.join(target_dir, "FacePro.exe")
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
            create_shortcut(exe_path, shortcut_path)
            
            messagebox.showinfo("Success", f"{APP_NAME} installed successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.install_btn.config(state="normal")
            self.status_lbl.config(text="Installation failed")

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
"""

def create_installer():
    print(f"Creating Installer for {APP_NAME}...")
    
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: {SOURCE_DIR} not found. Run build_exe.py first.")
        return

    # 1. Create payload.zip
    print("Compressing files...")
    with zipfile.ZipFile("payload.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, SOURCE_DIR)
                zf.write(abs_path, rel_path)
    
    # 2. Write installer script
    with open("installer_gui.py", "w", encoding="utf-8") as f:
        f.write(INSTALLER_SCRIPT_CONTENT)
        
    # 3. Build Installer EXE using PyInstaller
    print("Building Installer EXE...")
    subprocess.check_call([
        "pyinstaller",
        "--name", f"{APP_NAME}_Setup",
        "--onefile",
        "--windowed",
        "--add-data", "payload.zip;.",
        "--hidden-import", "winshell",
        "--hidden-import", "win32com.client",
        "installer_gui.py"
    ])
    
    # 4. Cleanup
    if os.path.exists("dist/FacePro_Setup.exe"):
        shutil.move("dist/FacePro_Setup.exe", SETUP_FILENAME)
        print(f"Installer created: {SETUP_FILENAME}")
    
    # Clean temporary files
    # os.remove("payload.zip")
    # os.remove("installer_gui.py")
    # os.remove("installer_gui.spec")

if __name__ == "__main__":
    # Install dependencies for installer script
    subprocess.check_call([sys.executable, "-m", "pip", "install", "winshell", "pywin32"])
    create_installer()

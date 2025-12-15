
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

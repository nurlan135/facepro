import os
import subprocess
import shutil
import sys
from pathlib import Path

# Config
APP_NAME = "FacePro"
MAIN_SCRIPT = "main.py"
ICON_FILE = "icon.ico"  # Əgər yoxdursa, default istifadə olunacaq
OUTPUT_DIR = "dist"
WORK_DIR = "build"

def install_pyinstaller():
    """PyInstaller quraşdırır."""
    print("Checking PyInstaller...")
    try:
        import PyInstaller
        print("PyInstaller already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """EXE faylını yaradır."""
    print(f"Building {APP_NAME}...")
    
    # PyInstaller argumentləri
    args = [
        'pyinstaller',
        '--name', APP_NAME,
        '--onedir',  # Bir qovluq (sürətli start üçün)
        '--windowed',  # Konsol pəncərəsini gizlət (GUI üçün)
        '--noconfirm',
        '--clean',
        # Data faylları (src module kimi)
        '--add-data', 'src;src',
        '--add-data', 'config;config',
        # Gizli importlar (bəzən PyInstaller görmür)
        '--hidden-import', 'src.utils.logger',
        '--hidden-import', 'src.utils.i18n',
        '--hidden-import', 'src.core.ai_thread',
        '--hidden-import', 'pyqt6',
        '--hidden-import', 'numpy',
        '--hidden-import', 'cv2',
        '--hidden-import', 'face_recognition',
        # Modelleri daxil et
        '--collect-data', 'face_recognition_models',
    ]
    
    # Icon varsa əlavə et
    if os.path.exists(ICON_FILE):
        args.extend(['--icon', ICON_FILE])
    
    # Main script
    args.append(MAIN_SCRIPT)
    
    # Run
    subprocess.check_call(args)

def post_build_cleanup():
    """Build sonrası təmizlik və kopyalama."""
    print("Post-build cleanup...")
    
    dist_path = Path(OUTPUT_DIR) / APP_NAME
    
    # Data qovluqlarını yaradaq
    data_dir = dist_path / 'data'
    data_dir.mkdir(exist_ok=True)
    (data_dir / 'db').mkdir(exist_ok=True)
    (data_dir / 'faces').mkdir(exist_ok=True)
    (data_dir / 'logs').mkdir(exist_ok=True)
    
    # Config qovluğunu kopyala (əgər pyinstaller add-data etməyibsə)
    # PyInstaller --add-data "config;config" edib, amma config faylları
    # user tərəfindən dəyişdirilə bilən olmalıdır (external).
    # Ona görə də manual olaraq dist qovluğuna kopyalayırıq ki, exe yanında olsun.
    
    src_config = Path("config")
    dest_config = dist_path / "config"
    
    if src_config.exists():
        # Mövcud config fayllarını (əgər varsa) silib təzəsini qoyuruq
        # ki default settings olsun.
        if dest_config.exists():
            shutil.rmtree(dest_config)
        shutil.copytree(src_config, dest_config)
        print(f"Copied config to {dest_config}")
        
    # YOLO Model-i kopyala (varsa)
    yolo_model = Path("yolov8n.pt")
    if yolo_model.exists():
        shutil.copy2(yolo_model, dist_path / "yolov8n.pt")
        print("Copied yolov8n.pt")
        
    print("-" * 50)
    print(f"Build SUCCESSFUL!")
    print(f"Executable location: {dist_path / (APP_NAME + '.exe')}")
    print("-" * 50)

if __name__ == "__main__":
    if not os.path.exists(MAIN_SCRIPT):
        print(f"Error: {MAIN_SCRIPT} not found!")
        sys.exit(1)
        
    install_pyinstaller()
    build_executable()
    post_build_cleanup()

"""
FacePro License Manager Module
Offline hardware-based license verification system.

Based on LICENSE_SPEC.md:
- Machine ID: SHA-256 hash of CPU + Motherboard IDs
- License Key: Base32 encoded SHA-256 hash of (Machine ID + Salt)
"""

import hashlib
import base64
import subprocess
import platform
import os
from typing import Optional, Tuple

# =====================================================================
# SECRET SALT - Bu dəyər gizli saxlanılmalıdır!
# Produksiyada bu dəyəri dəyişdirin və obfuscate edin.
# =====================================================================
_SECRET_SALT = "FaceGuard_v1_$uper$ecure_2025!"

# License file location
_LICENSE_FILE = ".license"


def _run_command(command: str) -> str:
    """
    Skel shell komandasını işlədir.
    """
    # Konsol pəncərəsini gizlətmək üçün flags
    startupinfo = None
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=5,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        )
        return result.stdout.strip()
    except Exception:
        return ""

def _get_system_uuid() -> str:
    """Windows System UUID əldə edir (Ən stabil unikal ID)."""
    if platform.system() == "Windows":
        # wmic csproduct get uuid
        try:
            output = _run_command("wmic csproduct get uuid")
            # Output adətən belə olur:
            # UUID
            # 4C4C4544-0042-4410-8053-C7C04F355032
            lines = output.split('\n')
            if len(lines) >= 2:
                return lines[1].strip()
        except:
            pass
            
        # Fallback: Powershell
        try:
            ps_cmd = 'powershell -command "Get-WmiObject Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"'
            return _run_command(ps_cmd)
        except:
            pass
            
    return "UNKNOWN_UUID"

def _get_volume_serial() -> str:
    """C: diskinin serial nömrəsini alır."""
    if platform.system() == "Windows":
        try:
            output = _run_command("vol c:")
            # Output: Volume Serial Number is XXXX-XXXX
            if "Serial Number is" in output:
                return output.split("Serial Number is")[-1].strip()
        except:
            pass
    return "UNKNOWN_VOL"

def get_machine_id() -> str:
    """
    Maşın ID-sini yaradır (Təkmilləşdirilmiş).
    
    Kombinasiya: System UUID + Disk Serial (Daha stabil)
    CpuId və MotherboardId bəzən dəyişmir (Generic olur).
    
    Format: XXXX-XXXX-XXXX-XXXX (16 char, uppercase)
    """
    # Hardware məlumatlarını yığ
    uuid = _get_system_uuid()
    vol_serial = _get_volume_serial()
    
    # Əlavə təhlükəsizlik: CPU ProcessorID (fallback)
    cpu_id = _run_command("wmic cpu get processorid")
    if len(cpu_id.split('\n')) >= 2:
        cpu_id = cpu_id.split('\n')[1].strip()
    else:
        cpu_id = "GENERIC_CPU"
    
    # Kombinə et (UUID əsasdır, digərləri duz kimi)
    # UUID boşdursa və ya genericdirsə, digərlərinə güvənirik
    source_data = f"{uuid}|{vol_serial}|{cpu_id}"
    
    # SHA-256 hash
    hash_bytes = hashlib.sha256(source_data.encode('utf-8')).hexdigest()
    
    # İlk 16 simvol, böyük hərf
    raw_id = hash_bytes[:16].upper()
    
    # Format: XXXX-XXXX-XXXX-XXXX
    formatted_id = f"{raw_id[0:4]}-{raw_id[4:8]}-{raw_id[8:12]}-{raw_id[12:16]}"
    
    return formatted_id


def generate_license_key(machine_id: str, salt: str = _SECRET_SALT) -> str:
    """
    Machine ID üçün lisenziya açarı yaradır.
    
    Args:
        machine_id: Maşın ID-si (XXXX-XXXX-XXXX-XXXX formatında)
        salt: Gizli salt (default: internal salt)
        
    Returns:
        Lisenziya açarı (20 simvol, Base32)
    """
    # Machine ID + Salt
    raw_string = f"{machine_id}{salt}"
    
    # SHA-256 hash
    hash_bytes = hashlib.sha256(raw_string.encode('utf-8')).digest()
    
    # Base32 encode
    b32_encoded = base64.b32encode(hash_bytes).decode('utf-8')
    
    # İlk 20 simvol
    license_key = b32_encoded[:20]
    
    return license_key


def validate_license_key(input_key: str, machine_id: Optional[str] = None) -> bool:
    """
    Daxil edilən lisenziya açarını yoxlayır.
    
    Args:
        input_key: İstifadəçinin daxil etdiyi açar
        machine_id: Maşın ID (None olarsa avtomatik əldə edilir)
        
    Returns:
        Açar düzgündürmü
    """
    if machine_id is None:
        machine_id = get_machine_id()
    
    expected_key = generate_license_key(machine_id)
    
    # Case-insensitive müqayisə
    return input_key.upper().strip() == expected_key.upper()


def get_license_file_path() -> str:
    """Lisenziya faylının tam yolunu qaytarır."""
    # Tətbiq qovluğunda
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(app_dir, _LICENSE_FILE)


def save_license(license_key: str) -> bool:
    """
    Lisenziya açarını fayla saxlayır.
    
    Args:
        license_key: Saxlanılacaq açar
        
    Returns:
        Uğurlu olub-olmadığı
    """
    try:
        license_path = get_license_file_path()
        
        with open(license_path, 'w', encoding='utf-8') as f:
            f.write(license_key.strip())
        
        # Windows-da faylı gizli et
        if platform.system() == "Windows":
            try:
                subprocess.run(
                    f'attrib +h "{license_path}"',
                    shell=True,
                    capture_output=True
                )
            except:
                pass
        
        return True
        
    except Exception:
        return False


def load_license() -> Optional[str]:
    """
    Saxlanılmış lisenziya açarını oxuyur.
    
    Returns:
        Açar və ya None
    """
    try:
        license_path = get_license_file_path()
        
        if not os.path.exists(license_path):
            return None
        
        with open(license_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
        
    except Exception:
        return None


def check_license() -> Tuple[bool, str]:
    """
    Sistemin lisenziyalı olub-olmadığını yoxlayır.
    
    Returns:
        (is_valid, message) tuple
    """
    machine_id = get_machine_id()
    saved_key = load_license()
    
    if saved_key is None:
        return False, f"No license found. Machine ID: {machine_id}"
    
    if validate_license_key(saved_key, machine_id):
        return True, "License valid"
    else:
        return False, f"Invalid license. Machine ID: {machine_id}"


def activate_license(input_key: str) -> Tuple[bool, str]:
    """
    Lisenziya açarı ilə aktivasiya edir.
    
    Args:
        input_key: İstifadəçinin daxil etdiyi açar
        
    Returns:
        (success, message) tuple
    """
    machine_id = get_machine_id()
    
    if validate_license_key(input_key, machine_id):
        if save_license(input_key):
            return True, "License activated successfully!"
        else:
            return False, "Failed to save license file."
    else:
        return False, f"Invalid license key for this machine.\nMachine ID: {machine_id}"


def delete_license() -> bool:
    """Lisenziya faylını silir (debug/test üçün)."""
    try:
        license_path = get_license_file_path()
        if os.path.exists(license_path):
            os.remove(license_path)
        return True
    except:
        return False


# =====================================================================
# Test / Debug
# =====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("FacePro License Manager - Debug Mode")
    print("=" * 50)
    
    # Machine ID
    machine_id = get_machine_id()
    print(f"\nMachine ID: {machine_id}")
    
    # Generate key for this machine
    license_key = generate_license_key(machine_id)
    print(f"License Key: {license_key}")
    
    # Validate
    is_valid = validate_license_key(license_key, machine_id)
    print(f"Validation: {'VALID' if is_valid else 'INVALID'}")
    
    # Check saved license
    is_licensed, msg = check_license()
    print(f"\nSaved License: {'YES' if is_licensed else 'NO'}")
    print(f"Message: {msg}")

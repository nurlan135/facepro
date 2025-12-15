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


def _run_wmic_command(command: str) -> str:
    """
    Windows wmic komandasını işlədir.
    
    Args:
        command: wmic komandası
        
    Returns:
        Çıxış mətni (təmizlənmiş)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        # İlk sətir başlıqdır, ikinci sətir dəyərdir
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            return lines[1].strip()
        return ""
    except Exception:
        return ""


def _get_cpu_id() -> str:
    """CPU Processor ID-ni əldə edir (Windows)."""
    if platform.system() == "Windows":
        return _run_wmic_command("wmic cpu get processorid")
    else:
        # Linux/Mac üçün alternativ
        try:
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()[:16]
        except:
            return "UNKNOWN_CPU"


def _get_motherboard_id() -> str:
    """Motherboard Serial Number-ı əldə edir (Windows)."""
    if platform.system() == "Windows":
        return _run_wmic_command("wmic baseboard get serialnumber")
    else:
        # Linux/Mac üçün alternativ
        try:
            result = subprocess.run(
                ['sudo', 'dmidecode', '-s', 'baseboard-serial-number'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except:
            return "UNKNOWN_MB"


def get_machine_id() -> str:
    """
    Maşın ID-sini yaradır.
    
    Format: XXXX-XXXX-XXXX-XXXX (16 char, uppercase)
    
    Returns:
        Formatlanmış Machine ID
    """
    # Hardware məlumatlarını yığ
    cpu_id = _get_cpu_id()
    mb_id = _get_motherboard_id()
    
    # Kombinə et
    source_data = f"{cpu_id}{mb_id}"
    
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

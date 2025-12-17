#!/usr/bin/env python3
"""
FacePro Admin Key Generator
===========================
Bu skript YalnÄ±z admin/developer tÉ™rÉ™findÉ™n istifadÉ™ olunmalÄ±dÄ±r!
MüştÉ™rilÉ™rÉ™ paylaÅŸmayÄ±n!

İstifadə:
    python admin_keygen.py XXXX-XXXX-XXXX-XXXX
    python admin_keygen.py  (interactive mode)
"""

import sys
import hashlib
import base64
import re

import os

# =====================================================================
# SECRET SALT - Loaded from environment variable for security
# SECURITY: Salt is NOT hardcoded to prevent unauthorized key generation!
#
# Before running this script, set the environment variable:
#   Windows: set FACEPRO_LICENSE_SALT=your_secret_salt_here
#   Linux:   export FACEPRO_LICENSE_SALT=your_secret_salt_here
# =====================================================================
def get_license_salt() -> str:
    """Get license salt from environment variable."""
    salt = os.environ.get('FACEPRO_LICENSE_SALT')
    if not salt:
        print("\n[ERROR] FACEPRO_LICENSE_SALT environment variable is not set!")
        print("Set it before running this script:")
        print("  Windows: set FACEPRO_LICENSE_SALT=your_secret_salt_here")
        print("  Linux:   export FACEPRO_LICENSE_SALT=your_secret_salt_here")
        sys.exit(1)
    return salt


def validate_machine_id_format(machine_id: str) -> bool:
    """Machine ID formatının düzgünlüyünü yoxlayır."""
    pattern = r'^[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$'
    return bool(re.match(pattern, machine_id.upper()))


def generate_license_key(machine_id: str) -> str:
    """
    Machine ID üçün lisenziya açarı yaradır.
    
    Args:
        machine_id: Maşın ID-si (XXXX-XXXX-XXXX-XXXX formatında)
        
    Returns:
        Lisenziya açarı (20 simvol, Base32)
    """
    # Machine ID + Salt (salt from environment variable)
    raw_string = f"{machine_id.upper()}{get_license_salt()}"
    
    # SHA-256 hash
    hash_bytes = hashlib.sha256(raw_string.encode('utf-8')).digest()
    
    # Base32 encode
    b32_encoded = base64.b32encode(hash_bytes).decode('utf-8')
    
    # İlk 20 simvol
    license_key = b32_encoded[:20]
    
    return license_key


def main():
    print("=" * 60)
    print("  FacePro License Key Generator (ADMIN ONLY)")
    print("=" * 60)
    print()
    
    # Command line argument yoxla
    if len(sys.argv) > 1:
        machine_id = sys.argv[1].upper().strip()
    else:
        # Interactive mode
        print("Enter the Machine ID from the client's screen.")
        print("Format: XXXX-XXXX-XXXX-XXXX")
        print()
        machine_id = input("Machine ID: ").upper().strip()
    
    # Format yoxlaması
    if not validate_machine_id_format(machine_id):
        print()
        print("[ERROR] Invalid Machine ID format!")
        print("Expected format: XXXX-XXXX-XXXX-XXXX (hexadecimal)")
        print(f"Received: {machine_id}")
        sys.exit(1)
    
    # Açar yarat
    license_key = generate_license_key(machine_id)
    
    print()
    print("-" * 60)
    print(f"  Machine ID:   {machine_id}")
    print(f"  License Key:  {license_key}")
    print("-" * 60)
    print()
    print("Send this License Key to the client.")
    print("They should enter it in the activation dialog.")
    print()


if __name__ == "__main__":
    main()

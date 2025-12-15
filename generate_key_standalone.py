
import hashlib
import base64
import os

def generate_license_key(machine_id, salt="FaceGuard_v1_$uper$ecure_2025!"):
    # Machine ID + Salt
    raw_string = f"{machine_id}{salt}"
    
    # SHA-256 hash
    hash_bytes = hashlib.sha256(raw_string.encode('utf-8')).digest()
    
    # Base32 encode
    b32_encoded = base64.b32encode(hash_bytes).decode('utf-8')
    
    # First 20 chars
    license_key = b32_encoded[:20]
    return license_key

machine_id = "5ACD-9202-043D-BEA5"
key = generate_license_key(machine_id)
print(f"Machine ID: {machine_id}")
print(f"License Key: {key}")

# Save to .license file
license_file = ".license"
with open(license_file, "w", encoding="utf-8") as f:
    f.write(key)
print(f"Saved to {os.path.abspath(license_file)}")

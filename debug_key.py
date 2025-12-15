
import sys
import os

# Ensure we can import from src
sys.path.insert(0, os.getcwd())

try:
    from src.utils.license_manager import generate_license_key, validate_license_key, _SECRET_SALT
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

mid = "5ACD-9202-043D-BEA5"
print(f"DEBUGGING LICENSE KEY")
print(f"Machine ID: '{mid}'")
print(f"Salt: '{_SECRET_SALT}'")

expected = generate_license_key(mid)
print(f"Generated Key: '{expected}'")

input_key = "Y2SLZD7OIULI2HOJHOXJ"
print(f"Input Key:     '{input_key}'")

is_match = input_key == expected
print(f"Direct Match: {is_match}")

is_valid = validate_license_key(input_key, mid)
print(f"Validate Function: {is_valid}")

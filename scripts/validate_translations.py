#!/usr/bin/env python
"""
Translation Validation Script
Validates that all translation files have the same keys as the reference (en.json).
"""

import os
import json
import sys


def load_json(path: str) -> dict:
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_keys(data: dict, prefix: str = '') -> set:
    """Recursively get all keys from nested dict"""
    keys = set()
    for key, value in data.items():
        if key.startswith('$'):
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys(value, full_key))
        else:
            keys.add(full_key)
    return keys


def validate_translations():
    """Main validation function"""
    # Find locales directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    locales_dir = os.path.join(script_dir, '..', 'locales')
    
    if not os.path.exists(locales_dir):
        print(f"Error: locales directory not found at {locales_dir}")
        sys.exit(1)
    
    # Load English as reference
    en_path = os.path.join(locales_dir, 'en.json')
    if not os.path.exists(en_path):
        print("Error: en.json not found")
        sys.exit(1)
    
    en_data = load_json(en_path)
    en_keys = get_all_keys(en_data)
    
    print(f"Reference (en.json): {len(en_keys)} keys")
    print("=" * 50)
    
    errors = []
    warnings = []
    
    for filename in sorted(os.listdir(locales_dir)):
        if not filename.endswith('.json'):
            continue
        if filename.startswith('_') or filename == 'en.json':
            continue
        
        lang_code = filename.replace('.json', '')
        lang_path = os.path.join(locales_dir, filename)
        
        try:
            lang_data = load_json(lang_path)
        except json.JSONDecodeError as e:
            errors.append(f"{filename}: Invalid JSON - {e}")
            continue
        
        lang_keys = get_all_keys(lang_data)
        
        # Missing keys
        missing = en_keys - lang_keys
        if missing:
            errors.append(f"\n{filename} - Missing {len(missing)} keys:")
            for key in sorted(missing):
                errors.append(f"  - {key}")
        
        # Extra keys (might be intentional)
        extra = lang_keys - en_keys
        if extra:
            warnings.append(f"\n{filename} - Extra {len(extra)} keys (review):")
            for key in sorted(extra):
                warnings.append(f"  + {key}")
        
        # Success message if no issues
        if not missing and not extra:
            print(f"[OK] {filename}: {len(lang_keys)} keys - Complete!")
        elif not missing:
            print(f"[!] {filename}: {len(lang_keys)} keys - Has extra keys")
        else:
            print(f"[X] {filename}: Missing {len(missing)} keys")
    
    # Print warnings
    if warnings:
        print("\n" + "=" * 50)
        print("WARNINGS (Extra keys - review if intentional)")
        print("=" * 50)
        for warning in warnings:
            print(warning)
    
    # Print errors and exit
    if errors:
        print("\n" + "=" * 50)
        print("VALIDATION FAILED")
        print("=" * 50)
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("\n" + "=" * 50)
        print("[OK] All translations are complete!")
        print("=" * 50)
        sys.exit(0)


if __name__ == '__main__':
    validate_translations()

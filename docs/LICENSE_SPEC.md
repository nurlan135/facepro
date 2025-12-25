# License & Security Specification (Offline Hardware Lock)

**Last Updated:** 2025-12-23

## 1. Overview
The application is protected against unauthorized distribution using a **Cryptographic Hardware Lock** system. Since the system often runs offline (no internet), we cannot use a cloud license server.

## 2. Architecture

### 2.1. Components
| Component | File | Purpose |
|-----------|------|---------|
| License Manager | `src/utils/license_manager.py` | Core validation & activation logic |
| License Dialog | `src/ui/license_dialog.py` | GUI activation interface |
| Admin Keygen | `admin_keygen.py` | Generate keys for customers (ADMIN ONLY) |
| License File | `.license` | Stores the activated license key |

### 2.2. Security Model
- **No hardcoded secrets** - Salt is loaded from secure sources
- **Environment-based** - Production salt via environment variable
- **Fallback chain** - Multiple secure fallback locations

## 3. Logic Flow

### 3.1. Application Startup
```
main.py
   │
   ├─► check_license()
   │       │
   │       ├─► Valid? → Continue to Login
   │       │
   │       └─► Invalid? → Show LicenseActivationDialog
   │                           │
   │                           ├─► User enters key
   │                           ├─► activate_license(key)
   │                           └─► Save to .license file
   │
   └─► Login → MainWindow
```

### 3.2. Key Generation (Admin Side)
```python
# Run: python admin_keygen.py XXXX-XXXX-XXXX-XXXX
# Requires: FACEPRO_LICENSE_SALT environment variable
```

## 4. Technical Implementation

### 4.1. Generating Machine ID (The Lock)
**Source Data:** Combination of unique hardware identifiers:
- System UUID (`wmic csproduct get uuid`)
- Volume Serial (`vol c:`)
- CPU Processor ID (fallback)

**Algorithm:**
```python
source_data = f"{uuid}|{vol_serial}|{cpu_id}"
hash_bytes = SHA-256(source_data)
machine_id = hash_bytes[:16].upper()  # Format: XXXX-XXXX-XXXX-XXXX
```

### 4.2. Salt Configuration (CRITICAL)
The license salt is loaded in priority order:

1. **Environment Variable** (Recommended for production):
   ```bash
   # Windows
   setx FACEPRO_LICENSE_SALT "your_secret_salt_here"
   
   # Linux/Mac
   export FACEPRO_LICENSE_SALT="your_secret_salt_here"
   ```

2. **Secure File** (Alternative):
   ```
   ~/.facepro/license_salt       # Primary location
   ~/.facepro_license_salt       # Legacy fallback
   ```

3. **Development Fallback** (WARNING: Only for dev!):
   - `__FACEPRO_DEV_SALT_2025__`
   - Real production keys will NOT work with this salt!

### 4.3. Generating Activation Key (The Key)
**Algorithm:**
```python
raw_string = f"{machine_id}{salt}"
hash_bytes = SHA-256(raw_string)
license_key = Base32_Encode(hash_bytes)[:20]
```

### 4.4. Validation Process
1. App reads saved key from `.license` file
2. Calculates expected key using current Machine ID + Salt
3. Compares (normalized, case-insensitive)
4. Returns `(is_valid, message)` tuple

## 5. Admin Key Generation

### 5.1. Setup (One-time)
```bash
# Set the production salt (keep this SECRET!)
setx FACEPRO_LICENSE_SALT "YourSuperSecretProductionSalt2025!"
```

### 5.2. Generate Key for Customer
```bash
# Customer provides their Machine ID from the activation dialog
python admin_keygen.py 5ACD-9202-043D-BEA5

# Output:
# Machine ID:   5ACD-9202-043D-BEA5
# License Key:  XXXX-XXXX-XXXX-XXXX-XXXX
```

## 6. Anti-Tamper Measures

| Attack Vector | Protection |
|--------------|------------|
| **Hardware Change** | Machine ID changes → Hash changes → License invalid |
| **File Copy** | .license file is hardware-bound |
| **Salt Discovery** | Not in source code, loaded from environment |
| **Key Sharing** | Each key is unique to hardware |

## 7. Troubleshooting

### "License check failed"
1. Verify Machine ID matches the one used for key generation
2. Check if salt is configured: `echo %FACEPRO_LICENSE_SALT%`
3. Ensure `.license` file exists and contains valid key

### "LICENSE SALT NOT CONFIGURED"
This warning means the system is using development fallback. For production:
```bash
setx FACEPRO_LICENSE_SALT "your_production_salt"
```

## 8. File Locations

| File | Location | Purpose |
|------|----------|---------|
| `.license` | Project root | Activated license key |
| `license_salt` | `~/.facepro/` | Production salt (optional) |

## 9. Security Best Practices

- ✅ Never commit salt to version control
- ✅ Use environment variables in production
- ✅ Keep `admin_keygen.py` secure (don't distribute!)
- ✅ Rotate salt periodically for new versions
- ❌ Never hardcode salt in source code
- ❌ Never share admin keygen with customers
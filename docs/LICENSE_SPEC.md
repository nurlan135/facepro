# License & Security Specification (Offline Hardware Lock)

## 1. Overview
The application must be protected against unauthorized distribution. Since the system often runs offline (no internet), we cannot use a cloud license server. We will use a **Cryptographic Hardware Lock**.

## 2. Logic Flow
1.  **Fingerprinting (Client Side):** The app generates a unique `Machine ID` based on the user's specific hardware.
2.  **Key Generation (Admin Side):** The Admin uses a private script (`keygen.py`) to generate an `Activation Key` based on that Machine ID.
3.  **Validation (Client Side):** The app mathematically verifies if the entered Key matches the Machine ID.

## 3. Technical Implementation

### 3.1. Generating Machine ID (The Lock)
* **Source Data:** Concatenate `CPU Processor ID` + `Motherboard Serial Number`.
    * *Windows:* Use `wmic cpu get processorid` and `wmic baseboard get serialnumber`.
    * *Linux:* Read `/etc/machine-id` or use `dmidecode`.
* **Hashing:** `SHA-256(Source Data)`.
* **Formatting:** Take the first 16 characters and format as: `XXXX-XXXX-XXXX-XXXX` (Uppercase).
* **UI Behavior:** On startup, if no valid license found, show a dialog:
    * *"System Locked. Your Machine ID is: [ID]. Contact Support."*

### 3.2. Generating Activation Key (The Key)
* **Secret Salt:** Define a hardcoded, complex string in the source code (obfuscated if possible).
    * *Example:* `SALT = "FaceGuard_v1_$uper$ecure_2025!"`
* **Algorithm:**
    1.  `Raw_String = Machine_ID + SALT`
    2.  `Hash_Bytes = SHA-256(Raw_String)`
    3.  `Key = Base32_Encode(Hash_Bytes)[:20]` (Taking first 20 chars).
* **Output:** The License Key given to the user.

### 3.3. Validation Process
* When user inputs the Key:
    1.  App calculates `Expected_Key` using the same logic (Machine ID + SALT).
    2.  If `Input_Key == Expected_Key`:
        * Create a hidden file `.license` containing the key.
        * **Success:** Load Main Dashboard.
    3.  If `Input_Key != Expected_Key`:
        * **Error:** Show "Invalid Key".

## 4. Anti-Tamper Measures
* **Hardware Change:** If the user copies the folder to another PC, the Hardware ID changes -> The Hash changes -> The `.license` file becomes invalid -> App locks.
* **Time Bomb (Optional):** The key logic can include an expiry date in the hash string for "Trial Versions", but for MVP we stick to Lifetime.
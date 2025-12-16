# Design Document: User Login System

## Overview

FacePro tətbiqi üçün istifadəçi autentifikasiya və avtorizasiya sistemi. Bu sistem proqrama giriş nəzarətini təmin edəcək, Admin və Operator rollarını dəstəkləyəcək, və sessiya idarəetməsini həyata keçirəcək.

Sistem mövcud hardware lisenziya sistemindən sonra işləyəcək - əvvəlcə lisenziya yoxlanılır, sonra istifadəçi girişi tələb olunur.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Startup                      │
├─────────────────────────────────────────────────────────────┤
│  1. License Check (existing) → 2. Login System (new)        │
│                                      │                       │
│                              ┌───────┴───────┐               │
│                              │               │               │
│                         First Run?      Has Accounts?        │
│                              │               │               │
│                         Setup Wizard    Login Dialog         │
│                              │               │               │
│                              └───────┬───────┘               │
│                                      │                       │
│                              Main Dashboard                  │
│                         (Role-based UI filtering)            │
└─────────────────────────────────────────────────────────────┘
```

### Threading Model
- Login/Setup dialogs run on Main Thread (UI)
- Session timeout timer runs on Main Thread
- Database operations are synchronous (SQLite is fast enough)

## Components and Interfaces

### 1. AuthManager (src/utils/auth_manager.py)
Core authentication logic - singleton pattern.

```python
class AuthManager:
    _instance = None
    
    def __init__(self):
        self.current_user: Optional[UserAccount] = None
        self.session_start: Optional[datetime] = None
        self.failed_attempts: Dict[str, int] = {}
        self.lockout_until: Dict[str, datetime] = {}
    
    # Authentication
    def authenticate(username: str, password: str) -> Tuple[bool, str]
    def logout() -> None
    def is_logged_in() -> bool
    def get_current_user() -> Optional[UserAccount]
    
    # Account Management (Admin only)
    def create_account(username: str, password: str, role: str) -> Tuple[bool, str]
    def update_account(user_id: int, password: str = None, role: str = None) -> bool
    def delete_account(user_id: int) -> Tuple[bool, str]
    def list_accounts() -> List[UserAccount]
    
    # Password
    def change_password(user_id: int, old_pass: str, new_pass: str) -> Tuple[bool, str]
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]
    def verify_password(password: str, hash: str, salt: str) -> bool
    
    # Session
    def check_session_timeout() -> bool
    def reset_activity_timer() -> None
```

### 2. UserAccount (Data Model)
```python
@dataclass
class UserAccount:
    id: int
    username: str
    password_hash: str
    salt: str
    role: str  # 'admin' or 'operator'
    created_at: datetime
    is_locked: bool = False
    lock_until: Optional[datetime] = None
```

### 3. UI Components

#### LoginDialog (src/ui/login_dialog.py)
- Username/Password fields
- Login button
- Error message display
- "Locked" state indicator

#### SetupWizardDialog (src/ui/setup_wizard.py)
- First-time admin account creation
- Username/Password/Confirm fields
- Validation feedback

#### UserManagementDialog (src/ui/user_management.py)
- User list table
- Add/Edit/Delete buttons
- Role selector (Admin/Operator)

#### ChangePasswordDialog (src/ui/change_password.py)
- Current password field
- New password + Confirm fields

## Data Models

### Database Schema (app_users table)
```sql
CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    is_locked INTEGER DEFAULT 0,
    lock_until TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Note:** Table named `app_users` to avoid conflict with existing `users` table (face recognition subjects).

### Session Data (In-Memory)
```python
class SessionData:
    user_id: int
    username: str
    role: str
    login_time: datetime
    last_activity: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Input Validation
*For any* username string with length < 3 characters OR password string with length < 6 characters, the account creation SHALL be rejected with appropriate error message.
**Validates: Requirements 1.2**

### Property 2: Password Storage Security
*For any* password stored in the database, the stored value SHALL be a SHA-256 hash with unique salt, and verifying the original password against the stored hash SHALL return true.
**Validates: Requirements 1.3, 8.1, 8.2, 8.3**

### Property 3: Authentication Correctness
*For any* username/password pair, authentication SHALL succeed if and only if the password hash matches the stored hash for that username.
**Validates: Requirements 2.2, 2.3**

### Property 4: Account Lockout
*For any* user account with 3 consecutive failed login attempts, the account SHALL be locked and subsequent login attempts SHALL be rejected until lockout period expires.
**Validates: Requirements 2.4**

### Property 5: Admin User List Completeness
*For any* database state, when an Admin_User requests the user list, the returned list SHALL contain exactly all accounts in the app_users table.
**Validates: Requirements 3.1**

### Property 6: Last Admin Protection
*For any* database state with exactly one Admin_User, attempting to delete that admin SHALL fail and return an error.
**Validates: Requirements 3.5**

### Property 7: Operator Access Restriction
*For any* Operator_User session, access to settings, user management, and face enrollment SHALL be denied.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 8: Password Change Verification
*For any* password change request, the operation SHALL succeed if and only if the provided current password matches the stored password.
**Validates: Requirements 5.2, 5.3**

### Property 9: Session Timeout
*For any* active session with no user interaction for the configured timeout period, the session SHALL be terminated and user returned to login screen.
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 10: Logout Cleanup
*For any* logout operation (manual or auto), the session SHALL be cleared, camera streams stopped, and cached user data removed from memory.
**Validates: Requirements 7.1, 7.2, 7.3**

## Error Handling

### Authentication Errors
- Invalid credentials → Show generic "Invalid username or password" (security)
- Account locked → Show "Account locked. Try again in X minutes"
- Database error → Log error, show "System error. Please restart."

### Account Management Errors
- Duplicate username → "Username already exists"
- Delete last admin → "Cannot delete the last administrator"
- Invalid role → "Invalid role specified"

### Session Errors
- Session expired → Auto-redirect to login
- Concurrent login → Allow (no restriction for MVP)

## Testing Strategy

### Unit Testing
- Password hashing/verification functions
- Input validation functions
- Role permission checks

### Property-Based Testing
**Library:** `hypothesis` (Python PBT library)
**Minimum iterations:** 100 per property

Each property test will be tagged with:
```python
# **Feature: user-login, Property {N}: {property_text}**
```

**Property Tests to Implement:**
1. Input validation rejects short usernames/passwords
2. Password hash round-trip (hash then verify)
3. Authentication correctness (valid creds succeed, invalid fail)
4. Lockout after 3 failures
5. Admin list completeness
6. Last admin protection
7. Operator restriction enforcement
8. Password change requires correct current password
9. Session timeout triggers logout
10. Logout clears all session data

### Integration Testing
- Full login flow (dialog → auth → dashboard)
- Role-based UI filtering
- Session timeout with camera cleanup

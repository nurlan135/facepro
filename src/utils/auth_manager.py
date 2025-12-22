"""
FacePro Authentication Manager Module
User authentication and session management system.

Based on user-login spec:
- Password hashing with SHA-256 + random salt
- Singleton pattern for global access
- Account lockout after failed attempts
- Session management with timeout
- Signal emission for logout/camera cleanup
"""

import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

import bcrypt
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.database.repositories.app_user_repository import AppUserRepository
from src.utils.audit_logger import get_audit_logger


@dataclass
class UserAccount:
    """User account data model."""
    id: int
    username: str
    password_hash: str
    salt: str
    role: str  # 'admin' or 'operator'
    created_at: datetime
    is_locked: bool = False
    lock_until: Optional[datetime] = None
    failed_attempts: int = 0


@dataclass
class SessionData:
    """Active session data model."""
    user_id: int
    username: str
    role: str
    login_time: datetime
    last_activity: datetime


class AuthManager(QObject):
    """
    Authentication manager - singleton pattern.
    Handles user authentication, account management, and session tracking.
    
    Signals:
        logout_requested: Emitted when logout occurs (manual or auto)
                         Used to trigger camera cleanup and UI updates
        session_timeout: Emitted when session times out due to inactivity
    """
    _instance = None
    
    # Signals for logout and session events
    logout_requested = pyqtSignal()  # Emitted on logout for camera cleanup
    session_timeout = pyqtSignal()   # Emitted when session times out
    
    # Constants
    MAX_FAILED_ATTEMPTS = 3
    LOCKOUT_DURATION_MINUTES = 5
    DEFAULT_SESSION_TIMEOUT_MINUTES = 30
    MIN_USERNAME_LENGTH = 3
    MIN_PASSWORD_LENGTH = 6
    
    def __init__(self, parent=None):
        """Initialize AuthManager (use get_instance() instead)."""
        super().__init__(parent)
        self._current_session: Optional[SessionData] = None
        self._session_timeout_minutes = self.DEFAULT_SESSION_TIMEOUT_MINUTES
        self._repo = AppUserRepository()
        # Thread safety for session operations
        from threading import RLock
        self._session_lock = RLock()
    
    @classmethod
    def get_instance(cls) -> 'AuthManager':
        """Get singleton instance of AuthManager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None
    
    # =========================================================================
    # Password Hashing
    # =========================================================================
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash password with bcrypt.
        """
        password_bytes = password.encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
        return password_hash.decode('utf-8'), 'bcrypt'
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verify password against stored hash.
        """
        try:
            if stored_salt == 'bcrypt':
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            else:
                salt_bytes = bytes.fromhex(stored_salt)
                salted_password = password.encode('utf-8') + salt_bytes
                computed_hash = hashlib.sha256(salted_password).hexdigest()
                return computed_hash == stored_hash
        except Exception:
            return False

    # =========================================================================
    # Account Management
    # =========================================================================
    
    def create_account(self, username: str, password: str, role: str = 'operator') -> Tuple[bool, str]:
        """Create a new user account."""
        if len(username) < self.MIN_USERNAME_LENGTH:
            return False, f"Username must be at least {self.MIN_USERNAME_LENGTH} characters"
        
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        if role not in ('admin', 'operator'):
            return False, "Invalid role. Must be 'admin' or 'operator'"
        
        password_hash, salt = self.hash_password(password)
        
        try:
            if self._repo.get_user_by_username(username):
                return False, "Username already exists"
            
            if self._repo.create_user(username, password_hash, salt, role):
                get_audit_logger().log("USER_CREATED", {"username": username, "role": role})
                return True, "Account created successfully"
            return False, "Failed to create account"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def list_accounts(self) -> List[UserAccount]:
        """Get list of all user accounts."""
        accounts = []
        try:
            rows = self._repo.get_all_users()
            for row in rows:
                lock_until = None
                if row['lock_until']:
                    lock_until = datetime.fromisoformat(row['lock_until'])
                
                created_at = datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
                
                account = UserAccount(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    salt=row['salt'],
                    role=row['role'],
                    is_locked=bool(row['is_locked']),
                    lock_until=lock_until,
                    failed_attempts=row['failed_attempts'],
                    created_at=created_at
                )
                accounts.append(account)
        except Exception:
            pass
        return accounts
    
    def update_account(self, user_id: int, password: Optional[str] = None, 
                       role: Optional[str] = None) -> Tuple[bool, str]:
        """Update user account."""
        if password is None and role is None:
            return False, "No changes specified"
        
        if role is not None and role not in ('admin', 'operator'):
            return False, "Invalid role. Must be 'admin' or 'operator'"
        
        if password is not None and len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        try:
            if not self._repo.get_user_by_id(user_id):
                return False, "User not found"
            
            updates = {}
            if password is not None:
                ph, salt = self.hash_password(password)
                updates['password_hash'] = ph
                updates['salt'] = salt
            
            if role is not None:
                updates['role'] = role
                
            if self._repo.update_user(user_id, updates):
                return True, "Account updated successfully"
            return False, "Update failed"
            
        except Exception as e:
            return False, "An error occurred while updating the account"
    
    def delete_account(self, user_id: int) -> Tuple[bool, str]:
        """Delete user account."""
        try:
            user = self._repo.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            if user['role'] == 'admin':
                if self._repo.get_admin_count() <= 1:
                    return False, "Cannot delete the last administrator"
            
            if self._repo.delete_user(user_id):
                get_audit_logger().log("USER_DELETED", {"user_id": user_id, "username": user['username']})
                return True, "Account deleted successfully"
            return False, "Delete failed"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def has_accounts(self) -> bool:
        """Check if any user accounts exist."""
        try:
            return len(self._repo.get_all_users()) > 0
        except Exception:
            return False

    # =========================================================================
    # Authentication
    # =========================================================================
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user with username and password."""
        try:
            user = self._repo.get_user_by_username(username)
            if not user:
                return False, "Invalid username or password"
            
            # Check lockout
            if user['is_locked'] and user['lock_until']:
                lock_until = datetime.fromisoformat(user['lock_until'])
                if datetime.now() < lock_until:
                    remaining = (lock_until - datetime.now()).seconds // 60 + 1
                    return False, f"Account locked. Try again in {remaining} minutes"
                else:
                    self._repo.update_user(user['id'], {
                        'is_locked': 0, 'lock_until': None, 'failed_attempts': 0
                    })
            
            # Verify password
            if self.verify_password(password, user['password_hash'], user['salt']):
                self._repo.update_user(user['id'], {
                    'failed_attempts': 0, 'is_locked': 0, 'lock_until': None
                })
                
                self._current_session = SessionData(
                    user_id=user['id'],
                    username=user['username'],
                    role=user['role'],
                    login_time=datetime.now(),
                    last_activity=datetime.now()
                )
                get_audit_logger().log("LOGIN", {"username": username}, user_id=user['id'])
                return True, "Login successful"
            else:
                new_attempts = user['failed_attempts'] + 1
                if new_attempts >= self.MAX_FAILED_ATTEMPTS:
                    lock_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                    self._repo.update_user(user['id'], {
                        'failed_attempts': new_attempts,
                        'is_locked': 1,
                        'lock_until': lock_until.isoformat()
                    })
                    return False, f"Account locked for {self.LOCKOUT_DURATION_MINUTES} minutes"
                else:
                    self._repo.update_user(user['id'], {'failed_attempts': new_attempts})
                    remaining = self.MAX_FAILED_ATTEMPTS - new_attempts
                    return False, f"Invalid username or password. {remaining} attempts remaining"
                    
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def logout(self) -> None:
        """
        End current session and clear session data.
        
        Emits logout_requested signal for camera cleanup.
        Requirements: 7.1, 7.2, 7.3
        """
        if self._current_session is not None:
            # Log the action
            get_audit_logger().log("LOGOUT", {"username": self._current_session.username}, user_id=self._current_session.user_id)
            
            # Clear session data
            self._current_session = None
            
            # Emit signal for camera cleanup and UI updates
            self.logout_requested.emit()
    
    def is_logged_in(self) -> bool:
        """Check if user is currently logged in."""
        return self._current_session is not None
    
    def get_current_user(self) -> Optional[SessionData]:
        """Get current logged-in user session data."""
        return self._current_session
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def check_session_timeout(self) -> bool:
        """
        Check if session has timed out.
        
        Returns:
            True if session is still valid, False if timed out
            
        Emits session_timeout signal if session has expired.
        Requirements: 6.1, 6.2, 6.3
        """
        if self._current_session is None:
            return False
        
        elapsed = datetime.now() - self._current_session.last_activity
        if elapsed.total_seconds() > (self._session_timeout_minutes * 60):
            # Emit timeout signal before logout
            self.session_timeout.emit()
            self.logout()
            return False
        
        return True
    
    def reset_activity_timer(self) -> None:
        """Reset the last activity timestamp."""
        if self._current_session:
            self._current_session.last_activity = datetime.now()
    
    def set_session_timeout(self, minutes: int) -> None:
        """Set session timeout duration in minutes."""
        if 5 <= minutes <= 120:
            self._session_timeout_minutes = minutes
    
    def get_session_timeout(self) -> int:
        """Get current session timeout in minutes."""
        return self._session_timeout_minutes
    
    # =========================================================================
    # Password Change
    # =========================================================================
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password."""
        if len(new_password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        try:
            user = self._repo.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            if not self.verify_password(old_password, user['password_hash'], user['salt']):
                return False, "Current password is incorrect"
            
            new_hash, new_salt = self.hash_password(new_password)
            if self._repo.update_user(user_id, {'password_hash': new_hash, 'salt': new_salt}):
                return True, "Password changed successfully"
            return False, "Change failed"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # =========================================================================
    # Role-Based Access Control
    # =========================================================================
    
    def can_access_settings(self) -> bool:
        """Check if current user can access settings."""
        if not self._current_session:
            return False
        return self._current_session.role == 'admin'
    
    def can_manage_users(self) -> bool:
        """Check if current user can manage other users."""
        if not self._current_session:
            return False
        return self._current_session.role == 'admin'
    
    def can_enroll_faces(self) -> bool:
        """Check if current user can enroll faces."""
        if not self._current_session:
            return False
        return self._current_session.role == 'admin'


# =========================================================================
# Module-level convenience functions
# =========================================================================

def get_auth_manager() -> AuthManager:
    """Get the singleton AuthManager instance."""
    return AuthManager.get_instance()

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
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal


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
        self._db_path = self._get_db_path()
    
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
    
    def _get_db_path(self) -> str:
        """Get database file path."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, 'data', 'db', 'faceguard.db')
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # =========================================================================
    # Password Hashing
    # =========================================================================
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash password with SHA-256 and salt.
        
        Args:
            password: Plain text password
            salt: Optional salt bytes (generated if not provided)
            
        Returns:
            Tuple of (password_hash, salt) as hex strings
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Combine password and salt, then hash
        salted_password = password.encode('utf-8') + salt
        password_hash = hashlib.sha256(salted_password).hexdigest()
        
        return password_hash, salt.hex()
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored password hash (hex string)
            stored_salt: Stored salt (hex string)
            
        Returns:
            True if password matches, False otherwise
        """
        salt_bytes = bytes.fromhex(stored_salt)
        computed_hash, _ = self.hash_password(password, salt_bytes)
        return computed_hash == stored_hash

    # =========================================================================
    # Account Management
    # =========================================================================
    
    def create_account(self, username: str, password: str, role: str = 'operator') -> Tuple[bool, str]:
        """
        Create a new user account.
        
        Args:
            username: Username (min 3 characters)
            password: Password (min 6 characters)
            role: User role ('admin' or 'operator')
            
        Returns:
            Tuple of (success, message)
        """
        # Validate username
        if len(username) < self.MIN_USERNAME_LENGTH:
            return False, f"Username must be at least {self.MIN_USERNAME_LENGTH} characters"
        
        # Validate password
        if len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        # Validate role
        if role not in ('admin', 'operator'):
            return False, "Invalid role. Must be 'admin' or 'operator'"
        
        # Hash password
        password_hash, salt = self.hash_password(password)
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check for duplicate username
            cursor.execute("SELECT id FROM app_users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"
            
            # Insert new user
            cursor.execute('''
                INSERT INTO app_users (username, password_hash, salt, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, salt, role))
            
            conn.commit()
            conn.close()
            return True, "Account created successfully"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def list_accounts(self) -> List[UserAccount]:
        """
        Get list of all user accounts.
        
        Returns:
            List of UserAccount objects
        """
        accounts = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, salt, role, is_locked, 
                       lock_until, failed_attempts, created_at
                FROM app_users
                ORDER BY created_at
            ''')
            
            for row in cursor.fetchall():
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
            
            conn.close()
        except Exception:
            pass
        
        return accounts
    
    def update_account(self, user_id: int, password: Optional[str] = None, 
                       role: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update user account.
        
        Args:
            user_id: User ID to update
            password: New password (optional)
            role: New role (optional)
            
        Returns:
            Tuple of (success, message)
        """
        if password is None and role is None:
            return False, "No changes specified"
        
        if role is not None and role not in ('admin', 'operator'):
            return False, "Invalid role. Must be 'admin' or 'operator'"
        
        if password is not None and len(password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM app_users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                conn.close()
                return False, "User not found"
            
            # Build update query
            updates = []
            params = []
            
            if password is not None:
                password_hash, salt = self.hash_password(password)
                updates.append("password_hash = ?")
                updates.append("salt = ?")
                params.extend([password_hash, salt])
            
            if role is not None:
                updates.append("role = ?")
                params.append(role)
            
            params.append(user_id)
            
            cursor.execute(f'''
                UPDATE app_users SET {", ".join(updates)} WHERE id = ?
            ''', params)
            
            conn.commit()
            conn.close()
            return True, "Account updated successfully"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_account(self, user_id: int) -> Tuple[bool, str]:
        """
        Delete user account.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if user exists and get their role
            cursor.execute("SELECT role FROM app_users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "User not found"
            
            # Check if this is the last admin
            if user['role'] == 'admin':
                cursor.execute("SELECT COUNT(*) as count FROM app_users WHERE role = 'admin'")
                admin_count = cursor.fetchone()['count']
                
                if admin_count <= 1:
                    conn.close()
                    return False, "Cannot delete the last administrator"
            
            # Delete user
            cursor.execute("DELETE FROM app_users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True, "Account deleted successfully"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def has_accounts(self) -> bool:
        """Check if any user accounts exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM app_users")
            count = cursor.fetchone()['count']
            conn.close()
            return count > 0
        except Exception:
            return False

    # =========================================================================
    # Authentication
    # =========================================================================
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user with username and password.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user
            cursor.execute('''
                SELECT id, username, password_hash, salt, role, is_locked, 
                       lock_until, failed_attempts
                FROM app_users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return False, "Invalid username or password"
            
            # Check if account is locked
            if user['is_locked'] and user['lock_until']:
                lock_until = datetime.fromisoformat(user['lock_until'])
                if datetime.now() < lock_until:
                    remaining = (lock_until - datetime.now()).seconds // 60 + 1
                    conn.close()
                    return False, f"Account locked. Try again in {remaining} minutes"
                else:
                    # Unlock account (lockout expired)
                    cursor.execute('''
                        UPDATE app_users SET is_locked = 0, lock_until = NULL, failed_attempts = 0
                        WHERE id = ?
                    ''', (user['id'],))
                    conn.commit()
            
            # Verify password
            if self.verify_password(password, user['password_hash'], user['salt']):
                # Reset failed attempts on success
                cursor.execute('''
                    UPDATE app_users SET failed_attempts = 0, is_locked = 0, lock_until = NULL
                    WHERE id = ?
                ''', (user['id'],))
                conn.commit()
                
                # Create session
                self._current_session = SessionData(
                    user_id=user['id'],
                    username=user['username'],
                    role=user['role'],
                    login_time=datetime.now(),
                    last_activity=datetime.now()
                )
                
                conn.close()
                return True, "Login successful"
            else:
                # Increment failed attempts
                new_attempts = user['failed_attempts'] + 1
                
                if new_attempts >= self.MAX_FAILED_ATTEMPTS:
                    # Lock account
                    lock_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                    cursor.execute('''
                        UPDATE app_users SET failed_attempts = ?, is_locked = 1, lock_until = ?
                        WHERE id = ?
                    ''', (new_attempts, lock_until.isoformat(), user['id']))
                    conn.commit()
                    conn.close()
                    return False, f"Account locked for {self.LOCKOUT_DURATION_MINUTES} minutes"
                else:
                    cursor.execute('''
                        UPDATE app_users SET failed_attempts = ? WHERE id = ?
                    ''', (new_attempts, user['id']))
                    conn.commit()
                    conn.close()
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
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password for verification
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        if len(new_password) < self.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute('''
                SELECT password_hash, salt FROM app_users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if not user:
                conn.close()
                return False, "User not found"
            
            # Verify old password
            if not self.verify_password(old_password, user['password_hash'], user['salt']):
                conn.close()
                return False, "Current password is incorrect"
            
            # Hash new password
            new_hash, new_salt = self.hash_password(new_password)
            
            # Update password
            cursor.execute('''
                UPDATE app_users SET password_hash = ?, salt = ? WHERE id = ?
            ''', (new_hash, new_salt, user_id))
            
            conn.commit()
            conn.close()
            return True, "Password changed successfully"
            
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

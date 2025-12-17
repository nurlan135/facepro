"""
FacePro AuthManager Tests
Tests for user authentication and account management functionality.

These tests verify the core implementation of tasks 1-3 from the user-login spec.
"""

import pytest
import os
import sys
import sqlite3
import tempfile
import shutil
from datetime import datetime, timedelta
import importlib.util

# Direct import of auth_manager module to avoid PyQt6 dependency from utils/__init__.py
def import_auth_manager():
    """Import auth_manager directly without going through utils package."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(project_root, 'src', 'utils', 'auth_manager.py')
    spec = importlib.util.spec_from_file_location("auth_manager", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

auth_module = import_auth_manager()
AuthManager = auth_module.AuthManager
UserAccount = auth_module.UserAccount
SessionData = auth_module.SessionData


class TestAuthManagerSetup:
    """Test fixture setup for AuthManager tests."""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        """Create a temporary database for testing."""
        # Reset singleton
        AuthManager.reset_instance()
        
        # Create temp db directory
        self.test_db_dir = tmp_path / "data" / "db"
        self.test_db_dir.mkdir(parents=True)
        self.test_db_path = self.test_db_dir / "faceguard.db"
        
        # Create database with schema
        conn = sqlite3.connect(str(self.test_db_path))
        cursor = conn.cursor()
        cursor.execute('''
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
            )
        ''')
        conn.commit()
        conn.close()
        
        # Get AuthManager instance and override db path
        self.auth = AuthManager.get_instance()
        self.auth._db_path = str(self.test_db_path)
        
        yield
        
        # Cleanup
        AuthManager.reset_instance()


class TestPasswordHashing(TestAuthManagerSetup):
    """Tests for password hashing functionality (Task 1.2) - now using bcrypt."""
    
    def test_hash_password_returns_hash_and_salt(self):
        """Test that hash_password returns both hash and salt placeholder."""
        password = "testpassword123"
        hash_result, salt = self.auth.hash_password(password)
        
        assert hash_result is not None
        assert salt is not None
        # bcrypt hash starts with $2b$ and is ~60 chars
        assert hash_result.startswith('$2b$')
        assert len(hash_result) == 60
        # Salt is now a placeholder for bcrypt
        assert salt == 'bcrypt'
    
    def test_hash_password_different_salts_produce_different_hashes(self):
        """Test that same password produces different hashes (bcrypt auto-generates salt)."""
        password = "testpassword123"
        hash1, salt1 = self.auth.hash_password(password)
        hash2, salt2 = self.auth.hash_password(password)
        
        # With bcrypt, each hash is unique even for same password
        assert hash1 != hash2
        # Salt placeholder is same
        assert salt1 == salt2 == 'bcrypt'
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hash_result, salt = self.auth.hash_password(password)
        
        assert self.auth.verify_password(password, hash_result, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        hash_result, salt = self.auth.hash_password(password)
        
        assert self.auth.verify_password("wrongpassword", hash_result, salt) is False
    
    def test_hash_password_with_provided_salt(self):
        """Test that bcrypt ignores provided salt (it generates its own)."""
        password = "testpassword123"
        hash1, salt1 = self.auth.hash_password(password)
        
        # bcrypt ignores provided salt, always generates new
        import secrets
        provided_salt = secrets.token_bytes(32)
        hash2, salt2 = self.auth.hash_password(password, provided_salt)
        
        # Hashes should be different (bcrypt generates unique salt each time)
        assert hash1 != hash2
        # Salt placeholder should be same
        assert salt1 == salt2 == 'bcrypt'


class TestAccountCreation(TestAuthManagerSetup):
    """Tests for account creation functionality (Task 2.1)."""
    
    def test_create_account_success(self):
        """Test successful account creation."""
        success, message = self.auth.create_account("testuser", "password123", "admin")
        
        assert success is True
        assert "successfully" in message.lower()
    
    def test_create_account_short_username(self):
        """Test account creation with short username fails."""
        success, message = self.auth.create_account("ab", "password123", "admin")
        
        assert success is False
        assert "3 characters" in message
    
    def test_create_account_short_password(self):
        """Test account creation with short password fails."""
        success, message = self.auth.create_account("testuser", "12345", "admin")
        
        assert success is False
        assert "6 characters" in message
    
    def test_create_account_invalid_role(self):
        """Test account creation with invalid role fails."""
        success, message = self.auth.create_account("testuser", "password123", "superuser")
        
        assert success is False
        assert "Invalid role" in message
    
    def test_create_account_duplicate_username(self):
        """Test account creation with duplicate username fails."""
        self.auth.create_account("testuser", "password123", "admin")
        success, message = self.auth.create_account("testuser", "password456", "operator")
        
        assert success is False
        assert "already exists" in message


class TestAccountListing(TestAuthManagerSetup):
    """Tests for account listing functionality (Task 2.3)."""
    
    def test_list_accounts_empty(self):
        """Test listing accounts when none exist."""
        accounts = self.auth.list_accounts()
        assert len(accounts) == 0
    
    def test_list_accounts_returns_all(self):
        """Test that list_accounts returns all created accounts."""
        self.auth.create_account("user1", "password123", "admin")
        self.auth.create_account("user2", "password123", "operator")
        self.auth.create_account("user3", "password123", "operator")
        
        accounts = self.auth.list_accounts()
        
        assert len(accounts) == 3
        usernames = [a.username for a in accounts]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames


class TestAccountUpdate(TestAuthManagerSetup):
    """Tests for account update functionality (Task 2.5)."""
    
    def test_update_account_password(self):
        """Test updating account password."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        
        success, message = self.auth.update_account(user_id, password="newpassword123")
        
        assert success is True
        
        # Verify new password works
        auth_success, _ = self.auth.authenticate("testuser", "newpassword123")
        assert auth_success is True
    
    def test_update_account_role(self):
        """Test updating account role."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        
        success, message = self.auth.update_account(user_id, role="operator")
        
        assert success is True
        
        # Verify role changed
        accounts = self.auth.list_accounts()
        assert accounts[0].role == "operator"
    
    def test_update_account_not_found(self):
        """Test updating non-existent account fails."""
        success, message = self.auth.update_account(9999, password="newpassword")
        
        assert success is False
        assert "not found" in message.lower()


class TestAccountDeletion(TestAuthManagerSetup):
    """Tests for account deletion functionality (Task 2.6)."""
    
    def test_delete_account_success(self):
        """Test successful account deletion."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.create_account("user1", "password123", "operator")
        
        accounts = self.auth.list_accounts()
        operator_id = next(a.id for a in accounts if a.role == "operator")
        
        success, message = self.auth.delete_account(operator_id)
        
        assert success is True
        assert len(self.auth.list_accounts()) == 1
    
    def test_delete_last_admin_fails(self):
        """Test that deleting the last admin fails."""
        self.auth.create_account("admin1", "password123", "admin")
        
        accounts = self.auth.list_accounts()
        admin_id = accounts[0].id
        
        success, message = self.auth.delete_account(admin_id)
        
        assert success is False
        assert "last administrator" in message.lower()
    
    def test_delete_admin_when_multiple_admins_exist(self):
        """Test that deleting an admin succeeds when other admins exist."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.create_account("admin2", "password123", "admin")
        
        accounts = self.auth.list_accounts()
        first_admin_id = accounts[0].id
        
        success, message = self.auth.delete_account(first_admin_id)
        
        assert success is True
        assert len(self.auth.list_accounts()) == 1


class TestAuthentication(TestAuthManagerSetup):
    """Tests for authentication functionality (Task 3.1)."""
    
    def test_authenticate_success(self):
        """Test successful authentication."""
        self.auth.create_account("testuser", "password123", "admin")
        
        success, message = self.auth.authenticate("testuser", "password123")
        
        assert success is True
        assert self.auth.is_logged_in() is True
    
    def test_authenticate_wrong_password(self):
        """Test authentication with wrong password fails."""
        self.auth.create_account("testuser", "password123", "admin")
        
        success, message = self.auth.authenticate("testuser", "wrongpassword")
        
        assert success is False
        assert self.auth.is_logged_in() is False
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user fails."""
        success, message = self.auth.authenticate("nonexistent", "password123")
        
        assert success is False
        assert "Invalid" in message


class TestAccountLockout(TestAuthManagerSetup):
    """Tests for account lockout functionality (Task 3.3)."""
    
    def test_account_locks_after_max_failures(self):
        """Test that account locks after 3 failed attempts."""
        self.auth.create_account("testuser", "password123", "admin")
        
        # Fail 3 times
        for i in range(3):
            success, message = self.auth.authenticate("testuser", "wrongpassword")
        
        # Should be locked now
        assert "locked" in message.lower()
        
        # Even correct password should fail
        success, message = self.auth.authenticate("testuser", "password123")
        assert success is False
        assert "locked" in message.lower()
    
    def test_failed_attempts_reset_on_success(self):
        """Test that failed attempts reset after successful login."""
        self.auth.create_account("testuser", "password123", "admin")
        
        # Fail twice
        self.auth.authenticate("testuser", "wrongpassword")
        self.auth.authenticate("testuser", "wrongpassword")
        
        # Succeed
        success, _ = self.auth.authenticate("testuser", "password123")
        assert success is True
        
        # Fail twice more - should not lock
        self.auth.logout()
        self.auth.authenticate("testuser", "wrongpassword")
        success, message = self.auth.authenticate("testuser", "wrongpassword")
        
        assert "locked" not in message.lower()


class TestSessionManagement(TestAuthManagerSetup):
    """Tests for session management functionality."""
    
    def test_logout_clears_session(self):
        """Test that logout clears the session."""
        self.auth.create_account("testuser", "password123", "admin")
        self.auth.authenticate("testuser", "password123")
        
        assert self.auth.is_logged_in() is True
        
        self.auth.logout()
        
        assert self.auth.is_logged_in() is False
        assert self.auth.get_current_user() is None
    
    def test_get_current_user_returns_session_data(self):
        """Test that get_current_user returns correct session data."""
        self.auth.create_account("testuser", "password123", "admin")
        self.auth.authenticate("testuser", "password123")
        
        session = self.auth.get_current_user()
        
        assert session is not None
        assert session.username == "testuser"
        assert session.role == "admin"
    
    def test_logout_emits_signal(self):
        """Test that logout emits logout_requested signal."""
        self.auth.create_account("testuser", "password123", "admin")
        self.auth.authenticate("testuser", "password123")
        
        # Track signal emission
        signal_received = []
        self.auth.logout_requested.connect(lambda: signal_received.append(True))
        
        self.auth.logout()
        
        assert len(signal_received) == 1
    
    def test_logout_no_signal_when_not_logged_in(self):
        """Test that logout does not emit signal when not logged in."""
        # Track signal emission
        signal_received = []
        self.auth.logout_requested.connect(lambda: signal_received.append(True))
        
        self.auth.logout()
        
        assert len(signal_received) == 0
    
    def test_session_timeout_check_valid_session(self):
        """Test session timeout check with valid session."""
        self.auth.create_account("testuser", "password123", "admin")
        self.auth.authenticate("testuser", "password123")
        
        # Session should be valid immediately after login
        assert self.auth.check_session_timeout() is True
    
    def test_session_timeout_check_no_session(self):
        """Test session timeout check with no session."""
        assert self.auth.check_session_timeout() is False
    
    def test_reset_activity_timer(self):
        """Test that reset_activity_timer updates last_activity."""
        self.auth.create_account("testuser", "password123", "admin")
        self.auth.authenticate("testuser", "password123")
        
        original_activity = self.auth.get_current_user().last_activity
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.1)
        
        self.auth.reset_activity_timer()
        
        new_activity = self.auth.get_current_user().last_activity
        assert new_activity > original_activity
    
    def test_set_session_timeout(self):
        """Test setting session timeout."""
        self.auth.set_session_timeout(60)
        assert self.auth.get_session_timeout() == 60
    
    def test_set_session_timeout_bounds(self):
        """Test session timeout bounds (5-120 minutes)."""
        # Below minimum - should not change
        self.auth.set_session_timeout(30)  # Set valid first
        self.auth.set_session_timeout(3)
        assert self.auth.get_session_timeout() == 30
        
        # Above maximum - should not change
        self.auth.set_session_timeout(150)
        assert self.auth.get_session_timeout() == 30
        
        # Valid values
        self.auth.set_session_timeout(5)
        assert self.auth.get_session_timeout() == 5
        
        self.auth.set_session_timeout(120)
        assert self.auth.get_session_timeout() == 120


class TestPasswordChange(TestAuthManagerSetup):
    """Tests for password change functionality (Task 6.1)."""
    
    def test_change_password_success(self):
        """Test successful password change."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        
        success, message = self.auth.change_password(user_id, "password123", "newpassword456")
        
        assert success is True
        assert "successfully" in message.lower()
        
        # Verify new password works
        self.auth.logout()
        auth_success, _ = self.auth.authenticate("testuser", "newpassword456")
        assert auth_success is True
    
    def test_change_password_wrong_current_password(self):
        """Test password change fails with wrong current password."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        
        success, message = self.auth.change_password(user_id, "wrongpassword", "newpassword456")
        
        assert success is False
        assert "incorrect" in message.lower()
        
        # Verify old password still works
        auth_success, _ = self.auth.authenticate("testuser", "password123")
        assert auth_success is True
    
    def test_change_password_short_new_password(self):
        """Test password change fails with short new password."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        
        success, message = self.auth.change_password(user_id, "password123", "12345")
        
        assert success is False
        assert "6 characters" in message
    
    def test_change_password_user_not_found(self):
        """Test password change fails for non-existent user."""
        success, message = self.auth.change_password(9999, "oldpass", "newpass123")
        
        assert success is False
        assert "not found" in message.lower()
    
    def test_change_password_updates_hash_and_salt(self):
        """Test that password change updates the hash (salt placeholder stays same with bcrypt)."""
        self.auth.create_account("testuser", "password123", "admin")
        accounts = self.auth.list_accounts()
        user_id = accounts[0].id
        old_hash = accounts[0].password_hash
        old_salt = accounts[0].salt
        
        self.auth.change_password(user_id, "password123", "newpassword456")
        
        # Get updated account
        accounts = self.auth.list_accounts()
        new_hash = accounts[0].password_hash
        new_salt = accounts[0].salt
        
        # Hash should be different
        assert new_hash != old_hash
        # Salt is placeholder 'bcrypt' for new accounts
        assert new_salt == 'bcrypt'


class TestRoleBasedAccessControl(TestAuthManagerSetup):
    """Tests for role-based access control functionality (Task 7.1)."""
    
    def test_admin_can_access_settings(self):
        """Test that admin user can access settings."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.authenticate("admin1", "password123")
        
        assert self.auth.can_access_settings() is True
    
    def test_operator_cannot_access_settings(self):
        """Test that operator user cannot access settings."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.create_account("operator1", "password123", "operator")
        self.auth.authenticate("operator1", "password123")
        
        assert self.auth.can_access_settings() is False
    
    def test_admin_can_manage_users(self):
        """Test that admin user can manage users."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.authenticate("admin1", "password123")
        
        assert self.auth.can_manage_users() is True
    
    def test_operator_cannot_manage_users(self):
        """Test that operator user cannot manage users."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.create_account("operator1", "password123", "operator")
        self.auth.authenticate("operator1", "password123")
        
        assert self.auth.can_manage_users() is False
    
    def test_admin_can_enroll_faces(self):
        """Test that admin user can enroll faces."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.authenticate("admin1", "password123")
        
        assert self.auth.can_enroll_faces() is True
    
    def test_operator_cannot_enroll_faces(self):
        """Test that operator user cannot enroll faces."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.create_account("operator1", "password123", "operator")
        self.auth.authenticate("operator1", "password123")
        
        assert self.auth.can_enroll_faces() is False
    
    def test_no_session_denies_all_permissions(self):
        """Test that all permissions are denied when not logged in."""
        assert self.auth.can_access_settings() is False
        assert self.auth.can_manage_users() is False
        assert self.auth.can_enroll_faces() is False
    
    def test_permissions_after_logout(self):
        """Test that permissions are denied after logout."""
        self.auth.create_account("admin1", "password123", "admin")
        self.auth.authenticate("admin1", "password123")
        
        # Verify admin has permissions
        assert self.auth.can_access_settings() is True
        
        # Logout
        self.auth.logout()
        
        # Verify permissions are denied
        assert self.auth.can_access_settings() is False
        assert self.auth.can_manage_users() is False
        assert self.auth.can_enroll_faces() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Implementation Plan

- [x] 1. Database schema and AuthManager core





  - [x] 1.1 Create app_users table schema in database


    - Add migration to `data/db/init_db.py` for `app_users` table
    - Include: id, username, password_hash, salt, role, is_locked, lock_until, failed_attempts, created_at
    - _Requirements: 8.1, 8.2_

  - [x] 1.2 Implement AuthManager class (src/utils/auth_manager.py)

    - Singleton pattern with `get_instance()` method
    - Password hashing with SHA-256 + random salt
    - Password verification function
    - _Requirements: 1.3, 8.1, 8.2, 8.3_
  - [ ]* 1.3 Write property test for password storage round-trip
    - **Property 2: Password Storage Security**
    - **Validates: Requirements 1.3, 8.1, 8.2, 8.3**

- [x] 2. Account management functions




  - [x] 2.1 Implement create_account function

    - Username validation (min 3 chars)
    - Password validation (min 6 chars)
    - Duplicate username check
    - _Requirements: 1.2, 3.2_
  - [ ]* 2.2 Write property test for input validation
    - **Property 1: Input Validation**
    - **Validates: Requirements 1.2**
  - [x] 2.3 Implement list_accounts function

    - Return all accounts from app_users table
    - _Requirements: 3.1_
  - [ ]* 2.4 Write property test for admin list completeness
    - **Property 5: Admin User List Completeness**
    - **Validates: Requirements 3.1**
  - [x] 2.5 Implement update_account function

    - Allow password and role changes
    - _Requirements: 3.3_
  - [x] 2.6 Implement delete_account function

    - Prevent deletion of last admin
    - _Requirements: 3.4, 3.5_
  - [ ]* 2.7 Write property test for last admin protection
    - **Property 6: Last Admin Protection**
    - **Validates: Requirements 3.5**

- [x] 3. Authentication logic





  - [x] 3.1 Implement authenticate function


    - Verify username exists
    - Verify password hash matches
    - Check account lock status
    - Track failed attempts
    - _Requirements: 2.2, 2.3, 2.4_
  - [ ]* 3.2 Write property test for authentication correctness
    - **Property 3: Authentication Correctness**
    - **Validates: Requirements 2.2, 2.3**
  - [x] 3.3 Implement account lockout mechanism


    - Lock after 3 consecutive failures
    - 5 minute lockout duration
    - _Requirements: 2.4_
  - [ ]* 3.4 Write property test for account lockout
    - **Property 4: Account Lockout**
    - **Validates: Requirements 2.4**

- [x] 4. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Session management





  - [x] 5.1 Implement session tracking


    - Store current user, login time, last activity
    - _Requirements: 6.1_
  - [x] 5.2 Implement session timeout check


    - Configurable timeout (default 30 min)
    - _Requirements: 6.1, 6.4_
  - [x] 5.3 Implement logout function


    - Clear session data
    - Emit signal for camera cleanup
    - _Requirements: 7.1, 7.2, 7.3_
  - [ ]* 5.4 Write property test for logout cleanup
    - **Property 10: Logout Cleanup**
    - **Validates: Requirements 7.1, 7.2, 7.3**

- [x] 6. Password change functionality

  - [x] 6.1 Implement change_password function

    - Verify current password first
    - Update hash and salt in database
    - _Requirements: 5.2, 5.3_
  - [ ]* 6.2 Write property test for password change verification
    - **Property 8: Password Change Verification**
    - **Validates: Requirements 5.2, 5.3**

- [x] 7. Role-based access control






  - [x] 7.1 Implement permission checking functions

    - `can_access_settings()`, `can_manage_users()`, `can_enroll_faces()`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [ ]* 7.2 Write property test for operator restriction
    - **Property 7: Operator Access Restriction**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 8. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Login Dialog UI




  - [x] 9.1 Create LoginDialog class (src/ui/login_dialog.py)



    - Dark theme consistent with app
    - Username/Password fields
    - Login button with Enter key support
    - Error message display area
    - Account locked indicator
    - _Requirements: 2.1, 2.5_

- [x] 10. Setup Wizard UI








  - [x] 10.1 Create SetupWizardDialog class (src/ui/setup_wizard.py)


    - First-time admin account creation
    - Username, Password, Confirm Password fields
    - Validation feedback





    - _Requirements: 1.1, 1.2, 1.4_

- [x] 11. User Management UI





  - [x] 11.1 Create UserManagementDialog class (src/ui/user_management.py)


    - Table showing all users (username, role, created_at)
    - Add User button → opens add dialog
    - Edit button → opens edit dialog
    - Delete button with confirmation
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 12. Change Password UI






  - [x] 12.1 Create ChangePasswordDialog class (src/ui/change_password.py)

    - Current password field
    - New password + Confirm fields
    - Validation and success/error feedback
    - _Requirements: 5.1, 5.4_

- [x] 13. Integration with main application





  - [x] 13.1 Update main.py startup flow


    - After license check, check for accounts
    - If no accounts → show SetupWizard
    - If accounts exist → show LoginDialog
    - On success → show MainWindow
    - _Requirements: 1.1, 2.1_
  - [x] 13.2 Update MainWindow for role-based UI


    - Hide/disable settings menu for operators
    - Hide user management for operators
    - Hide face enrollment for operators
    - Add logout button to sidebar
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 7.1_
  - [x] 13.3 Implement session timeout in MainWindow



    - Timer to check inactivity
    - On timeout → stop cameras, show login
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ]* 13.4 Write property test for session timeout
    - **Property 9: Session Timeout**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 14. Final Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

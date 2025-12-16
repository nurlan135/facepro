# Requirements Document

## Introduction

FacePro tətbiqi üçün istifadəçi giriş (login) sistemi. Bu sistem proqrama giriş nəzarətini təmin edəcək, müxtəlif istifadəçi rollarını dəstəkləyəcək və təhlükəsizlik tələblərini qarşılayacaq. Mövcud hardware lisenziya sistemindən fərqli olaraq, bu sistem proqram daxilində çoxlu istifadəçi hesablarını idarə edəcək.

## Glossary

- **Login_System**: FacePro tətbiqində istifadəçi autentifikasiyası və sessiya idarəetməsini həyata keçirən modul
- **User_Account**: Sistemdə qeydiyyatdan keçmiş istifadəçi hesabı (username, password hash, role)
- **Admin_User**: Tam səlahiyyətli istifadəçi - bütün ayarlara və istifadəçi idarəetməsinə çıxışı var
- **Operator_User**: Məhdud səlahiyyətli istifadəçi - yalnız monitorinq və hadisələrə baxış
- **Session**: İstifadəçinin aktiv giriş sessiyası
- **Password_Hash**: Şifrənin SHA-256 ilə hash edilmiş forması
- **Auto_Logout**: Müəyyən müddət ərzində aktivlik olmadıqda avtomatik çıxış

## Requirements

### Requirement 1

**User Story:** As an administrator, I want to create the first admin account on fresh installation, so that I can secure the application from unauthorized access.

#### Acceptance Criteria

1. WHEN the Login_System detects no user accounts in database THEN the Login_System SHALL display a first-time setup wizard for creating an Admin_User account
2. WHEN creating the first Admin_User account THEN the Login_System SHALL require username (minimum 3 characters) and password (minimum 6 characters)
3. WHEN the first Admin_User account is created THEN the Login_System SHALL store the Password_Hash using SHA-256 algorithm with salt
4. WHEN the first-time setup completes THEN the Login_System SHALL redirect to the login screen

### Requirement 2

**User Story:** As a user, I want to log in with my credentials, so that I can access the application securely.

#### Acceptance Criteria

1. WHEN the application starts THEN the Login_System SHALL display a login dialog before showing the main dashboard
2. WHEN a user enters valid credentials THEN the Login_System SHALL create a Session and grant access to the main dashboard
3. WHEN a user enters invalid credentials THEN the Login_System SHALL display an error message and remain on the login screen
4. WHEN a user fails login 3 consecutive times THEN the Login_System SHALL lock the account for 5 minutes
5. WHEN the login dialog is displayed THEN the Login_System SHALL show the application logo and a dark-themed interface consistent with the main application

### Requirement 3

**User Story:** As an administrator, I want to manage user accounts, so that I can control who has access to the system.

#### Acceptance Criteria

1. WHEN an Admin_User accesses user management THEN the Login_System SHALL display a list of all User_Accounts with username, role, and creation date
2. WHEN an Admin_User creates a new User_Account THEN the Login_System SHALL allow setting username, password, and role (Admin or Operator)
3. WHEN an Admin_User edits a User_Account THEN the Login_System SHALL allow changing password and role
4. WHEN an Admin_User deletes a User_Account THEN the Login_System SHALL remove the account after confirmation
5. WHEN attempting to delete the last Admin_User THEN the Login_System SHALL prevent deletion and show a warning message

### Requirement 4

**User Story:** As an operator, I want to have limited access to the system, so that I can monitor cameras without changing critical settings.

#### Acceptance Criteria

1. WHEN an Operator_User logs in THEN the Login_System SHALL grant access to camera monitoring and event logs only
2. WHEN an Operator_User attempts to access settings THEN the Login_System SHALL hide or disable settings menu items
3. WHEN an Operator_User attempts to access user management THEN the Login_System SHALL deny access and show "Access Denied" message
4. WHEN an Operator_User attempts to enroll faces THEN the Login_System SHALL deny access to face enrollment features

### Requirement 5

**User Story:** As a user, I want to change my own password, so that I can maintain my account security.

#### Acceptance Criteria

1. WHEN a logged-in user accesses profile settings THEN the Login_System SHALL display a password change form
2. WHEN changing password THEN the Login_System SHALL require current password verification before accepting new password
3. WHEN the new password is set THEN the Login_System SHALL update the Password_Hash in database
4. WHEN password change succeeds THEN the Login_System SHALL display a success message

### Requirement 6

**User Story:** As a system administrator, I want automatic session timeout, so that unattended workstations are secured.

#### Acceptance Criteria

1. WHILE a Session is active AND no user interaction occurs for 30 minutes THEN the Login_System SHALL trigger Auto_Logout
2. WHEN Auto_Logout triggers THEN the Login_System SHALL return to the login screen and clear the Session
3. WHEN Auto_Logout triggers THEN the Login_System SHALL stop all camera streams to save resources
4. WHERE the timeout duration is configurable THEN the Login_System SHALL allow Admin_User to set timeout between 5-120 minutes

### Requirement 7

**User Story:** As a user, I want to manually log out, so that I can secure my session when leaving the workstation.

#### Acceptance Criteria

1. WHEN a user clicks the logout button THEN the Login_System SHALL end the current Session and return to login screen
2. WHEN logout occurs THEN the Login_System SHALL stop all active camera streams
3. WHEN logout occurs THEN the Login_System SHALL clear any cached user data from memory

### Requirement 8

**User Story:** As a developer, I want user credentials stored securely, so that the system is protected against data breaches.

#### Acceptance Criteria

1. WHEN storing a password THEN the Login_System SHALL use SHA-256 hashing with a unique salt per user
2. WHEN serializing user credentials THEN the Login_System SHALL store password hash and salt as separate fields
3. WHEN deserializing user credentials THEN the Login_System SHALL reconstruct the hash for comparison

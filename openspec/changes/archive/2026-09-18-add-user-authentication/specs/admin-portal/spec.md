## ADDED Requirements

### Requirement: Users view
The system SHALL provide, within the Admin Portal, a list view of all non-deleted users showing their email, admin flag, and assigned customers, and a detail view for each showing the same, editable.

#### Scenario: User browses the users list
- **WHEN** an admin opens the Users list view in the Admin Portal
- **THEN** the system shows every non-deleted user's email, admin flag, and assigned customer count

#### Scenario: Admin opens a user's detail view
- **WHEN** an admin opens a user's detail view in the Admin Portal
- **THEN** the system shows that user's email, admin flag, and the full list of customers assigned to them

### Requirement: Assign customers to a user from the Admin Portal
The system SHALL let an admin, from a user's detail view in the Admin Portal, set which customers are assigned to that user.

#### Scenario: Assigning customers
- **WHEN** an admin selects one or more customers for a user and saves
- **THEN** the system persists that user's assigned customers as exactly the selected set

### Requirement: Toggle admin status from the Admin Portal
The system SHALL let an admin, from a user's detail view, grant or revoke that user's admin flag.

#### Scenario: Granting admin from the Admin Portal
- **WHEN** an admin toggles another user's admin flag on and saves
- **THEN** the system persists that user as an admin

### Requirement: Reset a user's password from the Admin Portal
The system SHALL let an admin, from a user's detail view, set a new password for that user directly.

#### Scenario: Resetting a password from the Admin Portal
- **WHEN** an admin enters a new password for a user and saves
- **THEN** the system persists that password (hashed) for the user, and the user can log in with it immediately

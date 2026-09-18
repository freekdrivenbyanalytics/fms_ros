# user-auth Specification

## Purpose

Represents who is logged in and what they're allowed to see: a user account is either an admin (full access to every portal) or a customer user (access to zero or more specific customers' data in the Customer Portal only), authenticated via a session cookie shared across all four portal frontends.

## Requirements

### Requirement: User data model
The system SHALL persist each user with a unique identifier, a unique email address, a hashed password, an admin flag (defaulting to false), and a soft-delete flag.

#### Scenario: User is persisted with required fields
- **WHEN** a user is created with an email and a password
- **THEN** the system persists the user with that email, a hash of that password (never the plaintext), an admin flag of false, and the fields are retrievable unchanged

#### Scenario: Email is unique
- **WHEN** a user is created with an email address already used by another non-deleted user
- **THEN** the system rejects the request

### Requirement: Self-service sign-up
The system SHALL let anyone create a user account by supplying an email and a password, without any email verification step. A newly signed-up user SHALL NOT be an admin and SHALL have no customers assigned, and therefore SHALL see no data anywhere until an admin grants access.

#### Scenario: Signing up creates an account with no access
- **WHEN** a person signs up with an email and password
- **THEN** the system creates a non-admin user with no assigned customers, who can log in but sees no customer data until an admin assigns one or more customers or grants admin

#### Scenario: No verification email is required
- **WHEN** a person signs up
- **THEN** the system does not require confirming the email address before the account can log in

### Requirement: Log in and log out
The system SHALL let a user log in with their email and password, receiving a session (a cookie) that identifies them on subsequent requests, and log out, invalidating that session.

#### Scenario: Successful login
- **WHEN** a user submits a correct email and password
- **THEN** the system issues a session cookie identifying that user

#### Scenario: Failed login
- **WHEN** a user submits an email with no matching account, or an incorrect password
- **THEN** the system rejects the login without indicating which of the two was wrong

#### Scenario: Logging out ends the session
- **WHEN** a logged-in user logs out
- **THEN** the system invalidates their session cookie, and subsequent requests are treated as not logged in

### Requirement: A user's own identity is retrievable
The system SHALL provide an API for a logged-in user to retrieve their own id, email, admin flag, and assigned customer ids; an anonymous caller SHALL receive an indication that they are not logged in rather than an error.

#### Scenario: Logged-in user retrieves their own identity
- **WHEN** a logged-in user requests their own identity
- **THEN** the system returns their id, email, admin flag, and the ids of every customer assigned to them

#### Scenario: Anonymous caller is told they are not logged in
- **WHEN** a caller with no valid session requests the current identity
- **THEN** the system indicates no one is logged in, rather than returning an error

### Requirement: A user can be assigned zero or more customers
The system SHALL allow an admin to associate a user with zero or more customers. This assignment SHALL have no effect on an admin user, who already has access to every customer.

#### Scenario: Assigning customers to a user
- **WHEN** an admin sets a non-admin user's assigned customers to a given list
- **THEN** the system persists that exact list, replacing whatever was assigned before

#### Scenario: A user with multiple assigned customers
- **WHEN** a non-admin user has two or more customers assigned
- **THEN** that user's Customer Portal session has access to all of them

#### Scenario: Assigning customers to an admin has no effect
- **WHEN** an admin assigns customers to a user who is themselves an admin
- **THEN** the assignment is persisted but grants nothing beyond what their admin flag already grants

### Requirement: Admin-driven password reset
The system SHALL let an admin set a new password for any user directly, without the affected user taking any action or receiving an email. This is the only password-recovery mechanism in this change; a self-service "forgot password" email flow is explicitly deferred.

#### Scenario: Admin resets a user's password
- **WHEN** an admin sets a new password for a user
- **THEN** the user can subsequently log in with the new password, and the old password no longer works

### Requirement: Toggling admin status
The system SHALL let an admin grant or revoke another user's admin flag.

#### Scenario: Granting admin
- **WHEN** an admin sets another user's admin flag to true
- **THEN** that user immediately has unrestricted access to every portal on their next request

#### Scenario: Revoking admin
- **WHEN** an admin sets another user's admin flag to false
- **THEN** that user's access reverts to only their assigned customers (if any) in the Customer Portal, and they lose access to Planning, Admin Portal, and Employee Management

### Requirement: Planning, Admin Portal, and Employee Management require an admin session
The system SHALL require a logged-in admin session for every page and API call belonging to the Planning application, the Admin Portal, or Employee Management. A request with no session, or a non-admin session, SHALL be rejected (API) or redirected to the login page (frontend).

#### Scenario: Anonymous access is rejected
- **WHEN** a request with no session is made to Planning, the Admin Portal, or Employee Management
- **THEN** the system rejects the API request or redirects the page to login

#### Scenario: Non-admin access is rejected
- **WHEN** a logged-in non-admin user's session is used against Planning, the Admin Portal, or Employee Management
- **THEN** the system rejects the API request or redirects the page to login

#### Scenario: Admin access is allowed
- **WHEN** a logged-in admin's session is used against Planning, the Admin Portal, or Employee Management
- **THEN** the system allows the request

### Requirement: Customer Portal requires a session, scoped by role
The system SHALL require a logged-in session (admin or customer) for every page and API call belonging to the Customer Portal. An admin session SHALL see and be able to preview any customer, unrestricted. A customer session SHALL only ever see the customer(s) assigned to it, and SHALL have no way to view another customer's data.

#### Scenario: Anonymous access is rejected
- **WHEN** a request with no session is made to the Customer Portal
- **THEN** the system rejects the API request or redirects the page to login

#### Scenario: Admin sees everything, unrestricted
- **WHEN** an admin's session is used against the Customer Portal
- **THEN** the system behaves as it does today: every customer's data is visible, and the existing switcher can preview any of them

#### Scenario: Customer session is scoped to its assigned customers
- **WHEN** a customer user's session is used against the Customer Portal
- **THEN** the system only ever returns data for the customer(s) assigned to that user, regardless of what is requested

#### Scenario: A customer user cannot access another customer's data
- **WHEN** a customer user's session requests data for a customer not assigned to them
- **THEN** the system rejects the request

### Requirement: Initial admin account
The system SHALL be seedable with one initial admin account (`sfm_admin`) with a randomly generated password, reported once at seed time and not stored anywhere in the codebase, so an operator has a way to log in and grant access to everyone else.

#### Scenario: Seeding the initial admin
- **WHEN** the seed script runs against a database with no existing `sfm_admin` user
- **THEN** the system creates an admin user with that email and a freshly generated strong password, and prints that password once

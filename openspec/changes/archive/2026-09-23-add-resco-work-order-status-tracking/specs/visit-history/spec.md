# Spec Delta

## Purpose

Gives a planner a complete, unfiltered view of every service visit - including ones hidden from the assignment page's board once overdue and completed, and ones automatically unassigned because their past planned Work Orders are currently Scheduled - so nothing scheduled is ever actually lost from view, only decluttered from the active planning board.

## ADDED Requirements

### Requirement: View all visits regardless of status or date
The system SHALL provide a page, under the Planning portal, showing every service visit: unassigned, assigned, and ones excluded from the assignment page's assigned-visit list because they are overdue and completed. The page SHALL apply no date-range restriction by default.

#### Scenario: Planner opens the all-visits page
- **WHEN** a user opens the all-visits page
- **THEN** the page displays every service visit, including ones that are overdue and completed and therefore hidden from the assignment page's board

#### Scenario: An overdue, completed visit is shown
- **WHEN** a service visit's assignment is overdue and its Resco Work Order status is completed, so it does not appear on the assignment page's board
- **THEN** that visit is still shown on the all-visits page, with its Resco status visible

#### Scenario: A visit unassigned because it never took place is shown with that reason
- **WHEN** a service visit was automatically unassigned because it never took place
- **THEN** that visit is shown on the all-visits page with that reason visible, the same as it would be on the assignment page's unassigned visit list

### Requirement: All-visits page is read-only
The system SHALL NOT offer individual create, edit, assign or unassign controls on the all-visits page. It SHALL offer an admin-only bulk "Update status from Resco" action as an explicit exception: this refreshes statuses and reconciles eligible past Scheduled assignments, including attempting their Draft reset. The action SHALL explain these effects and refresh the displayed data afterwards.

#### Scenario: No edit affordance on the all-visits page
- **WHEN** a user views a visit on the all-visits page
- **THEN** the system provides no per-visit create, edit, assign or unassign action; only the clearly explained admin bulk status-sync/reconciliation action is available

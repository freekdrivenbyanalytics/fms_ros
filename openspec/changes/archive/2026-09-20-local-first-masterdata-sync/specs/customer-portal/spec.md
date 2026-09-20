# Spec Delta

## REMOVED Requirements

### Requirement: Refresh customers from Tripletex
**Reason**: this triggered a Tripletex-to-local pull sync, which no longer exists (fms_ros is the system of record for customers/customer locations, not Tripletex - see `local-first-masterdata-sync`'s proposal). The control was also available to any logged-in customer-portal user, not just admins; the endpoint it called now triggers real writes to the connected Tripletex/Resco account, which a non-admin user should not be able to do.
**Migration**: None - removed outright. The Customers, Customer Locations, and Contracts views already reflect fms_ros's own current data without needing a sync of any kind.

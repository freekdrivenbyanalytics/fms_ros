## REMOVED Requirements

### Requirement: Skill data model
**Reason**: Skills are replaced by Tripletex-sourced products; see the `products` capability.
**Migration**: None — this is a destructive migration. Existing skill assignments are not carried over to products, since the two are different data sources with no defined mapping between them.

### Requirement: Create, update, and soft-delete a skill
**Reason**: Products are read-only locally, sourced entirely from Tripletex; there is no local create/rename/delete for the replacement concept.
**Migration**: Use the `products` capability's on-demand Tripletex sync instead.

### Requirement: Deleted skills are hidden by default
**Reason**: Replaced by the equivalent "List products" requirement in the `products` capability.
**Migration**: See the `products` capability's "List products" requirement.

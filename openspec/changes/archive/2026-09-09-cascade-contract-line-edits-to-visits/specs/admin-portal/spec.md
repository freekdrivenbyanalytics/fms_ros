## ADDED Requirements

### Requirement: Mark a contract line as open-ended from the Admin Portal
The system SHALL let a user, on the Admin Portal's contract-line form, check a "No end date" box to indicate the line has no end date. Checking it SHALL grey out and disable the end-date field and display `31.12.2099` in it as a placeholder; unchecking it SHALL re-enable the field for a real date. The form SHALL submit `end_date: null` whenever the box is checked, regardless of what is displayed in the disabled field.

#### Scenario: Marking a line as open-ended
- **WHEN** a user checks the "No end date" box on the contract-line form
- **THEN** the end-date field becomes disabled, shows `31.12.2099`, and the form submits `end_date: null` on save

#### Scenario: Unmarking an open-ended line
- **WHEN** a user unchecks the "No end date" box
- **THEN** the end-date field becomes editable again and the form submits whatever real date the user enters

#### Scenario: An existing open-ended line shows the box checked
- **WHEN** a user opens the edit form for a contract line that has no end_date
- **THEN** the "No end date" box is shown checked and the end-date field shows `31.12.2099`, disabled

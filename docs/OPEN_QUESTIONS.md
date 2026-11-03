# Open questions

## Product decisions

- Which learner flows are essential for the first demo: online only, OMR, or both?
- Should “centre” and “class/batch” be separate first-class entities?
- Which answer types need manual grading in MVP?
- What is the intended policy for exam versioning after a link is shared?
- Are notices in-app only or also email/push?

## LAN/WAN decisions

- Minimum supported hardware, operating systems and local network topology?
- Must LAN run with zero internet access, or may it use periodic cloud sync?
- Which records can sync, and which workspace is authoritative for conflicts?
- Required backup destination, retention, restore time and recovery point objectives?
- Is local OIDC/LDAP needed for schools?

## Security and operations

- Required MFA, password recovery and session timeout policy?
- Who may export student data, reports and question files?
- Required audit retention and privacy/data residency obligations?
- What is the emergency restore and incident-contact process?
- What are the test-data and staging requirements before any real learner data?

## Research gaps

Attendance, certificates, dedicated question bank, proctoring workflow, student exam-taking flow, responsive behavior, keyboard accessibility, API/import schemas, rate limits and backup/sync behavior were not observed in the authorized session.

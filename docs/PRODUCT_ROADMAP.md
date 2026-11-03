# Product roadmap

## MVP — first usable vertical slice

1. Workspace setup with owner/admin roles.
2. Student and faculty directory with CSV import preview and tags.
3. Subjects and question bank with immutable question versions.
4. Online exam authoring, preview, schedule and scoped share link.
5. Student attempt capture, objective scoring and result review.
6. LAN single-node deployment and cloud container deployment using the same schema.
7. Audit log, encrypted backups, recovery throttling and basic reports.

The MVP exam journey should include draft → review → immutable publish → scoped assignment → attempt → server-authoritative scoring/result receipt.

## Phase 2

- Faculty/campus delegation, notices, batches/classes and centre hierarchy.
- OMR template workflow and scanner handoff.
- Manual grading, moderation, result release and saved report views.
- LAN/cloud synchronization with conflict review.
- OIDC/SAML, MFA policy, scheduled backups and operational dashboards.

## Future

- Consent-based proctoring, certificates, attendance, adaptive tests, SIS/BI connectors, mobile scan, multi-region cloud and federation.

## Quality gates

- Product brief and acceptance criteria approved before coding.
- One end-to-end exam journey works in LAN mode before feature expansion.
- The same journey works in cloud preview with a documented rollback.
- Security review covers tenant isolation, recovery, imports/exports, audit logs and backups.
- Browser screenshots cover desktop, tablet and mobile before demo freeze.

## Research gate before implementation

- Confirm minimum exam duration and exact expiry/auto-submit semantics.
- Define student credential provisioning without putting secrets in chat or logs.
- Define LAN authority during WAN loss, durable local submissions, idempotent synchronization and conflict review.

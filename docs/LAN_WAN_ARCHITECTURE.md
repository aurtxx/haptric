# LAN and WAN architecture for the independent platform

## Design goals

- Run fully on a school or coaching-center LAN with no internet dependency during an exam.
- Run the same product as a secure cloud/WAN service for distributed learners.
- Keep tenant, role, exam, attempt and audit boundaries identical across modes.
- Make synchronization explicit; never silently merge conflicting exam or identity changes.

## Recommended topology

| Concern | LAN deployment | WAN/cloud deployment |
|---|---|---|
| App | Single-node container bundle on an administrator-managed server | Stateless web/API containers behind TLS ingress |
| Database | Local PostgreSQL or SQLite only for a small pilot; PostgreSQL preferred | Managed PostgreSQL with point-in-time recovery |
| Files | Local encrypted volume for question media, imports and exports | Object storage with private buckets and signed, short-lived access |
| Identity | Local accounts, optional campus OIDC when reachable | OIDC/SAML plus local break-glass admin |
| Queue | In-process durable queue or local worker | Managed queue/worker with idempotent jobs |
| Backups | Scheduled encrypted local backup plus removable/offsite copy | Encrypted snapshots and object-version retention |
| Observability | Local structured audit log and health page | Central logs, metrics, tracing and alerting without secrets |
| Updates | Signed package/container updates during maintenance window | Rolling deployment with migration gates |

## Data boundaries

Core entities: Organization, Campus, User, RoleBinding, Student, Faculty, Subject, Topic, Question, QuestionVersion, Exam, ExamVersion, Schedule, ShareGrant, Attempt, Answer, Result, Notice, ImportJob, ExportJob, AuditEvent, SyncCursor and BackupManifest.

Content versions are immutable after an exam is published. Attempts reference an exact ExamVersion. Identity and permission changes are authoritative in the local workspace that owns them; cloud synchronization must use explicit ownership and conflict records.

## Synchronization model

- LAN is authoritative during an offline exam window.
- Sync uses an append-only event or change feed with stable IDs, schema versions, idempotency keys and per-entity revision numbers.
- Exam content and answer keys use “publish once, no automatic merge” semantics.
- Student profile edits can use field-level conflict review; attempt and result records are append-only.
- The UI must show sync state, last successful sync, queued items, conflicts and retry controls.

Suggested event envelope: `event_id`, `tenant_id`, `origin_node_id`, `origin_sequence`, `entity_type`, `entity_id`, `operation`, `base_version`, `entity_version`, `occurred_at`, `schema_version`, payload and checksum/signature. Deduplicate by event ID and origin sequence. Use compare-and-swap revisions for mutable drafts; never silently merge published exams, submissions, grading events or audit records.

Keep synchronization separate from database replication. A small authenticated pull/push service with bounded batches, cursors, idempotency keys and gap detection is easier to operate across intermittent LAN links. Large media files should use a storage adapter and content hashes rather than embedding binaries in event payloads.

## API and recovery boundaries

The same domain contract should support both modes: `/v1/auth/login`, `/v1/auth/recovery/request`, `/v1/auth/recovery/verify`, `/v1/auth/recovery/reset`, tenant-scoped membership and role endpoints, exam draft/publish endpoints, attempt append/submit endpoints, report queries, and `/v1/sync/pull` plus `/v1/sync/push`. Mutations should accept idempotency keys; mutable resources should require a revision or `If-Match` value.

Recovery must be server-side, generic for known and unknown identifiers, short-lived, single-use, account/session bound and rate-limited by account and source. Reissuing a code must not reset the failed-attempt budget. LAN mode cannot depend on email/SMS, so provide an administrator-assisted reset or pre-issued recovery method. Do not synchronize password hashes casually between nodes.

## Security and reliability

- Enforce tenant and role checks in the API and database, not only in the UI.
- Use short-lived sessions, secure cookies, CSRF protection, MFA-capable owner accounts, rate limits and generic recovery errors.
- Encrypt backups and object storage; keep secrets outside the repository.
- Audit imports, exports, publication, result release, role changes and backup restores.
- Provide health checks, migration rollback guidance, restore drills and an offline fallback procedure.

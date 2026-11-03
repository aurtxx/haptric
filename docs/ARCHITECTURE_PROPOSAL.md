# Architecture proposal for manager approval

Status: proposed; implementation owners must align with this contract before integration.

## Thin vertical slice

The first slice is one tenant with an owner/admin and a student:

1. Admin creates a draft exam with three typed questions.
2. Admin publishes an immutable exam version and assigns it to a student.
3. Student starts one attempt, receives a server-issued deadline, and saves answers.
4. The server accepts an idempotent submit or auto-submit at the deadline, scores objective items, and creates a result.
5. Student and admin read the same sanitized result/attempt receipt.

Secondary modules (faculty, OMR, notices, reporting, proctoring, AI) remain outside the first slice.

## Service boundaries

- `backend/`: Django + DRF domain API, authorization, scoring, audit and sync outbox.
- `frontend/`: React + TypeScript client with role-aware routes and an offline-aware attempt store.
- `infra/`: PostgreSQL Compose baseline and deployment-mode configuration.

The browser never decides tenant membership, score, deadline or submission acceptance. Those are server-side decisions.

## Core API contract (v1)

All paths are under `/api/v1` and require an authenticated tenant context except login/health.

| Method | Path | Purpose | Idempotency/revision |
|---|---|---|---|
| POST | `/auth/login` | Create a session for a user | Rate limited; generic errors |
| POST | `/auth/logout` | Revoke current session | Safe to repeat |
| GET | `/me` | Current user, roles and organization | Read-only |
| GET/POST | `/organizations` | Owner-only workspace bootstrap/list | POST accepts idempotency key |
| GET/POST | `/students` | List/create tenant-scoped students | POST idempotency key |
| GET/POST | `/subjects` | List/create subjects | POST idempotency key |
| GET/POST | `/questions` | List/create draft question versions | POST idempotency key |
| GET/POST | `/exams` | List/create draft exams | POST idempotency key |
| POST | `/exams/{id}/publish` | Freeze an immutable exam version | Requires `revision`; no merge |
| POST | `/exams/{id}/assignments` | Assign a published version to students | Idempotency key |
| POST | `/attempts` | Start an assignment attempt | One active attempt policy |
| GET | `/attempts/{id}` | Read attempt and server deadline | Tenant/student scoped |
| PUT | `/attempts/{id}/answers/{question_id}` | Replace one answer snapshot | `Idempotency-Key` + answer revision |
| POST | `/attempts/{id}/submit` | Submit before deadline | Idempotent; server scores |
| GET | `/attempts/{id}/result` | Student/admin result view | Release policy enforced |
| GET | `/sync/pull` | Pull tenant-scoped change envelopes | Cursor + bounded batch |
| POST | `/sync/push` | Push LAN-originated envelopes | Event ID/origin sequence dedupe |
| GET | `/health/` | Liveness/readiness | No secrets |

Mutation responses should include a stable resource ID, `revision`, `updated_at`, and an audit event ID. Conflicts use HTTP 409 with a safe machine-readable code; clients must not auto-merge published exam content, answers, submissions or results.

## Data and consistency rules

- Every domain row carries an organization/tenant foreign key and is filtered in queryset and permission layers.
- `ExamVersion` is immutable after publication; `Attempt` references the exact version and question revisions.
- `Attempt.deadline_at` is server-issued and evaluated server-side for manual and automatic submission.
- Answer writes are transaction-safe and append an audit event; retries with the same idempotency key return the original result.
- Submission is exactly-once through a database constraint/state transition; scoring runs in the same transaction for the MVP.
- `SyncEvent`/outbox rows carry event ID, installation ID, origin sequence, entity ID, operation, base revision, schema version, checksum and timestamps. Pull/push is cursor-based with gap detection.

## LAN/WAN behavior

LAN mode serves the same frontend/API on an institution-managed node and remains usable without WAN. Local PostgreSQL is authoritative during an exam window. When connectivity returns, only approved, append-only events synchronize; published exams, answer events, submissions, results and audit records never silently merge. Cloud mode uses managed PostgreSQL and an authenticated sync worker. Media uses a storage adapter with content hashes and never travels inside large event payloads.

## Security and operational gates

- Enforce tenant and role checks in API permissions and database queries.
- Use secure, short-lived sessions, CSRF protection, rate limits, generic recovery responses and audit logging.
- Keep secrets out of source and `.env.example`; use deployment secret stores.
- Run migrations as a reviewed release step; health-check before traffic; keep encrypted backups and restore drills.
- Do not deploy with unresolved critical security findings.

## Integration assumptions for manager review

1. Backend exposes `/health/` and the API paths above; frontend reads `VITE_API_BASE_URL`.
2. Backend uses `DATABASE_URL`; the Compose service supplies PostgreSQL credentials.
3. Frontend supports `npm run dev -- --host 0.0.0.0` for LAN development.
4. Automated tests can run without a live external service; PostgreSQL-backed tests may use a local test database or a CI service.
5. The manager approves any contract changes and records them in the shared task board before integration.

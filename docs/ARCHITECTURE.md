# Architecture baseline

The selected implementation is a React + TypeScript + Vite frontend, a Django + Django REST Framework API, and PostgreSQL for LAN/cloud deployments. SQLite remains an explicit local test fallback when `DATABASE_URL` is absent. The first slice is objective-question focused and keeps answer keys server-side for student responses.

## Manager architecture

The primary Codex session is the manager. It coordinates specialist threads, owns shared files and integration, and records evidence in `docs/TASKS.md`. Specialist roles are bounded implementers or reviewers; they do not change shared contracts or spawn further agents.

## Contract gates

The architect proposed the smallest end-to-end data flow in `docs/ARCHITECTURE_PROPOSAL.md`; the manager integrated the contract into the backend and frontend foundations. The Design Director gate is represented by the original Northstar visual system and recorded desktop/tablet/mobile screenshots. Backend owns server behavior and validation; frontend owns presentation and client state; AI remains out of scope until a measurable product need exists.

## Implemented vertical-slice contract

- `GET /health/` and `/api/v1/health/` provide non-secret health responses.
- Session auth uses CSRF-aware `/api/v1/auth/csrf/`, `/api/v1/auth/login/`, `/api/v1/auth/logout/` and `/api/v1/me/` endpoints.
- Tenant-scoped resources include organizations, students, subjects, questions, exams, sections, assignments, attempts and results.
- Students see only assigned published exams and never receive `correct_answer` in serialized exam questions.
- Exams support `available_from`/`available_until`; server start rejects attempts outside the window.
- Attempt answers are checked against the assigned exam, and submission is transaction-safe and idempotent.
- `/api/v1/sync/pull/` and `/api/v1/sync/push/` expose bounded, tenant-scoped outbox envelopes with idempotency-key conflict protection. They do not auto-merge published content or answer conflicts.

## Unresolved decisions

- Event rules, judging rubric, deadline, and permitted AI use
- Required integrations, hosting, budget, and deployment constraints

These remain tracked uncertainties in `docs/TASKS.md`; they do not block local workflow implementation but do block external deployment or competition-specific claims.

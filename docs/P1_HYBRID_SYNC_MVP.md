# P1.2 Hybrid LAN + Cloud Sync MVP

## Scope

This milestone demonstrates upstream outage tolerance, not browser-offline
operation. A student browser remains connected to the institute LAN Django
node while that node cannot reach the cloud node. The LAN node remains the
authority for the attempt and its server-calculated result; the cloud node is
reconciled when connectivity returns.

## Nodes and configuration

- **LAN node:** the local Haptric Django deployment used by an institute.
- **Cloud node:** the upstream Haptric Django deployment used for centralized
  staff review.
- `HAPTRIC_NODE_ID` is an operator-managed stable installation identifier and
  is included in every event. It must be different for the two demo nodes.
- `HAPTRIC_SYNC_URL` configures the LAN node's upstream ingest URL.
- `HAPTRIC_SYNC_TOKEN` configures the node-to-node authentication secret. It is
  supplied through the environment only and is never exposed to browsers.

The two nodes use matching organization, student, exam, section and question
reference data for this MVP. Automatic master-data discovery is out of scope.

## Event contract

The durable outbox envelope contains `event_id`, `event_type`, organization,
`origin_node`, aggregate type/id, `occurred_at`, `schema_version`, and a
validated payload. Supported event types are `attempt.started`,
`answer.saved`, and `attempt.submitted`. Payloads contain attempt/answer/result
state needed for reconciliation, never passwords, sessions, answer keys or
private marking metadata.

Events are written in the same transaction as the business mutation. The
outbox retains delivery state (`pending`, `delivered`, `failed`, or
`conflict`) and the last error. Event IDs and idempotency keys are stable.

The ingest endpoint is configured for one organization per node through
`HAPTRIC_SYNC_ORGANIZATION_ID`; this prevents a valid node token from being
used to inject events into another tenant. Browser sessions cannot call the
ingest endpoint because it requires the node header and no browser path stores
the token.

## Delivery and conflict policy

The management command `python manage.py sync_upstream` performs bounded,
repeatable LAN-to-cloud delivery. A network failure leaves local business data
and outbox events intact. Identical replays are accepted once; an incompatible
payload for an existing event identity is an explicit conflict. Unsupported,
malformed, oversized, or cross-organization events are rejected. Events that
arrive out of order are rejected or retried unless the submitted snapshot has
all required answer state. No automatic answer merging is attempted.

Cloud ingestion is a dedicated authenticated node boundary, not a browser
endpoint. It materializes only the supported attempt lifecycle against already
seeded reference data. The LAN result is authoritative and is preserved during
ingestion; the browser cannot submit a score to the sync API.

## Acceptance topology

The deterministic integration test starts two Django processes with separate
SQLite files, distinct node IDs and one shared test token. Cloud is made
unreachable while the LAN student completes a three-question exam. The LAN
outbox remains pending/failed, then succeeds after cloud restart. Replaying
the batch leaves one attempt, three answers and one result on cloud. A
synthetic incompatible replay demonstrates explicit conflict handling.

## Deliberate limitations

There is no browser PWA/offline cache, peer discovery, background worker,
automatic master-data synchronization, multi-master merge, or production key
rotation in this milestone. PostgreSQL remains the production target; SQLite
is used only for the isolated local two-node test when Docker/PostgreSQL is
unavailable.

P1.3 hardening, CORS/CSRF topology and the reproducible PowerShell workflow
are documented in `docs/P1_HYBRID_HARDENING.md` and `tools/demo/`.

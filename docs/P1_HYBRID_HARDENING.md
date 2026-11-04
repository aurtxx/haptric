# P1.3 Hybrid Hardening + Reproducible Demo

## Configuration contract

Each process has one stable node identity and one role:

- LAN: `HAPTRIC_NODE_ID`, `HAPTRIC_NODE_ROLE=lan`, `HAPTRIC_SYNC_URL`,
  `HAPTRIC_SYNC_TOKEN`, and `HAPTRIC_SYNC_ORGANIZATION_ID`.
- Cloud: `HAPTRIC_NODE_ID`, `HAPTRIC_NODE_ROLE=cloud`,
  `HAPTRIC_SYNC_TOKEN`, and `HAPTRIC_SYNC_ORGANIZATION_ID`; it does not need
  an upstream URL.
- Both nodes must use explicit `DATABASE_NAME`/`DATABASE_URL`, distinct ports,
  and explicitly configured CORS and CSRF trusted frontend origins.

Tokens are process secrets only. React never receives or stores them. A node
token is compared in constant time, is bound to the configured organization,
and is accepted only for the versioned supported event contract.

## Sync safety rules

The sync command batches pending events per organization. A failure in one
organization is reported independently and does not mix that organization's
events with another batch. Delivery state is tracked per event. `available_at`
is the next retry eligibility timestamp; manual retries do not bypass a
recorded conflict. Identical event replays are safe, while changed payloads,
cross-tenant collisions, unsupported schema versions, and post-submit answer
mutations are explicit conflicts/rejections.

The submitted event contains a complete answer snapshot. Therefore `START →
SUBMIT` is valid when the attempt exists on the receiving node, and a replayed
or late answer cannot silently mutate a submitted attempt. A submitted snapshot
arriving before a separate answer event is authoritative for the included
answer; an incompatible later answer is a conflict.

## Browser topology

“Offline” means the student browser still reaches LAN Django while the
configured upstream cloud URL is unavailable. The cloud frontend uses a
separately configured Vite API base and an explicitly allow-listed origin;
credentialed CORS never uses `*`, and CSRF trusted origins are configured in
parallel.

## Reproducible demo

The PowerShell scripts in `tools/demo/` create two disposable SQLite stores,
seed matching synthetic reference data, start LAN and Cloud on separate ports,
simulate an upstream outage, run sync, and perform health/count checks. Reset
only targets the known demo directory and never accepts an arbitrary database
path.

## Scope limits

This milestone does not add browser-offline/PWA support, peer discovery,
multi-master merges, Celery/Redis, deployment, or production key rotation.

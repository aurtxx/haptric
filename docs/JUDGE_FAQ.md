# Judge FAQ

### Why not use a normal cloud exam system?

Cloud-only systems make an upstream outage a hard stop. Haptric keeps the exam workflow on the institute LAN and reconciles the trusted result later.

### What exactly works without internet?

The student can log in to and use a LAN Haptric node while the upstream Cloud node is unavailable. The browser still needs network access to that LAN node.

### Does the student's browser work with no network at all?

No. Browser-offline/PWA operation is out of scope for this release.

### How are duplicate submissions prevented during sync?

Events have stable identities and the Cloud ingest path applies supported events transactionally and idempotently. A replay does not create another attempt, answer, or result.

### What happens if sync runs twice?

The first run delivers pending events. The second run is a no-op for already delivered events; the business record counts remain unchanged.

### What happens during a conflict?

An incompatible replay is recorded as an explicit conflict. Haptric does not silently overwrite submitted state or merge incompatible answers.

### Can one school see another school's data?

Business queries, staff review, assignments, and sync ingestion are organization-scoped. Cross-tenant access is rejected by the backend tests.

### Where is scoring performed?

Django scores persisted answers on the authoritative node. React never calculates the authoritative result.

### Can students see answer keys?

No. Student exam and attempt payloads redact `correct_answer`, positive/negative marking fields, and other scoring internals.

### How is node-to-node sync authenticated?

The server-to-server request carries an environment-configured sync token. It is compared in constant time and is never sent to the browser.

### What remains before production deployment?

Production key rotation, signed envelopes, background scheduling, PostgreSQL two-node verification, operational monitoring, and deployment hardening remain.

### Why is this useful for schools and coaching centers?

It keeps an exam usable on the local network they control instead of making every student depend on a single upstream connection at the moment of assessment.

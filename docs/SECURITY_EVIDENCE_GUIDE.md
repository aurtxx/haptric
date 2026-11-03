# Security evidence guide

Evidence must prove the observed behavior without becoming a secret store.

## Record

- Scope reference, test ID, date/time/timezone, source-IP label (not an unapproved address), browser/CLI version, and environment.
- Route or visible page name, action summary, expected behavior, actual behavior, status/timing band, and screenshot/snapshot filename.
- Approval reference for the row, request ceiling, account-state check, and whether the result is verified, inferred, blocked, or untested.

## Never record

Passwords, OTP values, reset links, cookies, bearer/session tokens, storage state, API keys, full email/SMS contents, unrelated personal data, hidden endpoint inventories, protected assets, or raw request/response bodies containing those values. Do not put secrets in filenames, command arguments, logs, screenshots, tickets, or chat.

Store browser artifacts only beneath ignored `.playwright-cli/` paths. Redact before sharing. If an artifact cannot be safely redacted, discard it and record only the observation. Use timestamps and hashes of sanitized files when chain-of-custody is needed; never hash or publish a secret-bearing raw artifact as a substitute for redaction.

## Reporting language

Use “observed” only for behavior supported by an evidence file from the approved session. Use “reported,” “inferred,” “blocked,” or “untested” otherwise. Do not include exploit payloads in a general report; describe the minimum safe reproduction and the impact.

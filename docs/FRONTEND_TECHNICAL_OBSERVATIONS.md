# Frontend technical observations

## Method and limits

Observations were collected from the visible headed Playwright page using public performance metadata and DOM metadata only. JavaScript bundles were not downloaded, opened, copied or decompiled. Query strings, cookies, storage state, authorization headers and response bodies were not recorded.

## Resource metadata snapshot

At the inspection point, `performance.getEntriesByType('resource')` reported these initiator-type counts:

| Initiator type | Count | Classification |
|---|---:|---|
| script | 6 | **CONFIRMED** |
| stylesheet/link | 3 | **CONFIRMED** |
| image | 31 | **CONFIRMED** |
| css/font resources | 7 | **CONFIRMED** |
| fetch | 2 | **CONFIRMED** |
| XMLHttpRequest | 14 | **CONFIRMED** |

The page repeatedly requested the current exam route during section/question navigation. The route shape was observed in performance metadata, but request bodies, response bodies and undocumented endpoint semantics were not inspected. Any API interpretation is therefore **INFERRED**, not confirmed.

## Public filename and runtime indicators

Visible resource filenames included:

- `ee-base.min.js`
- `jquery-ui.custom.min.js`
- `dropify.min.js`
- `virtual-select.min.js`
- `ee-login.min.css`
- `ee-onex.min.css`
- `virtual-select.min.css`

The page exposed jQuery `3.2.1` on `window`. React, Vue, Angular, Bootstrap and Materialize globals were absent at the inspection point. These are **CONFIRMED runtime indicators**, not proof of the complete technology stack; bundled or server-rendered dependencies may not expose globals.

The filename prefix and global checks suggest a server-rendered or progressively enhanced interface using jQuery-era widgets (**INFERRED**). No framework or build pipeline should be asserted without vendor documentation or source access.

## Loading behavior

- Static CSS/JS loaded before exam interaction (**CONFIRMED**).
- Question/section interactions triggered additional XHR activity (**CONFIRMED**).
- Question images were requested as page resources; no image URL or content was copied into project documents (**CONFIRMED handling**).
- Aggregate resource timings were observed, but no performance budget or failure behavior was established (**NOT VERIFIED**).

## Original implementation guidance

- Prefer a typed API contract for `Exam`, `Section`, `Question`, `Attempt`, `AnswerEvent` and `SubmissionReceipt`.
- Keep question content and answer keys server-authorized; deliver only the minimum data needed for the current attempt.
- Use a small reactive state layer for section/question status and an append-only local event queue for LAN mode.
- Serve the same frontend bundle from a LAN node and cloud edge, with a configurable API origin and offline capability rather than depending on vendor-specific paths.
- Add CSP, dependency pinning, SRI for third-party static assets, strict CORS, and redacted telemetry. Never log answer values, credentials or tokens.
- Measure first render, section switch, answer acknowledgement and reconnect recovery in both LAN and WAN deployments.

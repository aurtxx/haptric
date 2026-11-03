# EZExam timer and auto-submit research

## Current status

Timer behavior is **NOT VERIFIED**. The exam has not been scheduled, published, assigned, started or submitted.

## Confirmed configuration surface

| Setting | Observation | Evidence | Status |
|---|---|---|---|
| Duration | UI rejected 1 minute and displayed a permitted range of 10–240 minutes; draft is staged at 10 minutes. | `.playwright-cli/page-2026-11-03T19-55-07-623Z.yml`, `.playwright-cli/page-2026-11-03T19-55-26-390Z.yml` | CONFIRMED |
| Scheduled access | The draft form exposed From and To fields, but the reopened named record currently shows a past 2026-10-21–2026-10-31 window. Provenance of that persisted window is unknown; no new schedule was saved in this retry. | `.playwright-cli/page-2026-11-03T19-55-26-390Z.yml`, `.playwright-cli/page-2026-11-03T20-04-32-640Z.yml` | CONFIRMED UI; attribution NOT VERIFIED |
| Switch limit | Enabled by default with 5 switches allowed. | `.playwright-cli/page-2026-11-03T19-55-41-433Z.yml` | CONFIRMED UI |
| Shuffle | Checkbox visible and unchecked. | `.playwright-cli/page-2026-11-03T19-55-41-433Z.yml` | CONFIRMED UI |
| Auto-submit | No explicit auto-submit control was visible in the inspected creation/settings surface. | `.playwright-cli/page-2026-11-03T19-55-41-433Z.yml` | NOT VERIFIED |

## Required future evidence

Only after separate approval: save a small access window, assign only the disposable student, obtain manual student login, start the exam with user approval, record the visible timer and answer persistence, and observe expiry without changing clocks or scripts. Do not manually submit unless separately approved.

## Proposed LAN/WAN behavior

Use a server-issued monotonic deadline, durable local answers during WAN loss, exactly-once autosubmit, idempotent sync, and a clear `accepted_local`/`synced` state. These are design recommendations, not EZExam findings.

## Unverified user-opened window

A separate tab displayed a student-facing `Check Demo Exam` with a visible timer around 59 minutes at `/online-exams/60635`. Because this was not confirmed as the named TEST-ONLY exam or designated student session, it is not evidence of the requested 10-minute timer or auto-submit behavior. No interaction was performed.

Read-only inspection on 2026-11-03 20:12–20:13 UTC observed the timer decrement from approximately 56:22 to 55:18 while the page remained open. The Instructions modal stated that the test cannot be paused and that Finish Exam submits. The Finish Exam confirmation warned that submission cannot be undone; the final submission link was not activated. The observed 60-minute summary and natural countdown are **CONFIRMED UI behavior for this unverified window**, not proof of server-side expiry or auto-submit. Expiry, automatic submission, timer authority, reconnect handling, and persisted attempt state remain **NOT VERIFIED**.


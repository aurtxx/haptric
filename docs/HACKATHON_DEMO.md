# Haptric judge demo

Target: 3 minutes, never more than 5. Use synthetic local data only. The browser always reaches the LAN node; the outage is between LAN and Cloud.

## Before the room opens

In PowerShell, set a disposable password and sync token in the current session only. Run `tools/demo/setup-hybrid-demo.ps1`, `seed-hybrid-demo.ps1`, both node start scripts, and `hybrid-demo-check.ps1`. Run the LAN frontend on 5173 and the Cloud frontend on 5174 with `VITE_API_BASE_URL` pointed at the matching API. Keep the Cloud terminal easy to stop and restart. Never put demo credentials in Git or this document.

## Hook — 15 seconds

**Presenter does:** Open the Haptric login screen.

**Presenter says:** “A weak internet connection should not stop an exam. Haptric keeps the exam on the institute network, then safely delivers the result when Cloud returns.”

**Judge should notice:** The product name and the LAN-first promise are immediately visible.

## Problem — 20 seconds

**Presenter does:** Point to the staff overview and the Cloud connection panel.

**Presenter says:** “Cloud-only exam tools make outages disruptive. Here, the institute has a local exam node and a separate Cloud node; students can still reach the LAN node when upstream connectivity is unavailable.”

**Judge should notice:** This is upstream outage tolerance, not a claim of browser-offline operation.

## Normal product — 40 seconds

**Presenter does:** Staff login → Overview → Students → Exams. Show the synthetic student, the published three-question exam, and its assignment. Switch to the student session, open My exams, and start the assigned exam.

**Presenter says:** “This is a real Django-backed workflow: staff author and publish, provision a learner, assign the exam, and the student receives a server-issued deadline.”

**Judge should notice:** No role preview or fake local-only exam state is involved.

## Failure moment — 30 seconds

**Presenter does:** Stop only the Cloud terminal. In the LAN student session, answer the questions, refresh once to show persistence, then submit.

**Presenter says:** “Cloud is unavailable now. The student is still answering on the institute LAN. The attempt, answers, timer, and score are committed by the local server.”

**Judge should notice:** The result appears locally and the staff sync card reports changes waiting to sync; the browser never receives the node token.

## Recovery + sync — 40 seconds

**Presenter does:** Restart Cloud. Run `tools/demo/sync-lan.ps1` once. Refresh the Cloud staff frontend.

**Presenter says:** “Connectivity is back. The LAN outbox delivers trusted events server-to-server. The same attempt and result are now visible on Cloud.”

**Judge should notice:** The Cloud result is not re-entered by the browser; it is synchronized from the LAN record.

## Proof — 30 seconds

**Presenter does:** On Cloud, open Results → Review attempt. Show the student, score, three ordered questions, responses, and correctness. Run `sync-lan.ps1` again.

**Presenter says:** “Review is question-level and organization-scoped. Replaying sync is safe: the second run creates no duplicate attempt, answers, or result.”

**Judge should notice:** The score and question marks reconcile with the persisted result, and answer keys remain hidden from student payloads.

## Close — 15 seconds

**Presenter says:** “Haptric gives schools a practical continuity layer: keep teaching and assessing on the LAN, then reconcile safely when the connection returns.”

## Recovery notes

Use [DEMO_RECOVERY.md](DEMO_RECOVERY.md) if a process, port, CORS setting, CSRF setting, token, or reference ID is wrong. If a browser step is unavailable, say so plainly; never present a simulated result as live evidence.

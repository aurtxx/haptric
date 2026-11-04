# Hackathon Demo Runbook

This runbook describes a short, deterministic demonstration of Haptric's real
staff and student workflow. It uses synthetic local data only; it contains no
credentials or private records.

## Before the demo

1. Set a disposable password only in the current PowerShell session:
   `$env:HAPTRIC_DEMO_PASSWORD = 'use-a-local-only-value'`.
2. Run `tools/demo/setup-hybrid-demo.ps1`, then
   `tools/demo/seed-hybrid-demo.ps1`.
3. Set `$env:HAPTRIC_SYNC_TOKEN` to a local-only value and run
   `tools/demo/start-lan.ps1` and `tools/demo/start-cloud.ps1` in separate
   terminals. Start the LAN frontend on port 5173 and the Cloud frontend on
   port 5174 with `VITE_API_BASE_URL` pointed at the matching API.
4. Run `tools/demo/hybrid-demo-check.ps1` before opening two headed browser
   contexts. Credentials are never stored in this document or repository.

## Three-to-five minute flow

1. Sign in as staff and show the Overview metrics loaded from Django.
2. Open Students and show the provisioned synthetic learner.
3. Open Exams, show the three-question exam, its published status, and the
   assignment.
4. Sign in as the student. Open My exams and start the assigned exam.
5. Answer two questions, refresh the browser, and show that the same attempt,
   answers, and server deadline are restored.
6. Answer the final question and submit. Show the server-calculated score and
   counts.
7. Return to the staff session, open Results, select **Review attempt**, and
   show the submitted student ID, exam title, matching score, and the exact
   three question-level responses, correctness states, and marks.

## 60–90 second hybrid differentiator

After the connected flow is understood, keep the browser connected to the
institute LAN node and make only the configured upstream cloud URL
unreachable. The student can still start, answer, submit, and receive the
LAN server-generated result. Show the staff-only sync status card with pending
events, then restore the cloud node and run `python manage.py sync_upstream` on
the LAN node. Open Results on the cloud node to show the synchronized attempt
and review. Run the command once more to demonstrate that the event IDs are
idempotent and no duplicate attempt, answers, or result are created.

This is upstream outage tolerance, not a browser-offline/PWA claim. The
student device continues to reach the local LAN Django server throughout.

The outage moment is repeatable: stop only the Cloud process, complete the
student attempt on LAN, run `tools/demo/sync-lan.ps1` once to show retained
failure, restart Cloud, run it again, and refresh the Cloud staff Results page.
Run it a third time to show replay does not duplicate records. Use
`tools/demo/reset-hybrid-demo.ps1` only when the disposable demo data should
be removed.

## Proof points

- Authentication is Django session authentication, not a role preview.
- The student payload contains questions without answer keys or marking
  internals.
- Attempt state, answers, deadline, submission, and score are persisted by
  Django and survive refresh.
- Staff review is organization-scoped; a staff user cannot see another
  organization's attempts.

If a local service or browser step is unavailable, describe the limitation in
`docs/LATEST_COMPLETION_REPORT.md` rather than presenting a simulated result.

# Hackathon Demo Runbook

This runbook describes a short, deterministic demonstration of Haptric's real
staff and student workflow. It uses synthetic local data only; it contains no
credentials or private records.

## Before the demo

1. Start Django and the Vite frontend using the commands in `README.md`.
2. Create a disposable local organization, staff user, student (`HACK-001`),
   published three-question exam, and assignment using the documented API or
   local fixture helpers. Do not commit the temporary password.
3. Open two headed browser contexts so staff and student sessions remain
   isolated.

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

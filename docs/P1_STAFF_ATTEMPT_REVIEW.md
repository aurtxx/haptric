# P1.1 — Staff Attempt Detail + Answer Review

## Scope

P1.1 adds a secure, persisted staff review contract and UI for understanding
submitted attempts question by question. It does not change the student exam
engine, add offline synchronization, or introduce analytics.

## API contract

`GET /api/v1/attempts/{attempt_id}/review/`

The endpoint is protected by `IsOrgStaff` and resolves attempts through the
existing organization-scoped `AttemptViewSet` queryset. It returns:

- attempt, student, exam, status, and lifecycle timestamps;
- the persisted `Result` summary when available; and
- ordered section/question rows containing the question prompt/type/options,
  the persisted student response, answer state, and server-derived marks.

For submitted attempts, the staff-only representation also includes the
correct answer. The general `AttemptSerializer`, exam payload, and student
endpoints remain unchanged and continue to redact `correct_answer`,
`positive_marks`, and `negative_marks`.

## Authorization and active attempts

Staff roles allowed by the existing permission model (owner, admin, teacher,
and invigilator) may review attempts in their own organization. Cross-tenant
attempts resolve as not found. Students cannot call the review endpoint and
continue to receive only their own safe attempt representation.

Opening an in-progress attempt never triggers submission or scoring. The
review response marks answered questions as `pending`, hides answer keys and
marks, and displays an explicit active-attempt warning. Correctness becomes
available only after the persisted submission transition.

## Calculation and integrity

Question-level correctness and marks use the existing server-side
`score_answer()` service. The review tests reconcile the sum of question marks
with the persisted `Result.score`, including normalized multi-choice and
numeric answers. Published questions remain immutable through
the existing `QuestionViewSet` guards, including prompt, options, answer key,
and positive/negative marking fields; regression tests cover those mutations.

## UI behavior

The staff Results screen now supports:

- exam, student, and status filters;
- a `Review attempt` action for each persisted attempt;
- a summary with student identity, exam, timestamps, status, score, and counts;
- question-by-question response, correct answer, state, options, and marks;
- a non-scoring active-attempt state;
- loading, empty, permission/network error, and back-to-results states.

Students never see the staff review control because the screen and endpoint
are role-gated.

## Verification

- Backend targeted review/integrity tests: 4 passed, 19 deselected.
- Frontend review contract and navigation tests are included in the full suite.
- Final delivery records exact full-suite results in
  `docs/LATEST_COMPLETION_REPORT.md`.
- Headed browser verification uses synthetic local data and confirms the staff
  review screen, three ordered questions, persisted responses, state/marks,
  refresh restoration, and absence of the control in the student role.

## Limitations

Staff can review answer detail but cannot edit answers or alter a submitted
result. LAN/cloud synchronization, deployment, historical version migration,
and broader analytics remain outside P1.1.

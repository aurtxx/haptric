# Student exam interaction research

## Observed interaction model

This is a sanitized description of the visible student-facing exam at `/online-exams/60635`. It does not reproduce question content, images or answers.

| Interaction | Visible result | Classification |
|---|---|---|
| Select Maths, Physics or Chemistry | Loads the section's first position and section-specific scoring instructions. | **CONFIRMED** |
| Select question number 1–5 | Changes the visible question number and overview state; no answer entered. | **CONFIRMED** |
| Chemistry question selection | Opens a numeric textbox/numpad; Cancel closes it and leaves the value empty. | **CONFIRMED** |
| Instructions | Opens a modal describing Save & Next, review, Finish Exam and no-pause behavior. | **CONFIRMED** |
| Question Paper | Opens a modal with 15 numbered positions; question content intentionally omitted. | **CONFIRMED count only** |
| Overview legend | Opens a legend for answered/not answered/not visited/review states. | **CONFIRMED** |
| Submit Exam | Opens a Finish Exam modal with an irreversible-action warning. Final submit not selected. | **CONFIRMED UI / NOT VERIFIED submission** |
| Timer | Counts down while the page remains open. | **CONFIRMED display / NOT VERIFIED authority or expiry** |

## Sanitized state machine

`loaded → section_selected → question_visited → (answer_entered → answer_saved) or (marked_for_review) → finish_confirmation → submitted`

Only `loaded`, `section_selected`, `question_visited` and `finish_confirmation` were observed. The remaining transitions are **NOT VERIFIED** because testing them would create or submit attempt data.

## UX and QA notes

- The overview exposes five positions per section and status concepts that should be available to keyboard and screen-reader users.
- The last Chemistry question uses a `Save & Finish` label, while earlier positions use `Save & Next`; this should be explicit in an independent design system.
- The UI displays scoring rules near the current question, reducing the need to reopen instructions.
- Numeric entry uses both a textbox and an on-screen numpad; an independent platform should also support physical keyboard input and validation for decimal/negative constraints.
- No answer, blank-submit warning, reload recovery, offline retry, or autosubmit behavior was tested; these remain **NOT VERIFIED**.

## Proposed hybrid LAN/cloud behavior

Use a local attempt journal with monotonic sequence numbers. Each answer event should be idempotent, bound to an attempt and question version, and queued during connectivity loss. A cloud or LAN server should accept events only within the server-issued deadline, return an acknowledgement cursor, and resolve duplicate/reordered events deterministically. Final scoring and submission should be server-authoritative, with a tamper-evident audit trail.

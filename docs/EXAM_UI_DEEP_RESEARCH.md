# EZExam exam UI deep research

## Scope and evidence

This document records sanitized, read-only observations from the existing headed `product-research` Playwright session at `/online-exams/60635` on 2026-11-03 20:19–20:21 UTC. The visible exam was titled `Check Demo Exam`; its identity as the approved TEST-ONLY fixture was **NOT VERIFIED**. Question text, answer keys, images, personal data, credentials, cookies and tokens were deliberately omitted.

Evidence is limited to ignored Playwright snapshots such as:

- `.playwright-cli/page-2026-11-03T20-19-45-876Z.yml` (Maths Q1)
- `.playwright-cli/page-2026-11-03T20-19-57-729Z.yml` (Maths Q5)
- `.playwright-cli/page-2026-11-03T20-20-02-514Z.yml` (Physics Q1)
- `.playwright-cli/page-2026-11-03T20-20-13-973Z.yml` (Physics Q5)
- `.playwright-cli/page-2026-11-03T20-20-18-151Z.yml` (Chemistry Q1)
- `.playwright-cli/page-2026-11-03T20-20-52-929Z.yml` (Chemistry Q3)
- `.playwright-cli/page-2026-11-03T20-20-43-688Z.yml` (Chemistry Q4)
- `.playwright-cli/page-2026-11-03T20-20-05-928Z.yml` (Chemistry Q5)

## Question-position inventory

| Positions inspected | Visible structure | State classification |
|---|---|---|
| Maths 1–5 | Each position displayed four answer affordances labelled A–D, `Only ONE correct option`, +3 correct and −1 incorrect, `Mark for Review & Next`, `Save & Next`, and a five-position overview. | **CONFIRMED**; no option was selected. |
| Physics 1–5 | Each position displayed four answer affordances labelled A–D, `ONE OR MORE correct options`, multi-select scoring guidance, `Mark for Review & Next`, `Save & Next`, and a five-position overview. | **CONFIRMED**; no option was selected. |
| Chemistry 1–5 | Each position displayed numerical-value instructions, +4 correct and 0 incorrect, `Mark for Review & Next`, `Save & Next`; selecting a position opened a numeric textbox and on-screen numpad with digits, decimal point, minus, Backspace and Clear All. | **CONFIRMED**; no numeric value was entered. |

The last Chemistry position displayed `Save & Finish` in place of `Save & Next`. This was observed in the UI, but its server-side effect was not tested. **CONFIRMED UI / NOT VERIFIED persistence.**

## Navigation and state transitions

1. Selecting a section loaded its first position and showed a section-specific question count, marks and answer mode (**CONFIRMED**).
2. Selecting a question number changed the visible `Q.No.` and answer affordances without entering an answer (**CONFIRMED**).
3. Entering a section showed counters such as `Answered Qs: 0`, `Unanswered Qs: 1`, and `Not Visited Qs: 4`; this suggests the current position becomes visited on navigation (**CONFIRMED UI; state semantics INFERRED**).
4. Opening and closing the Chemistry numpad did not populate a value (**CONFIRMED**).
5. The timer decreased naturally while navigation occurred, from approximately 00:49:06 to 00:47:49 (**CONFIRMED runtime display; server authority NOT VERIFIED**).

## Modals and warnings

- Instructions modal: Save & Next saves and advances; Mark for Review & Next marks a question; Finish Exam submits; pausing is unavailable (**CONFIRMED UI**).
- Full Question Paper modal: headings 1–15 were shown; content was not copied (**CONFIRMED count only**).
- Overview Legend modal: explained Answered, Not Answered, Not Visited, Marked for Review and Answered & Marked for Review (**CONFIRMED UI**).
- Finish Exam modal: showed `This can't be undone!`; the final `Submit Answers` action was not clicked (**CONFIRMED warning; submission NOT VERIFIED**).
- Validation for blank Save/Finish, review persistence, answer persistence, reload recovery and expiry behavior were not exercised (**NOT VERIFIED**).

## Responsive and keyboard observations

- At 390×844 and 1280×800, the section tabs, question overview, navigation controls and modal links remained present in snapshots (**CONFIRMED structural observation**). A full visual/accessibility audit was not performed (**NOT VERIFIED**).
- Repeated Tab presses moved focus to visible modal/navigation links, including Instructions (**CONFIRMED keyboard traversal**). Complete focus order, visible focus styling, screen-reader names and keyboard activation of answer controls remain **NOT VERIFIED**.

## Independent implementation recommendations

- Model an exam as immutable published sections with explicit question type, answer schema, scoring policy and stable position IDs.
- Make `visited`, `answered`, `marked_for_review`, `saved_local`, `synced` and `submitted` separate state fields rather than deriving them from CSS classes.
- Provide semantic radio/checkbox/number inputs with labels and keyboard-operable section/question navigation.
- Use a server-issued deadline plus a monotonic client display; persist answers locally for LAN outages and synchronize idempotently.
- Show a reversible review screen before final submission, then enforce exactly-once submission server-side.
- Treat images and question text as tenant content with authorization checks; never expose answer keys to the client.

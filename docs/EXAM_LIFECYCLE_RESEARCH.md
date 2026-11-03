# EZExam exam lifecycle research

## Scope and status

This is supervised research in the authorized test tenant only. The headed `product-research` session is authenticated as the expected Super Admin. Authorization and tenant scope remain user-reported and are not independently verified.

Status: **blocked on persistence mismatch before any new schedule/share/start action**.

## Confirmed observations

| Stage | Route/state | Observation | Evidence | Confidence |
|---|---|---|---|---|
| Step 1 | `/staff#` | New Online Exam form exposes Exam Name, Duration (minutes), and Next. | `.playwright-cli/page-2026-11-03T19-51-16-265Z.yml` | CONFIRMED |
| Duration validation | `/staff#` | A 1-minute value was rejected with “Duration must be between 10 and 240 mins!”. | `.playwright-cli/page-2026-11-03T19-55-07-623Z.yml` | CONFIRMED |
| Draft input | `/staff#` | Test exam name and duration 10 were entered; the draft flow showed an “Exam Updated” processing toast, but server acceptance was not independently verified. | `.playwright-cli/page-2026-11-03T19-55-26-390Z.yml` | INPUT ENTERED; SERVER ACCEPTANCE NOT VERIFIED |
| Question entry | `/staff#` | One-by-one authoring supports text plus four-option single-correct questions, answer key, subject and markings. | `.playwright-cli/page-2026-11-03T19-53-03-272Z.yml` | CONFIRMED |
| Synthetic questions | `/staff#` | Three original questions were entered in the draft flow with positive marking 1 and negative marking 0, but the reopened record did not contain them. | `.playwright-cli/page-2026-11-03T19-53-59-961Z.yml`, `.playwright-cli/page-2026-11-03T19-54-47-645Z.yml`, `.playwright-cli/page-2026-11-03T19-54-58-712Z.yml`, `.playwright-cli/page-2026-11-03T20-04-07-546Z.yml` | INPUT/CLIENT FLOW CONFIRMED; PERSISTENCE FAIL |
| Blank-question behavior | `/staff#` | After saving question 3, the UI opened a blank question 4 editor and displayed Questions (4). Reopening the named record instead showed Questions (15), so the blank editor was not verified as persisted. | `.playwright-cli/page-2026-11-03T19-55-26-390Z.yml`, `.playwright-cli/page-2026-11-03T20-04-07-546Z.yml` | NOT VERIFIED |
| Reopened named record | `/staff#qexam-qstns` | The only grid record with this name reopened with duration 10, Questions (15), question 1 showing an existing image, marking 3 / -1, and a different Verify Questions reference. | `.playwright-cli/page-2026-11-03T20-03-47-539Z.yml`, `.playwright-cli/page-2026-11-03T20-04-07-546Z.yml` | CONFIRMED; DOES NOT MATCH TEST FIXTURE |
| Persisted schedule/share | `/staff#qexam-share` | Reopened record showed From 2026-10-21 8:13 pm, To 2026-10-31 8:13 pm and JEE-Main tag. These values are persisted UI state, but their provenance relative to this run is unknown. | `.playwright-cli/page-2026-11-03T20-04-32-640Z.yml` | CONFIRMED; PROVENANCE NOT VERIFIED |
| Advanced options | `/staff#` | Visible defaults: switch limit enabled at 5; shuffle, camera, hide results/ranks/analytics, PC-only, practice exam, section skipping and hide-questions-in-analytics are unchecked. | `.playwright-cli/page-2026-11-03T19-55-41-433Z.yml` | CONFIRMED |

## Not performed / not verified

- No new schedule or time window was saved during this retry.
- No new student assignment or invitation was saved during this retry. The reopened record already displayed a JEE-Main tag assignment.
- No exam link was created.
- No notification was sent.
- No exam was started, submitted or published.
- Exact persisted question count for the intended three-question fixture is **FAIL**: the reopened record shows 15 questions. Randomization behavior, result visibility, access control, auto-submission and scoring remain NOT VERIFIED.

## Verification status matrix

| Property | Status | Evidence |
|---|---|---|
| Exam input entered | PASS | Step 1/2 snapshots |
| Save/process toast observed | PASS for UI feedback only | `19-55-26-390Z` |
| Intended exam server-accepted | NOT VERIFIED | No stable matching record was found |
| Intended three-question record persisted | FAIL | Reopened record has 15 questions and different content/settings |
| Blank fourth editor persisted | NOT VERIFIED | Reopened record mismatch prevents attribution |
| Schedule/assignment for this run | NOT VERIFIED | Existing past schedule/tag has unknown provenance |

## Proposed independent-platform requirements

These are recommendations, not EZExam observations: immutable published exam versions; server-authoritative deadlines; durable local attempt writes on LAN; idempotent submission and cloud sync; explicit conflict records; append-only audit events; and a visible recovery state after connectivity loss.


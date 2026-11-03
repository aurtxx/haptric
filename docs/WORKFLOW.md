# Development workflow (compatibility reference)

The authoritative orchestration rules are in [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md). This file remains for existing references; where wording differs, AGENT_WORKFLOW.md and AGENTS.md take precedence.

The primary session is the manager. Only the manager delegates; specialists do not spawn further agents. Use at most four children, fewer when tasks are small. Use sequential role execution when spawning is unavailable and report that honestly.

## Assignment contract

Every assignment supplies: task ID, objective, exclusive writable paths (or read-only), inputs and approved contract, dependencies, acceptance criteria, prohibited changes, verification commands, and a timebox. Default timebox is 15 minutes; report progress or blockers at expiry and stop expanding scope. The manager cancels or reassigns stalled tasks after checking their changes. No additional paid services or purchases without approval; report usage when available rather than inventing cost estimates.

Handoffs report status, files changed, exact verification commands/results, risks, and blockers. Feature owners implement tests; QA independently verifies acceptance scenarios. Security and QA review read-only; fixes go to feature owners.

## Ownership and integration

The manager alone edits TASKS.md, shared manifests/lockfiles, root configuration, and approved contracts. Architect proposes contracts; manager integrates them. Frontend owns UI/UX/accessibility; backend owns services/auth/persistence; AI owns explicitly assigned AI modules and evaluations. Never assign overlapping writable paths. Request shared changes through the manager. If an unexpected overlapping edit appears, stop the affected work, inspect the diff, and agree ownership before continuing; never revert another agent's changes.

## Delivery gates

1. Complete PRODUCT.md: official event URL/rules, deadline/timezone, rubric, permitted tools, problem/user, core journey, measurable success, exclusions, data/privacy/auth needs, integrations, budget/accounts, team time, and hosting constraints.
2. Architect proposes the smallest design and API contracts; security reviews risks and DevOps hosting feasibility. Manager approves before implementation.
3. Assign separate frontend/backend tasks against approved contracts. Delegate AI only when required. Build one complete journey before expanding scope.
4. Manager integrates; run available lint, typecheck, tests, build, and browser acceptance walkthrough. Record exact results and unavailable checks. QA and security independently review. Unresolved critical security exposure blocks external deployment.
5. DevOps prepares environment/setup, CI, smoke tests and rollback. Strategist verifies official rules and prepares pitch, submission checklist and offline fallback. Ask before every external deployment (preview or production), destructive operation, or spending money. After approved deployment, smoke-test and rehearse.

Done means acceptance criteria pass, relevant checks have evidence, review blockers are resolved, setup/limitations are documented, and manager updates the board. Failed or unavailable checks must never be reported as passing.

## Capability evidence (2026-11-03)

Installed CLI reported 0.166.0; features list reported multi_agent enabled and multi_agent_v2 disabled. Security and architect specialist tasks returned real independent audits in this session. Exact simultaneous execution and capacity limits were not benchmarked. Project declares four spawned children. All ten role paths exist. `codex --strict-config features list` is unsupported; do not use it as a validation command. Full installed-version strict validation and effective reviewer sandbox enforcement remain unverified. The authoritative, current capability evidence is in AGENT_WORKFLOW.md.

No application manifest exists yet, so lint/typecheck/tests/build are unavailable. Do not install dependencies merely to audit this starter.

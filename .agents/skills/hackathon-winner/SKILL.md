---
name: hackathon-winner
description: Plan, build, test, deploy and pitch an end-to-end hackathon MVP with judging criteria, demo reliability, timeboxing and specialist agent delegation. Use for hackathons, rapid prototypes and competition submissions.
---
# Hackathon execution playbook
1. Read docs/PRODUCT.md. Confirm actual event rules, permitted AI use, judging rubric, submission format, and deadline from official sources; never assume or fabricate them.
2. Rank ideas by user pain, novelty, feasibility, impact, and demo clarity. Choose a single sharp problem statement.
3. Produce a 60-second demo story and a measurable acceptance test before coding.
4. Delegate architecture, UX, frontend, backend, AI, QA, security, DevOps and pitch to specialist agents only when appropriate; avoid agent overhead for tiny tasks.
5. Build one complete vertical slice first, with realistic sample data and resilient error states. Keep frontend/backend contracts written down.
6. Validate with automated tests and a real browser walkthrough where tools permit. Never claim unrun checks passed.
   For visual work, use Product Brief -> Design Director -> Design Specification -> Frontend Engineer -> Browser Screenshot Review -> Visual QA -> Fixes -> Final Review. Do not claim visual QA without screenshots at the required viewports.
7. Prepare README, setup instructions, screenshots or demo video if permitted, deployment URL, backup offline demo, and 2-minute pitch.
8. Conduct a rubric-based review: problem, solution, novelty, implementation, UX, impact, feasibility, demo quality. Mark unknown criteria as unknown.
9. Prioritize fixes: broken demo > critical security > incomplete core flow > visual polish > extra features.
   Unresolved critical security exposure blocks external deployment regardless of demo priority. Follow docs/AGENT_WORKFLOW.md for manager-only delegation, exclusive ownership and approval gates.
10. Finish with submission checklist and precise known limitations.

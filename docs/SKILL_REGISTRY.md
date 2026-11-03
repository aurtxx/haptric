# Skill registry

This registry records the project-local skills and their reviewed upstream sources. Commits are pinned to the upstream `main` head observed on 2026-11-03; update deliberately rather than silently following moving content. Skill installation copied instruction files and supporting assets only; no upstream scripts were executed.

| Skill | Local path | Upstream / commit | License | Dependencies and use |
|---|---|---|---|---|
| design-taste-frontend | `.agents/skills/design-taste-frontend` | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill), `12af471f627f866411b4bd785b19646d3672784c` | MIT | Node 22+ and Chrome/Edge/Chromium for its browser inspector; network only for optional image search; baseline for visual direction and screenshot critique |
| gpt-taste | `.agents/skills/gpt-taste` | [Leonxlnx/taste-skill-classics](https://github.com/Leonxlnx/taste-skill-classics), `5e08c9383dc4ad7fc0df70e1ac8cfa09ec356305` | MIT | Opt-in only; recommends GSAP and motion-heavy patterns, so select only when the product and performance budget justify it |
| image-to-code | `.agents/skills/image-to-code` | [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills), `beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e` | MIT | Requires an image-generation capability plus implementation; image-first workflow; no application dependency installed by the skill |
| frontend-design | `.agents/skills/frontend-design` | [anthropics/skills](https://github.com/anthropics/skills), `ca45fc496a3436251f191354091d557da31c15b5` | Apache-2.0 (`LICENSE.txt`) | Instruction-only; use for subject-specific visual direction and design plans |
| web-design-guidelines | `.agents/skills/web-design-guidelines` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills), `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` | MIT | Fetches the latest guideline source at review time; use for terse UI/accessibility audits |
| playwright-cli | `.agents/skills/playwright-cli` | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli), `db2a0fad3a768319a16e3a2bb8078cf62e690b07` | Apache-2.0 | Node 18+; global `@playwright/cli`; headed mode requires `--headed`; persistent profiles use `--persistent`; browser artifacts stay under ignored `.playwright-cli/` |
| hackathon-winner | `.agents/skills/hackathon-winner` | Project-local | Project instructions | Product/rules verification, vertical slice, testing, demo and submission gates |

## Selection policy

Use `design-taste-frontend` as the baseline. Add `frontend-design` for deliberate visual direction. Call `gpt-taste` only by explicit manager selection because it imposes a GSAP/AIDA-heavy direction. Use `image-to-code` only when supplied or generated visual references are the source of truth. Run `web-design-guidelines` during UI review after fetching its current rules. Do not combine conflicting art-direction systems without a written manager decision.

## Compatibility and provenance

All installed entries contain an Agent Skills `SKILL.md` frontmatter block and are readable by this Codex project. `skills-lock.json` records content hashes for reproducibility. Upstream repositories are third-party content: review changes, licenses, network use, and scripts before upgrading. The Playwright CLI package is the only runtime package installed for browser capability; design skills themselves add no application dependencies.

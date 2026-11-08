# Fresh Haptric pitching prototype

Open `index.html` directly in a browser after restarting the laptop. No installation, server, credentials or internet connection is needed. The walkthrough and presenter notes are included on the page; README.md contains the 60-second script.

## What was delivered

An original responsive concept based on the saved product brief: a classroom exam continues over the school LAN while cloud connectivity drops. The interactive demonstration includes three questions, simulated WAN disconnection, queued answer changes, reconnection, a control-room view, one stable submission receipt, reset and presentation mode. Existing application code was not copied or modified.

This is a pitching simulation using in-memory browser state. Refresh clears the demo. It does not implement a real backend, persistent answer storage, authentication, scoring or network synchronization. Production readiness and load capacity are not asserted.

## Verification

- `node --check pitch-prototype/app.js` passed.
- `node pitch-prototype/verify.cjs` passed with installed Playwright and local Chrome.
- `git diff --check` passed.
- Browser checks covered file-based opening; desktop 1440×1000, tablet 820×1180 and mobile 390×844; no horizontal overflow; no remote HTTP requests or page errors; outage queue and recovery; stable receipt after replay; reset; keyboard tabs; submission focus; both presentation exits; presenter notes.
- Local screenshots: `screenshots/desktop.png`, `tablet.png`, `mobile.png`, `outage.png`, `receipt.png`. Generated evidence is intentionally ignored by Git.
- Manager reviewed desktop/mobile screenshots. Independent `pitch_design` review approved the composition and requested focus restoration, a visible presentation exit and a refresh disclosure; all three were implemented before final checks.

The existing Django/React application suites were not run because this separate buildless prototype does not change that application. No dependency installation, external deployment or live security testing was performed.

## Git handoff

Task branch: `feat/fresh-pitch-prototype` in `https://github.com/aurtxx/haptric`.
The delivery response records the verified commit and push outcome. Use `git log -1` for the current checkout's exact commit.

The user requested laptop shutdown after completion. Work is saved on disk before scheduling shutdown; no preview server needs to stay running. The next step is to rehearse this prototype and decide which visual ideas to carry into the production application.

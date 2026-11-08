# Haptric — fresh pitching prototype

Double-click **index.html**. It works directly from disk, without installing anything or starting a server. It will still open after the laptop restarts.

This is a new visual concept based on the saved Haptric product brief: a school runs exams on its LAN while the internet/cloud connection can drop. Existing frontend/backend code and competitor assets were not copied.

## 60-second walkthrough
1. Scroll to “Pull the plug. Keep the answer.”
2. Click “Simulate internet outage.”
3. Choose an answer. Open “Control room”: local answers remain, cloud changes queue.
4. Reconnect. The local and cloud views agree.
5. Answer all three questions and submit.
6. Open “Shared receipt” and replay synchronization: the receipt remains unchanged.
7. “Restart demo” clears only this simulation. “Pitch mode” focuses the demo; Escape or “Exit pitch mode” returns to the page.
8. Presenter notes are at the bottom. Print from your browser for a fallback pitch handout.

## Honest boundaries
All students, answers, network states and receipts are fictional browser state. It does not disconnect your internet, connect to a LAN server, score an assessment, or provide authentication. Reload resets the simulation. The real source project remains separate and unchanged. No customer claims, performance figures, pricing or official event rules are invented.

## Files
- index.html — original page and demonstration
- style.css — responsive visual design
- app.js — local simulation logic
- DESIGN.md — source context, direction and acceptance
- screenshots/ — local review evidence (not committed)
- verify.cjs — interaction and viewport review using installed Playwright

The new work lives on branch feat/fresh-pitch-prototype. No external deployment was performed.

## Repeat the browser checks

The preview itself has no dependencies. The optional verification script needs Node.js, `@playwright/test` and a Chromium browser. If Playwright is installed elsewhere, set `NODE_PATH` to that installation's `node_modules`. Set `PLAYWRIGHT_EXECUTABLE` to your Chrome executable, or omit it when Playwright Chromium is already installed. Run from the repository root:

```powershell
node --check pitch-prototype/app.js
node pitch-prototype/verify.cjs
```

See DELIVERY.md for verification evidence and limitations.

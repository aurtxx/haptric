# UX research and independent design recommendations

## Confirmed observations

- Navigation is organized around Exams, Students, Settings, payments, customization, help videos, and a More menu for Faculty, Centres and Notices.
- Tables use inline column filters and show compact empty states such as “Not found” or “No Exam Attempts Yet.”
- Exam work is a multi-step flow: details/import, timing and sharing, questions, attempts, and analytics.
- The account exposes creation controls beside read-only tables, so mutation boundaries need clear review and confirmation in our product.
- The session showed multiple dense forms and several unlabeled or icon-oriented controls. Mobile and keyboard behavior were not observed.

## Recommendations for our product

- Use a persistent workspace switcher and role-aware sidebar with plain labels, breadcrumbs and an always-visible “read-only preview” state.
- Split authoring into explicit stages with a progress indicator, draft autosave, validation summary, preview, approval and publish gates.
- Make table filters, pagination, bulk selection, import preview and export permissions explicit. Never combine destructive actions with navigation.
- Show a compact “what changes when you publish” panel for exam links, notices and result releases.
- Provide empty states with one safe next action and an explanation of required permissions.
- Treat LAN mode as a first-class mode with a clear offline indicator, last-sync time, queued changes and conflict review.
- Build an original visual identity: calm paper-and-ink neutrals, one high-contrast accent, accessible typography, generous spacing, and restrained data visualization. Do not copy EZExam branding, logos, colors, or distinctive layouts.

## Accessibility and responsive gaps

No browser screenshot, mobile viewport, keyboard traversal, focus order, contrast measurement, screen-reader output, or reduced-motion behavior was collected. These are open validation tasks for our own application, not claims about EZExam.

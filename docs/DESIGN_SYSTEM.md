# Design system contract

Status: pre-product baseline. No application palette, brand, imagery, or component library is approved until `docs/PRODUCT.md` contains a real product brief. This document defines the decisions the Design Director must make and the constraints the Frontend Engineer must implement after approval.

## Design authority

The Design Director owns this document and any product-specific design specification. The manager approves changes before frontend implementation. The Frontend Engineer translates the approved system into code and reports implementation constraints. Visual QA verifies the rendered result with browser evidence.

## Required design decisions

Every product-specific specification must record:

- Visual thesis: one sentence connecting the product's subject matter to its visual language, plus the one memorable element.
- Identity: wordmark treatment, icon approach, imagery source and credit policy, tone of voice, and explicit anti-patterns.
- Type: chosen families, fallback stacks, weights, roles, optical sizes, line lengths, and a responsive type scale.
- Color: named semantic roles for background, surface, raised surface, ink, muted ink, border, accent, success, warning, danger, and focus; contrast evidence for text and controls.
- Space: a base unit, spacing scale, content widths, section rhythm, and rules for dense versus quiet regions.
- Grid: column count, gutters, max width, alignment, and when the composition changes at each viewport.
- Responsive behavior: mobile, tablet, laptop, and wide-screen layout changes; overflow policy; touch target rules; and navigation collapse behavior.
- Components: anatomy, variants, states, content limits, keyboard behavior, focus treatment, reduced-motion behavior, and loading/empty/error states.
- Motion: purpose, duration/easing budget, trigger, interruption behavior, and reduced-motion fallback.

## Neutral implementation tokens

Use semantic names so product values can change without rewriting components. Values remain unassigned until the brief is approved.

```css
:root {
  --color-background: <approved value>;
  --color-surface: <approved value>;
  --color-ink: <approved value>;
  --color-ink-muted: <approved value>;
  --color-border: <approved value>;
  --color-accent: <approved value>;
  --color-focus: <approved value>;
  --space-unit: <approved value>;
  --content-max: <approved value>;
  --grid-gutter: <approved value>;
}
```

Do not introduce a generic cream/terracotta palette, gradient wash, repeated rounded cards, monospace micro-labels, or decorative numbering without a subject-specific reason. These are review prompts, not absolute bans; the brief and Design Director's rationale win.

## Quality floor

The system must support visible keyboard focus, WCAG-appropriate contrast, readable line lengths, touch targets, `prefers-reduced-motion`, responsive layouts down to 390px, and explicit loading/empty/error states. The final specification links the screenshots and browser evidence recorded in `docs/UI_QUALITY_CHECKLIST.md`.

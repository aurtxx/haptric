# UI quality and visual QA checklist

This checklist applies once an application exists. A visual review is incomplete without browser evidence. Never report screenshots, interaction checks, or accessibility checks that were not actually run.

## Evidence set

Capture the same approved flow at minimum:

- Desktop: 1440px wide
- Tablet: 768px wide
- Mobile: 390px wide

Record browser/tool version, URL or local route, commit or working-tree state, viewport dimensions, and screenshot paths. Compare against the approved Design Director specification and reference images. Keep before/after captures for every defect fix that changes visual behavior.

## Visual review

- The first viewport has a clear focal point and the intended primary action.
- Typography uses the approved families, weights, scale, line length, and hierarchy.
- Color roles, contrast, borders, imagery, and focus indicators match the design system.
- Grid alignment, gutters, content widths, section rhythm, and responsive transitions hold at all three viewports.
- No clipped text, overflow, sideways scrolling, collapsed controls, empty grid holes, or accidental layout shifts.
- Loading, empty, success, error, disabled, hover, focus, and pressed states are intentional.
- Motion communicates a state change, does not block interaction, and settles correctly under reduced motion.
- Images have meaningful alternatives or are correctly decorative; credits and licensing are recorded.

## Accessibility and interaction

- Keyboard-only navigation reaches every actionable element in a logical order.
- Focus is visible and never hidden behind sticky or animated regions.
- Semantic headings, landmarks, labels, button names, form errors, and status announcements are present.
- Touch targets and spacing are usable on mobile; zoom and text scaling do not destroy the flow.
- Contrast and non-color cues are checked for text, controls, charts, and validation states.
- Primary and failure paths are exercised with realistic sample data.

## Defect handoff

Report `severity`, viewport, route, exact reproduction steps, expected result, actual result, screenshot path, and owner. Critical visual defects block the demo when they prevent comprehension or the core journey. The Frontend Engineer fixes defects; the Design Director confirms visual intent; QA records the retest evidence.

If browser tools are unavailable, mark visual QA as blocked and provide static review notes. Do not substitute a textual claim for browser evidence.

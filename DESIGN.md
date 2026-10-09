# Design

Visual system for Veridion. Source of truth for tokens: `apps/web/src/app/globals.css`.

## Visual Theme & Atmosphere

An institutional intelligence interface: archival documents, ink, stone and oxidised metal. Marketing pages alternate between deep obsidian "instrument" sections and light reading sections. The analytical workspace is light and quiet, built for long reading sessions next to source PDFs. Precision is communicated through hairlines, alignment, tabular numerals and restraint — not effects.

## Colour Palette & Roles

| Role | Token | Value | Use |
|---|---|---|---|
| Obsidian | `--color-obsidian` | `#101112` · oklch(0.177 0.003 248) | Ink on light; dark section canvas |
| Graphite | `--color-graphite` | `#1B1E20` · oklch(0.233 0.006 237) | Elevated dark surfaces |
| Canvas (warm ivory) | `--color-canvas` | `#F3F0E8` · oklch(0.955 0.011 90) | Light page canvas, app shell |
| Surface (paper) | `--color-surface` | `#FCFBF8` · oklch(0.988 0.004 91) | Reading surfaces: tables, documents, panels |
| Slate | `--color-slate` | `#707780` | Icons, borders, large metadata only (3.97:1 on canvas) |
| Ink muted | `--color-ink-muted` | `#5B626A` | Secondary text on light (5.4:1) |
| Brass | `--color-brass` | `#A88C55` | Brand accent on dark only; focus ring; one highlight per view |
| Brass deep | `--color-brass-deep` | `#7D6533` | Partial status and brass text on light (4.9:1) |
| Forest | `--color-forest` | `#31483E` | Supported, positive |
| Oxide | `--color-oxide` | `#9B4B43` | Conflicts, destructive, errors |

Strategy: **Restrained.** Tinted neutrals carry 90%+ of every view. Brass is never a generic highlight on every card or border.

### Status vocabulary (never colour alone)

| Status | Glyph | Colour |
|---|---|---|
| Supported | filled circle | forest |
| Partially supported | half-filled circle | brass deep |
| Evidence not found | open circle | ink muted |
| Conflicting evidence | crossed diamond | oxide |
| Human review required | circle with centre dot (an eye, abstracted) | obsidian |

## Typography

- **Display:** Libre Caslon Display (400) for major editorial headlines and selected section titles only. Caslon: the printer's type of record.
- **Editorial text serif:** Libre Caslon Text for pull quotes and serif sub-heads.
- **Interface:** Geist for navigation, tables, forms, controls and body. Tabular numerals (`font-variant-numeric: tabular-nums`) for all figures.
- **Technical:** Geist Mono only for document identifiers, evidence IDs, hashes, timestamps and version strings.
- Product scale (fixed rem, ~1.2 ratio): 12 · 13 · 14 · 16 · 19 · 23 · 28. Marketing display uses `clamp()` with a ceiling of ~5.5rem.
- Headings use `text-wrap: balance`; prose uses `text-wrap: pretty` and a 68ch measure.

## Components

- **Buttons:** square-ish (2px radius). Primary: obsidian on light / canvas on dark. Secondary: hairline outline. Ghost for tertiary. One primary per view.
- **Hairlines:** 1px `--color-rule` borders and tonal separation instead of shadows. Elevation only for overlays (drawers, menus).
- **Tables:** sticky headers, 40px rows (32px compact), keyboard row navigation, status glyph + label column, tabular numerals.
- **Inspector:** contextual right panel (440px) that appears only when something is selected; becomes a drawer below 1280px.
- **Evidence Explorer:** a size container. Where it has room (48rem and up) findings are a table, with period and assessment columns from 56rem; narrower (phones, tablets, or beside the inspector) they become stacked entries with code, status, coverage, missing elements and source. The selected finding stays in view when the layout changes.
- **Evidence Trail:** requirement → evidence → rationale → gap → action, joined by thin connector lines; the signature interaction. Narrow panels drop the connectors and wrap the step links.
- **Document viewer:** rendered PDF page with SVG highlight rectangles over the cited bounding boxes.

## Layout

- Product: left navigation (232px) · main workspace · optional inspector (440px). Generous space around primary content, dense tables where the task needs them. Workspace components respond to their container's width, not the viewport's.
- Marketing: 12-column grid, max content width 1240px, asymmetrical compositions, long measured scroll. 16px side gutter on mobile.
- z-index scale: dropdown 10 · sticky 20 · drawer-backdrop 30 · drawer 40 · toast 50 · tooltip 60.

## Motion

- 160–240ms, ease-out-quart (`cubic-bezier(0.25, 1, 0.5, 1)`). Motion conveys state: panel open, selection, a source being revealed, a changed assessment.
- One slow, purposeful reveal on the marketing hero (the evidence instrument resolving a trail). No scroll-jacking, parallax, particles or cursor effects.
- `prefers-reduced-motion`: transitions become instant or crossfades.

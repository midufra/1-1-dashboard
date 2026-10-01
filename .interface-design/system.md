# Sales Enablement 1:1 — design system

Source of truth for `docs/index.html`. Read this before touching the page's
CSS, markup, or JS — it records decisions already made so they don't get
re-litigated or defaulted away in a future pass.

## Direction and feel

The page is styled as a **printed editorial memo** — a weekly dispatch
someone hands you before a 1:1, not a SaaS dashboard. The vocabulary is
journalism, not software: masthead, ledger, lede, dispatch, agenda, dossier.
That vocabulary shows up directly in class names (`.masthead`, `.ledger`,
`.lede`, `.sect-k`) and in the hanging-label layout (see below) — it isn't
decorative, it's structural.

Consequences that follow from this direction, and must hold everywhere:

- **Sharp corners only.** No `border-radius` anywhere except perfect circles
  (status dots). This is deliberate — rounded cards read as generic SaaS;
  sharp rectangular blocks read as a printed page. Don't round a card or
  button "to soften it" — that breaks the signature.
- **One accent color, used sparingly.** `--accent` (teal) marks the active
  tab, focus rings, and the one interactive highlight. Status meaning is
  carried by the semantic palette (`--now`/`--next`/`--later`/`--stop`/`--ok`/
  `--ship`), not by the accent. Don't reach for a second "pop" color.
- **Depth strategy: borders + one soft card shadow, not both everywhere.**
  Most structure (`.sect`, `.wk`, `.wcard`) is borders/dotted-rules only —
  no shadow. `.pcard` is the one elevated surface (1px ring + soft shadow,
  because it's literally a card stacked on the board). Don't add shadows to
  flat sections, and don't add borders *and* heavy shadows to the same
  element.
- **Typography carries the hierarchy, not color.** Newsreader (serif,
  display/lede/headings) vs. Instrument Sans (UI body) vs. IBM Plex Mono
  (all-caps tracked labels, numbers, meta) — the font *is* the signal for
  "this is a headline" vs. "this is a label" vs. "this is data." Don't
  introduce a fourth typeface or use mono for body prose.

## Tokens

Defined once in `:root`, overridden for dark mode under both
`@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"]`. Every
color used in the CSS traces back to one of these — no inline hex.

| Token | Role |
|---|---|
| `--ground` / `--surface` / `--surface-2` | page background / card background / recessed background |
| `--ink` / `--ink-2` / `--ink-3` | primary text / secondary text / labels & meta (mono, uppercase, tracked) |
| `--line` / `--line-2` | standard border / softer separator |
| `--accent` | the one interactive/active color |
| `--now` / `--next` / `--later` / `--stop` | the four board categories — also used for status text and the timeline bands (`--now-bg`/`--next-bg`/`--later-bg`) |
| `--ok` / `--ship` | two extra semantic states (done / shipped) used only in status dots and signal text |
| `--track` | meter/progress-bar background |
| `--shadow` | the one card-elevation shadow, tuned per theme |

**`--ink-3` contrast is load-bearing.** It's the color of every `.k` label,
timestamp, and meta note on the page — used dozens of times. Light mode is
`#5E6E78` on `#EEF1F2` ground (~4.6:1, WCAG AA for small text). If this ever
gets touched, re-check contrast against the ground before committing —
the original `#7C8B95` measured ~3.1:1 and failed AA; that's why it changed.

**Only define tokens that get used.** `--accent-soft`, `--ok-bg`,
`--stop-bg`, `--ship-bg` existed in all three theme blocks and were never
referenced — removed. Don't add a `*-bg` or `*-soft` variant "for
completeness"; add it when a rule actually needs it.

## Spacing & density

- Base unit: 2px grid, built up in multiples (6, 10, 14, 18, 22, 32...).
  Section-level rhythm (`.sect`, `.wk`) uses 32px vertical padding between
  blocks; card interiors sit around 16–18px; tight clusters (icon+label,
  stat+sub) sit around 4–9px.
- Density is **tool-tight, not airy** — this is an internal working doc,
  not a brochure. Hold to the existing values rather than loosening padding
  "to give it room."
- The hanging-label spine (136px label column + 34px gap, used by `.sect`
  and `.wk`) is the one layout signature reused across Overview and The
  5:15. If a new section needs a label + content pattern, reuse this grid
  rather than inventing a new column width.

## Type scale

Base 14px body. Scale is not a strict ratio — it's tuned per role:
`caption/meta 9.5–11px (mono, tracked .11–.15em, uppercase)` ·
`body 13–14px` · `h/card-name 16–19px (serif, 500)` · `lede 19–23px (serif,
400)` · `display 30–40px (serif, 400, clamp)`.

Headings and prose both get optical-sizing treatment:
- `.display`/`.lede`/`.pc-name` → `text-wrap: balance`
- Body copy (`.body`, `.dtext`, `.wc-b`, `.foc p`, `.flag p`, `.prow .pd`) →
  `text-wrap: pretty` (orphan control)
- Large serif headings carry slightly negative letter-spacing
  (-0.01 to -0.018em); mono labels carry positive tracking (+0.11 to +0.15em)

Any dynamic/tabular number gets `font-variant-numeric: tabular-nums` —
already on `.fig`, `.goal-count`, `.col-c`, `.kid-due`, `.pc-live .pct`.
Add it to any new numeric display too.

## States & motion

- Every real button (`.tab`, `.expand`, `.movebtn`, `.outbtn`) has hover,
  active (press feedback `transform: scale(.97)`), and focus-visible
  states, with `color`/`border`/`background`/`transform` transitions at
  `.1–.15s ease`. Don't ship a new interactive element without all three.
- `.tab` buttons use real roving `tabindex` + Left/Right/Home/End keyboard
  nav (see the `keydown` listener in the script) because they declare
  `role="tab"` — that role implies the ARIA APG tablist behavior contract,
  not just a label. If you add a tab, it inherits this for free; if you add
  a *new* tablist-like control, wire the same pattern rather than relying
  on click-only.
- Interactive elements with a visually small target (`.outbtn`, `.expand`,
  `.movebtn`) get invisible hit-area padding offset with a matching negative
  margin, so the click target grows without shifting layout.
- Respect `prefers-reduced-motion` — already handled globally.

## Key component patterns

- **Hanging-label section** (`.sect`, `.wk`) — 136px `.k` label column +
  34px gap + content. Reused for Overview's "This week"/"Year targets"/
  "In focus" and for every week in The 5:15.
- **Ledger stat** (`.led`) — `.k` label → `.fig` (30px/600, tabular-nums,
  `--accent` when it's the lead figure) → `.sub` one-line context. No
  icons, no colored backgrounds — the number does the work.
- **Status dot + label row** (`.prj`, `.prow .pn`) — 6px circle in a
  semantic color, name, right-aligned mono status text.
- **Board card** (`.pcard`) — the one shadow+border surface. Header (name,
  window, "doing now" line) → optional progress/live-sync strip → footer
  (expand toggle, move-category button) → detail panel (editable ask,
  next step, blocker, meeting-decision textarea) that slides in via
  `hidden`, not animated (the board fully re-renders on toggle, so a CSS
  transition wouldn't play without a larger restructure — known
  limitation, not an oversight).
- **Outcome buttons** (`.outbtn`) — three-state toggle group
  (Agreed/Parked/Declined) using `aria-pressed`, 9px/12px padding (sized up
  from the original 6px/10px for touch-target reasons — this page has a
  mobile breakpoint).

## Known trade-offs (don't "fix" these without re-checking)

- Button/touch targets are sized for a dense internal tool, not full
  WCAG 44px — bumped where they were egregiously small (`.outbtn`), left
  compact elsewhere by design.
- The card detail panel doesn't animate open/closed because the board
  re-renders the whole column on every toggle. Animating it properly needs
  a toggle that patches the DOM instead of re-rendering — out of scope for
  a polish pass.

## Still true from the original brief

- Two data sources: `data.json` (written daily by `sync.py`, never
  hand-edited) and `content.json` (hand-maintained prose/structure,
  `sync.py` never touches it). Don't blur this line when adding fields.
- Page-local edits (asks, decisions, outcome marks, card category moves)
  persist to `localStorage` only — never assume they're visible to anyone
  else opening the link.

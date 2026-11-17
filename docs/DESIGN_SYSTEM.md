# Design System — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
**Status:** Palette and fonts proposed and contrast-checked; the owner approves visually in Phase 1 (`[CONFIRM]`). Agents must use these tokens, never ad-hoc colours or sizes.

---

## 1. Design Direction

| | Patient app | Doctor app |
|---|---|---|
| Style | Soft, card-based, calm (inspired by cycle-tracker apps like Clue) | Clean, clinical, information-dense |
| Mood | Warm, reassuring, gentle | Focused, trustworthy, efficient |
| Primary layout | Phone first | Laptop first |

**Principles**
- Safety first: warning messages are always visible, high-contrast, and never decorative.
- Calm by default: no alarming colours unless something is actually urgent.
- One accent family: soft lavender in both apps; the patient side is warmer, the doctor side cooler.
- Never rely on colour alone: every status has a text label and an icon.
- Educational content, the patient's own data and doctor-confirmed information always look different (Journey D15).

---

## 2. Brand

- **Name:** Alovia
- **Logo:** a simple letter mark "A" in white on a lavender circle (patient: `--color-primary` patient light; doctor: doctor primary). Wordmark "Alovia" in the heading font. `[OPEN]` a real logo later.
- **Voice:** patient side: warm, short sentences, no jargon, never alarming unless urgent. Doctor side: precise, neutral, clinical terms allowed.

---

## 3. Colour tokens

Implemented as CSS variables in `frontend/packages/ui/src/styles/tokens.css`, mapped to Tailwind. Each app sets `data-app="patient"` or `data-app="doctor"`; each theme sets `data-theme="light"` or `"dark"` (default follows the system setting; the user can override).

### 3.1 Patient app

| Token | Light | Dark |
|---|---|---|
| `--color-primary` (buttons, links) | `#6B4FBB` | `#B9A6F2` |
| `--color-on-primary` (text on primary) | `#FFFFFF` | `#1A1430` |
| `--color-primary-soft` (tinted cards, chips) | `#EFE9FB` | `#2C2440` |
| `--color-accent` (decorative only, never text) | `#F6C9B4` (soft peach) | `#5A3F38` |
| `--color-bg` | `#FBF8FF` | `#17141F` |
| `--color-surface` | `#FFFFFF` | `#221D2E` |
| `--color-text` | `#2B2440` | `#EEEAF6` |
| `--color-text-muted` | `#5E5873` | `#B4ACC8` |
| `--color-border` | `#E6E0F2` | `#3A3350` |

### 3.2 Doctor app

| Token | Light | Dark |
|---|---|---|
| `--color-primary` | `#4F3FA8` | `#A79BF0` |
| `--color-on-primary` | `#FFFFFF` | `#14112B` |
| `--color-primary-soft` | `#ECEAF8` | `#262344` |
| `--color-secondary` (charts, secondary actions; teal kept from the test frontend) | `#25606D` | `#5FB3C2` |
| `--color-bg` | `#F6F7FB` | `#12151D` |
| `--color-surface` | `#FFFFFF` | `#1B1F2A` |
| `--color-text` | `#1E2230` | `#E8EAF2` |
| `--color-text-muted` | `#4E566A` | `#A3AABB` |
| `--color-border` | `#DDE1EA` | `#2E3445` |

### 3.3 Status colours (both apps)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-urgent` (L1, errors) | `#B42318` | `#F97066` | Level 1 red flag, destructive actions, errors |
| `--color-caution` (L2, warnings) | `#93370D` | `#FDB022` | Level 2 red flag, warnings |
| `--color-success` | `#1F6B4A` | `#6CC79C` | Saved, completed |
| `--color-info` | = primary | = primary | Neutral information |

Status backgrounds use the same hue at about 10% opacity, with the text in the full colour.

### 3.4 Contrast check (WCAG 2.1 AA, computed 2026-11-16)

| Pair | Ratio |
|---|---|
| Patient light: text on bg | 13.98 |
| Patient light: muted text on bg | 6.40 |
| Patient light: white on primary (button) | 6.07 |
| Patient light: primary link on bg | 5.77 |
| Patient light: urgent / caution / success on white | 6.57 / 7.52 / 6.44 |
| Doctor light: text / muted on bg | 14.79 / 6.85 |
| Doctor light: white on primary / on secondary | 8.05 / 7.06 |
| Patient dark: text / muted on bg | 15.34 / 8.37 |
| Patient dark: button text on primary / primary on bg | 8.26 / 8.48 |
| Patient dark: urgent / caution on bg | 6.52 / 9.87 |
| Doctor dark: text / muted on bg | 15.19 / 7.84 |
| Doctor dark: button text on primary / secondary on bg | 7.50 / 7.57 |

| Dark success on bg (patient / doctor) | 8.90 / 8.94 |
| Doctor dark: urgent / caution on bg | 6.55 / 9.92 |
| Doctor light: urgent on bg | 6.14 |
| Patient light: primary / text on primary-soft | 5.12 / 12.40 |
| Patient dark: text on primary-soft | 12.37 |
| Dark: urgent button text (`--color-bg`) on urgent, patient / doctor | 6.52 / 6.55 (same pair as urgent on bg; white on dark urgent would fail) |

All pairs pass AA for normal text (≥ 4.5). Any new colour pair must be checked before use and added here.

---

## 4. Typography

Fonts are **self-hosted** through `@fontsource` packages (no Google Fonts CDN, so no third-party requests). Both are SIL Open Font Licence.

| | Patient app | Doctor app |
|---|---|---|
| Heading + body | **Nunito** (rounded, friendly) | **Inter** (clear, dense) |
| Numbers in tables/charts | Nunito, tabular figures | Inter, tabular figures |

| Style | Size / weight / line height |
|---|---|
| H1 | 28px / 700 / 1.25 (32px on ≥ 1024px) |
| H2 | 22px / 700 / 1.3 |
| H3 | 18px / 600 / 1.35 |
| Body | 16px / 400 / 1.5 (never smaller for patient body text) |
| Small | 14px / 400 / 1.45 |
| Caption | 12px / 500 / 1.4 (doctor tables only; never for safety text) |

---

## 5. Spacing
Base unit **4px**. Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96 (Tailwind default spacing). Patient cards use 16–24px padding; doctor tables use 8–12px cell padding.

## 6. Border radius
| Token | Patient | Doctor |
|---|---|---|
| Small | 8px | 6px |
| Medium | 16px | 8px |
| Large | 24px | 12px |
| Pill | 9999px | 9999px |

## 7. Shadows
Small: `0 1px 2px rgb(0 0 0 / 0.06)`. Medium: `0 4px 12px rgb(0 0 0 / 0.08)`. Large (dialogs): `0 12px 32px rgb(0 0 0 / 0.12)`. In dark mode, use borders instead of shadows.

## 8. Buttons
- **Primary:** `--color-primary` background, `--color-on-primary` text, medium radius, min height 44px (touch target), clear verb label ("Save symptom", not "OK").
- **Secondary:** surface background, primary text, 1px primary border.
- **Danger:** urgent colour; always followed by a confirmation dialog.
- **Disabled:** 40% opacity, `aria-disabled`, still readable.
- **Loading:** label stays, spinner inside, button disabled.

## 9. Inputs
Label always visible above the field (no placeholder-only labels). Focus: 2px primary outline + 2px offset. Error: urgent-coloured border, message below with icon, `aria-describedby`. Units shown inside the field on the right (e.g. "mmol/mol").

## 10. Cards
Patient: surface, large radius, 20px padding, small shadow (light) / border (dark). Doctor: surface, medium radius, 16px padding, border. **Content-type marking (Journey D15):** educational content = primary-soft background with a small "Learn" label and source line; patient's own data = surface with "You logged"; doctor-confirmed = surface with a doctor icon and "From your doctor".

## 11. Navigation
- **Patient, phone:** bottom nav bar (Home, Calendar, Log, Appointments, More), urgent button pinned top-right on every screen; notification bar under the header.
- **Patient, laptop:** left side bar with the same items.
- **Doctor:** left side bar (Home, Patients, Genetic review, Rule review, Admin [admin only]); top bar with search and theme toggle; collapses to a menu on small screens.

## 12. States
Loading, Empty, Error, Success, Disabled as defined in `docs/UX_FLOWS.md` §0.

## 13. Icons and imagery
- UI icons: **Lucide** (ISC licence), outline, 20px default (24px in patient nav).
- Size comparisons: **Microsoft Fluent Emoji** (MIT).
- Month illustrations: openly licensed drawings only (Journey spec §7.1); all credits in `docs/legal/CREDITS.md`.
- Every meaningful image has alt text; decorative images use `alt=""`.

## 14. Motion
Framer Motion (`motion` package) for gentle float, swipes and week transitions; Lottie only for decorative moments. Durations 150–300ms. **Respect `prefers-reduced-motion`** and the in-app "Reduce motion" setting. No motion on L1 screens, and no heartbeat-like animation anywhere.

## 15. Responsive design
Tailwind breakpoints: phone < 640px, small tablet 640–767px, tablet 768–1023px, laptop ≥ 1024px. Patient app designed at 375px first; doctor app at 1280px first, usable down to 375px (tables become cards). Layout details may change during build `[CONFIGURABLE]`, but must work at 375px and 1280px.

## 16. Accessibility (WCAG 2.1 AA target)
Semantic HTML; all interactive elements reachable and usable by keyboard; visible focus; labels on every input; colour never the only signal; minimum touch target 44×44px; language `lang="en"`; automated checks with axe in Playwright tests (`docs/TESTING.md`).

## 17. Component library
`shadcn/ui` components (built on Radix primitives, which handle keyboard and screen-reader behaviour), copied into `frontend/packages/ui` and styled with these tokens. Do not add other UI kits.

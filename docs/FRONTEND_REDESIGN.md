# Alovia Frontend Redesign: Build Brief for Claude Code

**Version:** 1.0 · **Date:** 2026-11-21 · **Owner:** Raheem
**Replaces:** `claude/ui_inspiration_analysis.md` (short notes). This file merges that analysis, the full Clue teardown, and every owner decision made on 2026-11-21.
**Status:** Decisions marked **[OWNER]** are final. Items marked **[PROPOSAL]** are mine and need the owner's yes. Items marked **[OPEN]** are not decided.

---

## 0. How to use this file

Read in this order: `CLAUDE.md`, `docs/DESIGN_SYSTEM.md`, `docs/modules/` Journey and Symptom specs, then this file.

**Precedence when documents or skills disagree (highest first):**
1. Safety rules and wording rules in the Journey and Symptom specs, and `CLAUDE.md`.
2. This file (it records the owner's newest decisions).
3. `docs/DESIGN_SYSTEM.md` (tokens, components, accessibility).
4. The design skills in section 3. A skill never overrides items 1 to 3.

**Where this file changes an older document, update that document too** and add a line to `docs/DECISIONS.md` (see section 15). Do not leave two versions of the same rule.

**No new dependency without asking the owner** (`CLAUDE.md`). Where this file already approves a package it says so. Anything else: list it, say why, wait.

---

## 1. What this redesign is

A full frontend redesign of both apps, keeping the current colour palette, so they feel like a premium product while staying calm and safe for pregnancy use.

| Area | Decision | Source |
|---|---|---|
| Patient app priority | **Mobile web app first** (installable PWA). It must also look properly designed on desktop, not a stretched phone | **[OWNER]** |
| Doctor app priority | **Desktop first.** Must also work well on a phone | **[OWNER]** |
| Colour | **Keep the current palette** (`DESIGN_SYSTEM.md` section 3). Only add the ring tokens in section 5.2 | **[OWNER]** |
| Patient first screen | **The ring with the baby illustration in its centre** is the first thing seen | **[OWNER]** |
| Patient navigation | Bottom tab bar on phone and tablet, left sidebar on desktop (section 6) | Skills guidance + `DESIGN_SYSTEM.md` section 11 |
| Calendar | Shows the symptoms the patient has logged, day by day | **[OWNER]** |
| Look | Expensive and modern: current components, refined type, strong spacing, restrained motion | **[OWNER]** |
| Images | Use the supplied doctor-approved month illustrations (section 12) | **[OWNER]** |
| Tooling | Use six design skills together (section 3) | **[OWNER]** |

**Reference apps:** two screen recordings of Clue (a cycle tracker). We borrow ideas, not looks. Alovia must not be mistaken for Clue. The full breakdown is in Appendix A.

---

## 2. Rules that never bend

These come from the specs. A skill, a component library or a design preference may not break them.

**Safety and wording**
- Urgent button "I have an urgent symptom" is **always visible** on every patient screen. Urgent advice never competes with banners, promos or animation.
- Red-flag levels (L0, L1, L2) are computed **on the backend**. The frontend only shows the level and the message key it receives.
- Clinical text comes only from `msg_*` keys or knowledge-base content with a source. Do not write medical wording yourself. Use obvious placeholders and mark `[CONFIRM AT REVIEW]`.
- Never write "your baby weighs", "normal", or "nothing to worry about". Baby content is always "a typical baby at this stage".
- No heartbeat animation or anything that looks like live monitoring (Journey D4).
- No motion at all on L1 screens. No celebratory wording after an L1 or L2 check-in.
- Baby content, the ring and the month image disappear when the pregnancy ends (Journey section 11.3). No Lottie after the end.
- No ads, banners, modals-on-launch, padlocks or paywalls. Alovia locks no health content.
- Educational content, the patient's own data and doctor-confirmed content must look different (Journey D15, `DESIGN_SYSTEM.md` section 10).

**Colour and accessibility**
- Red (`--color-urgent`) is reserved for L1 red flags, errors and destructive actions. Never for trimesters, decoration or categories.
- Colour is never the only signal. Every status has a text label and an icon.
- WCAG 2.1 AA. Text 4.5:1, large text and UI shapes 3:1. Any new colour pair is checked and added to the contrast table before use.
- Touch targets at least 44 by 44 px, at least 8 px apart.
- Body text for patients is never below 16 px. Input text is at least 16 px (prevents iOS zoom on focus).
- Respect `prefers-reduced-motion` and the in-app "Reduce motion" setting everywhere.

**Known exception [OWNER]:** the ring marker has **no keyboard path**. This is a recorded exception to `DESIGN_SYSTEM.md` section 16. Compensations are in section 7.2.

---

## 3. The design skills and how to use them together

> The slash names below come from each skill's public repository and registry page. They were **not** visible in the owner's claude.ai account skill list, so they are most likely installed in Claude Code. **First step: run `/skills` in Claude Code, compare with this table, and install anything missing.** Several registries publish different skills with the same short name (especially `unslop` and `playwright`), so check the author.

### 3.1 The toolkit

| # | Skill | Author and install | Slash command(s) | What we use it for |
|---|---|---|---|---|
| 1 | **Emil Kowalski design engineering skills** | `emilkowalski/skills` · `npx skills@latest add emilkowalski/skills` | `/emil-design-eng` (main), `/animate`, `/choreograph`, `/gestures`, `/mobile-native`, `/apple-design`, `/review-animations`, `/improve-animations`, `/animation-performance`, `/find-animation-opportunities`, `/remove-animations`, `/break-ui`, `/prototype`, `/pick-ui-library`, `/learn-taste`, `/ask-emil` | Motion rules, the ring drag and sheet gestures, native feel on phones (sticky hover, tap delay, safe areas), testing with worst-case data |
| 2 | **Impeccable** | `pbakaus/impeccable` · `/plugin marketplace add pbakaus/impeccable` or `npx skills add pbakaus/impeccable --skill impeccable` | `/impeccable` with sub-commands: `init`, `document`, `extract`, `shape`, `craft`, `critique`, `audit`, `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize`, `live` | The design workflow: plan a screen, build it, critique it, audit it, polish it. Also empty states (`onboard`), edge cases (`harden`), devices (`adapt`), type (`typeset`), spacing (`layout`), copy (`clarify`) |
| 3 | **21st.dev** | `21st-dev/magic-mcp` · MCP: `npx @21st-dev/cli@latest init --client claude` (API key from 21st.dev/mcp) · skill: `npx skills add https://github.com/21st-dev/magic-mcp --skill 21st-ui` | `/21st-ui` (skill). MCP tools: `search`, `get_component` (also `generate`, `search_logo`) | Finding well-made shadcn-compatible components to adapt (bottom nav, sheets, calendar, stat tiles, data tables) |
| 4 | **heydamir unslop** | `heydamir/unslop` · `claude plugin install unslop --marketplace heydamir/unslop` | `/unslop <what to review>`; if the name collides, `/unslop:unslop` | The anti-"AI look" pass on every finished screen: audit, direction, then fixes to spacing, colour, icons, copy, type, layout, details, motion |
| 5 | **Taste skill** | `Leonxlnx/taste-skill` · `/plugin marketplace add Leonxlnx/taste-skill` then `/plugin install taste-skill@taste-skill`, or `npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"` | `/design-taste-frontend` (redesigning existing projects is now part of this skill) | Premium typography, spacing, rhythm and restraint. Use it for polish and hierarchy, not for flashy layouts |
| 6 | **Playwright** | Use the Playwright skill that is installed; the common one is `playwright-best-practices`. Playwright and axe are already in `docs/TESTING.md` | `/playwright-best-practices` (confirm with `/skills`) | Multi-viewport tests, accessibility checks, layout-shift and touch-target checks, visual snapshots |

Also use the **shadcn skills** (shipped with shadcn CLI v4) when adding or changing shadcn components. They know Radix and Base UI APIs.

### 3.2 How they work together: one pipeline per screen

Run these in order for **every** screen. Do not skip the safety review at the end.

| Step | What | Skill | Output |
|---|---|---|---|
| 0 | Once only: `/impeccable init` using the answers in this file. Create root `PRODUCT.md`. Create root `DESIGN.md` as a **thin file that points to `docs/DESIGN_SYSTEM.md`** and holds learned rules. Never let a skill write a second palette | Impeccable, `/learn-taste` | `PRODUCT.md`, `DESIGN.md` |
| 1 | Plan the screen: layout at 375 and 1280, states, copy keys | `/impeccable shape` | A short plan in the PR description |
| 2 | Find existing parts before writing new ones: shadcn first, then 21st.dev (`search`, then `get_component`), then custom | `/21st-ui`, shadcn skills | Components adapted to our tokens |
| 3 | Build the screen | `/impeccable craft` + `/design-taste-frontend` for type, spacing, hierarchy | Working screen |
| 4 | Motion, gestures, native phone feel | `/emil-design-eng`, `/gestures`, `/mobile-native`, `/choreograph`, then `/review-animations` and `/animation-performance` | Reviewed motion |
| 5 | Worst-case data: very long names, empty lists, 99+ counts, 12-week-old data, Hindi or Telugu text if used | `/break-ui` | Fixed overflows |
| 6 | Remove the generic look | `/unslop <screen>` | Fewer tells, same palette |
| 7 | Review | `/impeccable critique`, `/impeccable audit`, `/impeccable adapt`, `/impeccable clarify` | Fix list, applied |
| 8 | Finish | `/impeccable polish`, `/impeccable harden`, `/impeccable onboard` for empty states | Shippable screen |
| 9 | Prove it | `/playwright-best-practices`: tests in section 13 | Green tests and screenshots |

### 3.3 Limits on each skill (they were written for marketing sites; this is a clinical app)

| Skill or command | Limit |
|---|---|
| `/impeccable bolder`, `overdrive`, `delight` | **Never** on the Log, warning-signs, advice, urgent, pregnancy-end or loss screens. On other screens only with owner sign-off |
| `/impeccable colorize` | May not introduce a new hue. The palette is fixed (section 5) |
| `/unslop` | It dislikes purple. **Keep the brand lavender**, flat, with no gradients or glows. Remove only: gradients, glows, emoji labels, shouty copy, uneven spacing, generic card piles |
| `/design-taste-frontend` | Written for landing pages. Use it for type, spacing and polish. Keep layout variance and motion intensity low. The ring screen is not a hero section |
| `/prototype` (Emil) | Dev only, to compare two or three variants. Never ship the switcher |
| `/21st-ui` `generate` | Do not use. Pull only existing components with `search` and `get_component`. Check each component's licence and strip any dependency we have not approved |
| `/21st-ui` `search_logo` | Do not use (no third-party logos in Alovia) |
| `/impeccable init`, `/learn-taste` | Both write `DESIGN.md`. There must be **one** root `DESIGN.md`, pointing to `docs/DESIGN_SYSTEM.md` |
| Any skill that suggests a new UI kit or font | Ask the owner. `DESIGN_SYSTEM.md` section 17 forbids other UI kits |

### 3.4 First message to give Claude Code

> Read `CLAUDE.md`, `docs/DESIGN_SYSTEM.md`, the Journey and Symptom specs, then `docs/FRONTEND_REDESIGN.md`. Run `/skills` and tell me which of the six toolkit skills are missing. Then do step 0 of section 3.2, and stop for my review before building any screen.

---

## 4. Stack and "latest components" rules

The stack is already fixed in `ARCHITECTURE.md`. Keep it; use its current features.

| Layer | Use | Notes |
|---|---|---|
| Framework | React 19 + TypeScript + Vite (existing) | Remove `forwardRef` where shadcn's v4 components no longer need it |
| Styling | **Tailwind CSS v4**, CSS-first: tokens live in `@theme` in `tokens.css` | Keep the `data-app` and `data-theme` switches |
| Components | **shadcn/ui on Radix** (existing, `DESIGN_SYSTEM.md` section 17) | New shadcn projects now default to Base UI, but Radix is still fully supported. **Stay on Radix.** Do not migrate; it adds risk for no user benefit. Use the shadcn CLI v4 (`diff`, `view`, `add --dry-run`) to bring components up to date |
| Icons | Lucide, outline, one stroke width everywhere (1.75 px) | 24 px in patient nav, 20 px elsewhere |
| Motion | `motion` package (import from `motion/react`) | CSS transitions first; Motion for drag, springs, layout and presence |
| Charts | Recharts (doctor and patient trends) | Accessible colours, direct labels, "view as table" |
| Calendar | `react-day-picker` or a custom grid | Custom grid if the markers, week gutter or sticky headers fight the library |
| Toasts | shadcn Sonner | Only for non-clinical confirmations |
| Fonts | Self-hosted `@fontsource-variable/*` (section 5.3) | **Approved by this file**; confirmed visually by the owner 2026-11-21 (DEC-111) |
| Browser features | `100dvh`, `env(safe-area-inset-*)`, `viewport-fit=cover`, container queries, `:focus-visible`, `touch-action: manipulation`, `overscroll-behavior`, `text-wrap: balance`, `@media (hover: hover)` | All widely supported |
| Drag-to-dismiss sheets | Radix `Sheet` first. If swipe-to-dismiss is wanted, ask the owner before adding `vaul` | New dependency rule |

---

## 5. Design tokens

### 5.1 Palette: unchanged

Use `DESIGN_SYSTEM.md` section 3 exactly. Patient: lavender `#6B4FBB` primary, peach `#F6C9B4` decorative accent, `#FBF8FF` background. Doctor: `#4F3FA8` primary, teal `#25606D` secondary, `#F6F7FB` background. Status colours unchanged. Light and dark themes unchanged.

**Premium look comes from structure, not new colour:** warm layered surfaces (card on background), 1 px hairline borders in `--color-border`, soft shadows from section 7 of the design system, large whitespace, one hero element per screen, flat fills only (no gradients or glows).

### 5.2 New tokens: ring arcs (contrast-checked 2026-11-21)

The ring uses three steps of the primary colour, darker as the pregnancy advances. Each arc is at least 3:1 against both the background and the card surface. **Add these to the DS contrast table.**

| Token | Patient light | On bg `#FBF8FF` | Patient dark | On bg `#17141F` |
|---|---|---|---|---|
| `--color-arc-1` (trimester 1, weeks 0 to 13) | `#907BCC` | 3.39 | `#8073A8` | 4.27 |
| `--color-arc-2` (trimester 2, weeks 14 to 27) | `#8169C5` | 4.20 | `#9989C8` | 5.85 |
| `--color-arc-3` (trimester 3, weeks 28 to 42) | `#6B4FBB` | 5.77 | `#B9A6F2` | 8.48 |

On the card surface the dark-theme ratios are 3.85, 5.27 and 7.64; the light-theme ratios are 3.56, 4.41 and 6.07. All pass the 3:1 rule for graphics.

Other ring tokens: `--color-track` = `--color-border` (decorative base; the ring is also described in text). Marker bubble: white fill (`--color-surface`), 2 px `--color-primary` outline, text `--color-text`. Today dot: `--color-primary`.
The doctor app does not use the ring. Its chart colours stay `--color-primary` and `--color-secondary`.

### 5.3 Typography [OWNER asked for an "expensive" look; **decided 2026-11-21, DEC-111**: Fraunces + Figtree, Geist]

The design system currently says Nunito (patient) and Inter (doctor). Both are fine but common. Proposal:

| | Patient app | Doctor app |
|---|---|---|
| Display (ring headline, H1, big numerals) | **Fraunces** (variable, soft serif) | **Geist** |
| Body and UI | **Figtree** (variable) | **Geist** |
| Numbers in tables and charts | Figtree, `tabular-nums` | Geist, `tabular-nums` |

Rules:
- Safety, urgent and clinical-message text is **always the sans**, never the serif.
- Use CSS variables `--font-display` and `--font-body`, so swapping fonts is a one-line change.
- Self-host with `@fontsource-variable/fraunces`, `/figtree`, `/geist`. Latin subset, `font-display: swap`, preload only the files used above the fold, and set fallback metrics to avoid layout shift.
- Keep the DS size scale (H1 28 px, 32 px on desktop; H2 22; H3 18; body 16; small 14; caption 12 for doctor tables only). Add one fluid size for the ring headline: `clamp(1.75rem, 1.4rem + 1.6vw, 2.25rem)`.
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs, `font-optical-sizing: auto`, display letter-spacing about -0.01em.
- **Before locking, Claude Code renders Home at 375 px in two versions** (Fraunces + Figtree vs the current Nunito) and shows both to the owner. If the owner prefers Nunito or Inter, change the two variables and stop. Run `/impeccable typeset` for the detail pass.

### 5.4 Shape, spacing, motion

- Spacing: 4 px base; scale 4, 8, 12, 16, 24, 32, 48, 64, 96. Patient cards 20 to 24 px padding.
- Radius, shadow, buttons, inputs, cards: as in the design system (sections 6 to 10).
- Motion tokens: fast 150 ms, base 200 ms, slow 300 ms. Entering and moving elements use a strong ease-out (`cubic-bezier(0.23, 1, 0.32, 1)`); the ring marker release uses a short spring. Pressed buttons scale to about 0.97. Hover styles only inside `@media (hover: hover)`. Animate `transform` and `opacity` only.
- Reduced motion: no float, no spring, no cross-fade; changes are instant.

---

## 6. Responsive strategy

Tailwind breakpoints (design system section 15): phone below 640, small tablet 640 to 767, tablet 768 to 1023, laptop 1024 and above. **Design patient at 375 first, doctor at 1280 first.** Also test 360, 390, 430, 768, 1024, 1440.

| | Patient app | Doctor app |
|---|---|---|
| Below 768 | Bottom tab bar, single column, full-screen sheets | Top bar with menu button (opens a sheet), single column, tables become cards |
| 768 to 1023 | Bottom tab bar, two-column where it helps (ring left, cards right on landscape), centred sheets | Collapsed icon sidebar (72 px), tables with fewer columns |
| 1024 and above | **Left sidebar**, content max width about 1200, ring column sticky on the left, cards on the right | Full sidebar (240 px), dense tables, side-by-side panels |
| Max content width | 1200 px, centred | 1440 px, centred |

**Rules for both apps**
- No horizontal page scroll at 360 px. Test it.
- Never show a phone-width column floating in the middle of a desktop screen. Desktop gets a real layout.
- Use container queries for components that appear in different widths (cards, tables, the ring block).
- Bottom bars and sticky bars add `env(safe-area-inset-bottom)` and the page adds matching bottom padding.
- Hover is never the only way to reach anything.

---

## 7. Patient app (mobile first)

### 7.1 Home: ring and baby image first

**Order on phone (top to bottom).** Everything in the first six rows must be visible without scrolling at 375 by 667.

| # | Block | Notes |
|---|---|---|
| 1 | Top bar | Logo mark left, urgent button right (always visible, 44 px high, urgent variant, text "Urgent" with icon on phone and the full label on desktop). Height 56 px |
| 2 | Notification bar | Only when there is something to show. Loaded together with Home data so it never pushes the ring after first paint (section 11) |
| 3 | **Ring with baby image in the centre** | About 300 px wide at 375 (full width minus 32 px margins, max 340 px). Details in 7.2 |
| 4 | Headline block | "N weeks, D days pregnant" in the display font, then "X days to go · Due date" and the word "estimate" when `due_date_source = lmp_estimate` (Journey 4.3, 6.1) |
| 5 | Preview chip | Only while scrubbing: "Viewing week 30 · Back to today" |
| 6 | Size comparison line | "About the size of a [object]" with the Fluent Emoji icon, typical value and source. Hidden when no sourced value exists |
| 7 | Quick log card | Shortcut to log; shows "logged today" if a check-in exists |
| 8 | This stage | Learn card (primary-soft, "Learn" label, source line) with "Read more" |
| 9 | This week's summary | "You logged" next to "Common at this stage", visually different |
| 10 | Next appointment | Only if one exists |
| 11 | Status cards | New doctor note, result available, genetic check status, each only when relevant |
| 12 | Bottom tab bar | Fixed |

**Home on desktop (1024 and above).** Left sidebar. Two columns: left column (about 420 px, sticky) holds the ring, headline, preview chip and size line; right column holds rows 7 to 11 as a card grid. The top bar keeps the urgent button on the right.

**States (Journey 4.5):** no due date shows the onboarding card only (ring hidden; quick log and urgent button remain); active weeks 0 to 39 normal; 40 to 41 add `msg_past_due_date`; 42 and over: ring marker stops at the end, counter stops, `msg_beyond_42_weeks`, no new weekly content; any ended status shows the section 11 screens and no ring or baby content.

**First paint:** show a static ring track and a round placeholder immediately (skeleton), then fill. No blank spinner screens anywhere.

### 7.2 The ring, in detail

**Geometry**
- SVG, viewBox 320 by 320, ring radius 140, stroke about 22. Starts at 12 o'clock and runs clockwise.
- Three arcs separated by 3 degree gaps. Arc lengths are proportional to the weeks in each trimester: 14, 14 and 15 week slots (weeks 0 to 13, 14 to 27, 28 to 42).
- Colours: `--color-arc-1`, `-2`, `-3`. Elapsed weeks are drawn at full strength; weeks still to come are the same colours at 35 percent opacity (decorative; the text carries the facts).
- Trimester names appear as text: the headline block states the current trimester ("Second trimester") and the ring has an `aria-label` describing all three. A small legend row ("1st · 2nd · 3rd trimester") sits under the ring on desktop only.
- **Marker:** a 44 px white bubble with a primary outline showing "Wk 24" (14 px). It sits on the ring at today's position. A small **today dot** stays at today's position while the marker is dragged away.
- Cap: the ring ends at week 42.

**Centre of the ring**
- The **month illustration** (7.3), in a round surface disc, about 58 percent of the inner diameter.
- Under it, one caption line: "Month 4 · now" (14 px). Always the current month, never the scrubbed one.

**Scrubbing [OWNER: option A with guardrails]**
- The marker can reach week 0 up to the 42-week end, past and future, by dragging in either direction.
- Guardrails: (a) any week other than today shows the preview chip "Viewing week N · Back to today"; (b) a scrubbed week is **read-only**: no log, warning or action buttons, and it never changes any risk status or red-flag rule; (c) the today dot stays visible, and the marker returns to today when the screen is left and reopened.
- While scrubbing, the headline block shows the viewed week ("Week 30") and the date that week starts, and hides "days to go". A link line "Read about week 30" opens that week's content item with its source. **[OWNER 2026-11-21, DEC-114: opens the month page that holds that week; no week page yet.]**
- **The month illustration and its caption do not change while scrubbing.** [OWNER]
- Compute the headline from `previewDay` synchronously (no animation lag), so the week, date and text never disagree.

**Haptics [OWNER]**
- One short pulse per day change while dragging (`navigator.vibrate(8)`), only where supported. Android browsers support it; iPhones do not, so those users get no pulse and the ring still works.
- Never on L1 screens, never when reduced motion is on, never rhythmic or repeating without a drag (Journey D4).
- At both ends the marker stops with the same single pulse.

**Accessibility compensation for the drag-only decision [PROPOSAL, owner approved the idea]**
- The centre text and headline are real text, so screen readers hear today's week and date.
- The marker is `aria-hidden` and outside the tab order.
- All week content stays reachable without the ring: the nine month cards (Journey 4.4) and "Previous week / Next week" buttons on each week's content page.
- The preview chip and "Back to today" are normal buttons.

**Other**
- Estimate uncertainty: show the word "estimate" next to the due date (existing spec). A soft band on the ring needs a doctor-approved width, so it is **[OPEN]**; do not invent one.
- No pulsing, glowing or heartbeat-like motion on the ring.
- Do not copy Clue's red-to-salmon tail, the red drop quick-log button or phase colours.

### 7.3 Month illustration and animation

**Which image [OWNER]**
- Nine images, one per pregnancy month. The patient sees **only the image for the month she is in now**: month 2 shows month 2, month 3 shows month 3.
- The month comes from today's `content_week` through the existing `month_map` in `config.yaml` (Journey 6.3), never from the scrub position, and never hard-coded:

| Month | Weeks | Month | Weeks | Month | Weeks |
|---|---|---|---|---|---|
| 1 | 0 to 4 | 4 | 14 to 17 | 7 | 28 to 31 |
| 2 | 5 to 8 | 5 | 18 to 22 | 8 | 32 to 35 |
| 3 | 9 to 13 | 6 | 23 to 27 | 9 | 36 to 42 |

- Caption "Month N · now". Alt text: "Illustration of a typical baby in month N of pregnancy". Never "your baby".
- Past 42 weeks the month 9 image stays. After the pregnancy ends, no image.
- The same nine images are used on the month cards (swipe list, Journey 4.4) and the detail view.

**Animation (the already planned simple animation, Journey D3)**
- Slow float on the home screen only: the image moves up and down about 4 px over about 6 seconds, ease-in-out, only while the ring is idle (not while dragging) and the screen is not L1.
- When a new month starts, the image cross-fades once (about 300 ms). Changing weeks animates text only.
- Off completely with reduced motion. No Lottie here. Lottie stays for small decorative moments only.
- Use `/emil-design-eng` and `/review-animations` to check it. It must feel calm, never like monitoring.

**Fit.** The supplied images sit on a white background. Show each inside a round `--color-surface` disc in light mode. In dark mode use a cream or white disc (do not invert the artwork). See section 12 for files and licence.

### 7.4 Navigation and shell

**Bottom tab bar (below 1024).** Items from config `nav_items`: Home, Calendar, **Log** (raised centre action), Appointments, More. Height 64 px plus the safe-area inset. The Log button is a 56 px primary circle lifted about 16 px; it is the only filled item. Active tab: a soft `--color-primary-soft` pill behind icon and label, both in `--color-primary`. Labels are always shown (14 px). Icons 24 px Lucide. The bar is hidden while the full-screen Log sheet is open.

**Sidebar (1024 and above).** Same items. Log is a primary button at the top of the list. Active item has the same soft pill.

**Doctor notes [OWNER 2026-11-21, DEC-112]:** it lives under More, and appears as a status card on Home when there is a new note.

**Urgent button:** top right on every screen (phone and desktop). When the backend cannot be reached it keeps the Phase 3 behaviour (DEC-060): the warning-sign list stays usable, any warning sign shows the L1 advice at once, and the check-in is kept to send later **[OWNER 2026-11-21, DEC-109]**.

**Notification bar:** in-app only (no push in v1). Types are those in Journey section 10. Dismissible. See the no-layout-shift rule in section 11.

### 7.5 Log symptoms (Module 7)

Interior is defined by the Symptom spec; this section defines only the surface.

**Container.** Phone: full-screen sheet with an X (never a back arrow), no bottom tab bar. Desktop: right-side sheet about 480 px wide, same content. Fixed header (X, title "Log symptoms", pregnancy week), scrolling body, sticky footer with the Save button and safe-area padding. The body has bottom padding equal to the footer height so the last chip is never hidden.

**Order of the body**
1. **Warning signs group first** (Symptom spec 4.1). An urgent-tinted container (`--color-urgent` at about 10 percent, 1 px urgent border), `triangle-alert` icon, text label. Selecting one and submitting is the whole flow: no detail questions (spec 5.2). Text comes from message keys.
2. **Everyday symptoms** as chips under clear group headers. A chip expands inline into a detail row: severity (mild, moderate, severe), duration (the fixed ranges from config), and the extra checkboxes from spec 5.1.
3. **Nausea and vomiting** opens a separate sheet for the PUQE questions with a live score band.

**Chip.** At least 44 px high, label first, with a Lucide icon. Unselected: `--color-primary-soft` wash with 1 px border. Selected: `--color-primary` fill, `--color-on-primary` text **and a check icon**. Pressed state scales slightly. Several chips can be selected **[OWNER]**.

**Save**
- Label "Save check-in". Disabled until at least one symptom is chosen (this is validation V1), shown at 40 percent opacity with `aria-disabled`.
- On success show "Saved" **[OWNER: "saved successfully"]**. L0: a plain "Saved" plus `msg_level0_logged`. L1 or L2: the advice screen comes **first**, and the saved line stays plain, with no celebration and no motion on L1.
- **If the sheet is closed with unsaved choices [OWNER]:** keep the selections for a short time, then drop them. Store the draft on the device only, keyed to the patient, with a timestamp. Time to live: `draft_ttl_minutes` = **30**, `[CONFIGURABLE]` **[OWNER confirmed]**. Clear it on sign-out and on expiry. On reopening within the time, restore the choices with a small "Draft restored · Clear" line.
- **Offline [OWNER]:** the everyday Log is online only in v1. If Save fails, say it is not saved yet (message key) and keep the draft. Do not queue everyday check-ins. (Warning signs from the urgent button follow DEC-060, see 7.4.)
- Optional "Nothing to report today" and back-filling past days are **[OPEN]** (section 15). Until decided, there is no such option and only today can be logged.

### 7.6 Calendar: where logged symptoms live

**Purpose [OWNER].** The calendar stores and shows the symptoms the patient has logged, per day, along with appointments and pregnancy milestones (Journey section 9).

**Range.** Bounded: from the first day of the pregnancy to the due date plus 2 weeks. Not infinite.

**Phone layout.** One vertical scroll of months. Weekday letters pinned at the top; the current month header is sticky. A **week-number gutter** shows "W24" at the start of each row. Seven columns at 375 px give cells of about 44 px, which meets the touch rule. Today has a primary outline and bold numeral. A **Jump to today** button appears only when today is well off-screen. A visible "What these mean" link opens the legend (Clue hides its legend behind an unexplained icon).

**Desktop layout.** One month grid at a time with previous, next and Today controls, and a day-detail panel on the right (master and detail). Cells are larger and can show up to two markers plus "+n".

**Cell markers (each has a visible or accessible text equivalent)**
| Marker | Meaning | Look |
|---|---|---|
| Dot | A check-in was logged that day | Small filled circle, `--color-primary`; count shown in the day detail |
| Level icon | A red-flag day (L1 or L2) | **A different shape from the dot**: L1 `triangle-alert` in `--color-urgent`; L2 an icon in `--color-caution`. Always with an `aria-label` such as "Level 2 warning logged" |
| Appointment | An appointment that day | Lucide calendar icon |
| Milestone | New week, new month, new trimester (weeks 14 and 28), 37 weeks, due date | Week label in the gutter; small flag for the rest |
| Suggested check-up | Only after the official schedule is copied in (Journey R3) | **Dashed outline** and the word "suggested" in the detail |

Do not fade colours to show "predicted" (Clue's faded cells measured 1.97:1 and 2.17:1). Keep numerals at full contrast and use the dashed outline.

**Tap a day.** Phone: bottom sheet. Desktop: the right panel. It lists that day's check-ins (symptoms, severity, duration, level), appointments and milestones, with the pregnancy week. Past days are view-only until the owner decides on back-filling.

**Range pills.** Use for multi-day spans only (for example a hospital stay), not for single logged days.

### 7.7 Other patient screens

Appointments, More, genetic, results, notes, settings, legal, pregnancy end: keep their specs. Apply the same shell, tokens, typography, empty-state and skeleton rules. Use `/impeccable onboard` to propose empty states for history charts and the calendar, and show the owner before building **[OPEN]**.

---

## 8. Doctor app (desktop first, mobile supported)

**Look.** Clean, clinical, dense but calm. Cooler palette from the design system. Geist type with tabular numbers. Radius 6 to 12 px. Borders instead of shadows in dark mode.

### 8.1 Desktop layout (1024 and above)

- **Sidebar** 240 px, collapsible to 72 px: Home, Patients, Genetic review, Rule review, Admin (admin only). Active item has a soft pill and a 2 px left marker.
- **Top bar** 56 px: global patient search (press `/` to focus), theme toggle, user menu.
- **Content** max 1440 px, 12-column grid, 24 px gutters.

### 8.2 Dashboard home

Built so the doctor sees what needs attention first.
1. **Needs attention** (inbox): unseen red-flag items at the top, with level icon plus text, patient name, week, time, and a "seen" action (DEC-009).
2. **Summary tiles:** patients, unseen alerts, today's appointments. Big tabular numerals, small labels. No decorative charts.
3. **Patient list preview** and recent activity.

### 8.3 Patient list

Dense table, rows 48 px, sticky header, sortable columns, paginated (default 25). Columns: patient (name and ID), gestational week, risk status (badge with **icon and text**), last check-in, last warning level, next appointment, unseen count. Filters as chips plus a search field. Row click opens the patient. Keyboard friendly (arrow keys move row focus, Enter opens). Columns can be hidden on narrow screens.

### 8.4 Patient detail

Header card: name, age, week, due date and its source, risk badges. Tabs for the areas in the architecture: overview, trends, symptoms, predictions, records, genetic, notes, appointments. Charts with Recharts: direct labels, reference ranges with text, units inside the value, tabular numerals, a "View as table" switch for accessibility. Training-range warnings per DEC-009. AI drafts are labelled "AI draft, doctor approves".

### 8.5 Doctor on a phone (below 768)

- Sidebar becomes a menu button that opens a left sheet.
- **Tables become cards** (design system section 15): name, week, risk badge, last alert, chevron. Filters move into a sheet.
- Patient detail tabs become a horizontally scrollable tab bar. Charts go full width with fewer ticks. Primary actions sit in a sticky bottom bar. Forms are one column. Touch targets are 44 px.
- Tablet (768 to 1023): collapsed icon sidebar and tables with fewer columns.
- The same code serves both; there is no separate mobile app and no manual "mobile mode" switch.

---

## 9. Component inventory

Built from shadcn/ui (Radix) and Tailwind. New items have no shadcn equivalent.

| Component | Props (suggested) | States | Built from |
|---|---|---|---|
| **PregnancyRing** (new) | dueDate, dueDateSource, today, previewDay, onPreviewChange | default, previewing, estimate, capped at 42, skeleton, reduced motion | SVG arcs, Motion drag with `useMotionValue` |
| **RingCentre** (new) | month, caption, imageSrc | normal, month change, skeleton | Plain markup, `<picture>` |
| **RingMarker** (new) | day, isPreview | at today, dragging, released | Pointer events and Motion; `aria-hidden`, out of tab order |
| **RingHeadline** (new) | weeks, days, daysToGo, dueDate, isEstimate, previewWeek | today, previewing, no due date | Plain markup |
| **PreviewChip** | week, onReset | only while previewing | shadcn Badge + Button |
| **BabyImage** (new) | month | loaded, loading, none (ended) | `<picture>`, Motion float |
| **SizeLine** | object, valueText, source | shown, hidden (no sourced value) | Plain markup, Fluent Emoji |
| **BottomNav** | items from config | active, inactive, raised centre | Tailwind, Lucide 24 |
| **SideNav** | items | expanded, collapsed (doctor), active | shadcn Sidebar |
| **UrgentButton** | onPress, offline | always visible, offline fallback | shadcn Button, urgent variant |
| **NotificationBar** | items, onOpen, onDismiss | none, one, several, dismissed | shadcn Alert in a fixed slot |
| **LogSheet** | open, onClose | phone full-screen, desktop right sheet | shadcn Sheet |
| **SymptomChip** | id, label, icon, selected, onToggle | default, pressed, selected, disabled, focus-visible | shadcn Toggle |
| **SymptomGroup** | title, variant (urgent or everyday) | collapsed row, expanded detail | shadcn Card |
| **SymptomDetailRow** | symptomId, severity, duration, extras | empty, partial, complete | shadcn ToggleGroup |
| **PuqeSheet** | answers, onChange, onSubmit | empty, partial, complete with score band | shadcn Sheet + RadioGroup |
| **StickySaveBar** | label, disabled, onSave, pending | disabled (40 percent), enabled, saving | shadcn Button with safe-area padding |
| **DraftNotice** | onClear | shown when restored | Plain text |
| **CalendarMonthList** | startDate, endDate, markersByDate, onSelectDate | loading, empty, today in view, today off-screen | Custom grid or react-day-picker |
| **CalendarMonthGrid** (desktop) | month, markersByDate | default, selected day | Custom grid |
| **CalendarCell** | date, weekNumber, markers, isToday, isSuggested | default, today, logged, suggested (dashed), red-flag | Tailwind |
| **DayDetail** | date | phone sheet, desktop panel | shadcn Sheet and Card |
| **JumpToToday** | visible, onPress | hidden, shown | shadcn Button |
| **Legend** | open | closed, open | shadcn Popover or Sheet |
| **PatientTable** (doctor) | rows, columns, sort, filters | loading, empty, error, cards on phone | shadcn Table, container queries |
| **StatTile** (doctor) | label, value, trend | default, loading | shadcn Card |
| **TrendChart** (doctor) | series, ranges | default, table view, empty | Recharts |
| **Skeleton set** | ring, card, chip row, calendar month, table row | loading | shadcn Skeleton |

---

## 10. What we borrowed from Clue, and what we fixed

| Clue idea | Verdict | Alovia version |
|---|---|---|
| Ring with centre content and a draggable marker | Adapt | Pregnancy ring, 0 to 42 weeks, three trimester arcs, image in the centre |
| Trailing dot showing "today" while previewing | Borrow | Same, plus "Back to today" |
| Fade to show uncertainty | Adapt | The "estimate" label; band width is open |
| Category chips with a header | Adapt | Warning signs first, then everyday symptoms with inline detail |
| Search over options | Reject for v1 | About 25 options fit on two screens |
| Save disabled until a selection | Borrow | "Save check-in" with 40 percent disabled style |
| "Pain free" chip | Propose | "Nothing to report today", open decision |
| Week strip date picker | Hold | Only if back-filling is approved |
| Continuous month scroll, range pills | Adapt | Bounded scroll, week gutter, pills for multi-day spans |
| Solid logged and faded predicted | Adapt | Solid logged, dashed outline suggested |
| Jump-to-today that appears when needed | Borrow | Same |
| Raised centre Log button in the bottom bar | Borrow | Same |
| Promo banner, research modal, padlocks, paywall pill, mode chip | Reject | None |

**Measured facts from the recordings** (sampled pixels, so approximate): predicted calendar numerals 1.97:1 and 2.17:1; disabled Save label 2.21:1; solid fertile cell numerals 4.43:1; promo banner text 4.49:1. Chips about 40 dp high (Alovia minimum is 44 px). Ring stroke about 12 percent of diameter. Save button about 46 dp high. Neutral cells are rounded squares; numerals sat bottom-right.

---

## 11. Behaviours to implement exactly

1. **Ring is drag only** with haptics as in 7.2. Marker is `aria-hidden` and out of the tab order.
2. **Preview never changes data.** The marker position is local state. Nothing is written until the user logs something.
3. **The month image follows today, not the marker.** Test it.
4. **Reduced motion.** With `prefers-reduced-motion` or the in-app setting: no float, no easing, no cross-fade, no haptics.
5. **No layout shift.** Home data and notifications load together behind one skeleton. If a notification arrives later, animate its height only, never while the user is touching the ring, and respect reduced motion. Cumulative Layout Shift stays under 0.1 in tests.
6. **Touch targets** 44 by 44 px or larger, 8 px apart (chips, calendar cells, nav items, marker).
7. **Contrast gate.** Every new colour pair goes into the design-system table first. Numerals on any coloured fill reach 4.5:1.
8. **Save clearance.** Scroll containers get bottom padding equal to the bar plus the safe-area inset.
9. **Text and colour together.** Every marker has a text equivalent (`aria-label` and a visible label in the day detail).
10. **Ring text from state, synchronously.** Compute the headline from `previewDay` in the same render.
11. **Draft handling** as in 7.5 (30 minutes, device only, cleared on sign-out).
12. **Offline:** Save fails visibly and keeps the draft; the urgent button still shows the L1 advice for any warning sign and keeps the check-in to send later (DEC-060).
13. **No loading spinners on blank screens.** Use skeletons. Keep the bottom bar enabled while content loads.
14. **Config over code:** nav items, month map, draft time, duration ranges and message keys come from config, never hard-coded.

---

## 12. Images: the month illustrations

**[OWNER]** Use the supplied nine illustrations, which the owner says a doctor has approved. They are the **second set** the owner shared: a 3 by 3 sheet of nine unlabelled flat-style uterus-and-baby drawings. Read the sheet left to right, top to bottom: **top row = months 1, 2, 3; middle row = months 4, 5, 6; bottom row = months 7, 8, 9** (month 1 is the small curled embryo, month 9 is head-down). The other two sets the owner supplied are not used, except that the trimester grouping idea may inform the month cards.

**Files (done 2026-11-21).** The owner supplied the sheet; it is kept as `assets/illustrations/source/dreamstime_304802954_preview.jpg` and cropped (no other change) into the nine files below. Do not substitute other images. Saved as:
- `frontend/apps/patient-web/public/illustrations/month_1.webp` to `month_9.webp`, square, 312 to 470 px (the preview's full resolution; no `@2x`, because upscaling a preview adds no detail; make `@2x` files from the licensed originals), with the original sheet kept under `assets/`.
- Preload only the **current** month's file (it is the largest content on first paint).

**Rules**
- Do not edit the artwork. Cropping each drawing out of the sheet is fine. Do not add, remove or hide any watermark or credit text that is part of the artwork.
- Show in a round surface disc (7.3). Decorative `alt` is not allowed; use the alt text in 7.3.
- Wording stays "a typical baby at this stage". No photographs.

**Licence and review: read this.**
- These images are commercial stock images (Dreamstime, image ID 304802954, credited to Liubomyr Feshchyn) and the files supplied are the watermarked previews. They are **not** an openly licensed set. Journey decision D2 and section 7.1 allow only public domain, CC0, CC BY 4.0 or CC BY-SA 4.0. This brief **overrides D2 and 7.1 for these nine images only, for the capstone prototype and demo**, on the owner's instruction.
- **Before any public deployment** (anything beyond the college demo), buy the licence for the images, or replace them with an openly licensed set. Watermarked previews must not be shown to the public.
- Keep `show_prototype_banner = true` while these files are in use.
- Record each file in `docs/legal/CREDITS.md`: file name, source (Dreamstime, ID 304802954), artist, licence status ("stock, preview, not licensed for release"), date added (2026-11-21), changes (cropping only).
- Record the doctor's approval in `docs/illustration_review.md`: the owner supplies the reviewer's name and the date. Claude Code leaves a clear `[OWNER TO FILL]` line.
- Add the decision entry in section 15.

---

## 13. Testing (Playwright, plus axe)

Use `/playwright-best-practices`. Minimal reporters in CLI runs. Projects: patient at 360, 375 by 667, 390 by 844, 768 by 1024, 1280 by 800, 1440 by 900; doctor at 375, 768, 1280, 1440. Both themes. Freeze the clock with `page.clock` for date-dependent tests.

| Test | Pass condition |
|---|---|
| Above the fold (375 by 667) | Ring, baby image, headline and bottom bar are all visible without scrolling; urgent button visible |
| Month image | For each month boundary week in 7.3, the correct file is shown (uses `month_map` config) |
| Scrub does not change image | Drag the marker with pointer events to week 30 and to week 2; the image and "Month N · now" are unchanged; the preview chip appears; "Back to today" restores the headline |
| Read-only preview | No log or action buttons appear while previewing |
| Haptics | Stub `navigator.vibrate`; one call per day change; zero calls on an L1 screen and with reduced motion |
| Reduced motion | No float or cross-fade; changes are instant |
| Layout shift | CLS under 0.1 on Home, Log and Calendar |
| Touch targets | Every interactive element is at least 44 by 44 px |
| No horizontal scroll | At 360 px on every screen |
| Responsive layout | Patient: bottom bar below 1024, sidebar at 1024 and above, two columns on desktop. Doctor: table at 1280, cards at 375 |
| Save flow | Disabled until a chip is chosen; "Saved" on success; draft restored within 30 minutes and gone after; failed save keeps the draft; offline urgent button shows the L1 advice for a warning sign (DEC-060) |
| Calendar | Logged days show markers; L1 and L2 icons differ from the dot; tapping a day opens the detail with that day's check-ins |
| Accessibility | axe finds no violations (the ring marker is `aria-hidden`); contrast script passes for all token pairs |
| Visual snapshots | Light and dark, key screens at 375 and 1280, compared against stored images |

**Definition of done for a screen:** the section 3.2 pipeline was run; the screen works at 375 and 1280; tests above pass for it; there are no new colours outside the palette; no clinical wording was invented; the owner has seen a screenshot.

---

## 14. Build order

1. Root `PRODUCT.md` and `DESIGN.md` (step 0). Tokens: add arc tokens, fonts, motion tokens. Update `DESIGN_SYSTEM.md`.
2. Skeleton set, BottomNav and SideNav, UrgentButton, NotificationBar slot, app shells for both apps (responsive).
3. Log flow (Module 7), because it carries the safety logic: chips, groups, detail rows, PUQE sheet, Save bar, draft handling.
4. Home: ring, baby image, headline, preview chip, cards.
5. Calendar: markers, day detail, legend, desktop grid.
6. Doctor: shell, dashboard home, patient list, patient detail, responsive cards.
7. Motion pass with the Emil skills, reduced-motion pass.
8. `/unslop` and `/impeccable critique`, `audit`, `polish`, `harden` over every screen.
9. Playwright suite, axe, snapshots.

---

## 15. Decision log and open items

### Decisions to add to `docs/DECISIONS.md` (use the next free numbers)

| Draft ID | Date | Decision |
|---|---|---|
| next | 2026-11-21 | Frontend redesign: patient mobile-first PWA, doctor desktop-first with mobile support; palette unchanged; ring and baby image first on Home |
| next | 2026-11-21 | Ring marker is drag only with haptic ticks; no keyboard path (exception to `DESIGN_SYSTEM.md` section 16); scrub is the whole ring, read-only, with a preview chip |
| next | 2026-11-21 | Month image is fixed to the current month; scrubbing never changes it |
| next | 2026-11-21 | Month illustrations: use the owner-supplied doctor-approved set (stock, watermarked) for the prototype; **overrides Journey D2 and 7.1 for these nine files**; must be licensed or replaced before public release |
| DEC-109 | 2026-11-21 | Symptom draft kept 30 minutes on the device; everyday Log online only; offline urgent button keeps DEC-060 (owner, 2026-11-21) |
| next | 2026-11-21 | Design toolkit: Emil Kowalski skills, Impeccable, 21st.dev, heydamir unslop, taste skill, Playwright; single root `DESIGN.md` pointing to the design system |
| DEC-111 | 2026-11-21 | Typography: Fraunces + Figtree (patient), Geist (doctor); accepted after the owner's visual check |

### Open items

| # | Item | Default until decided |
|---|---|---|
| 1 | "Nothing to report today" option in Module 7 (spec treats an empty check-in as error V1) | Not built |
| 2 | Back-filled check-ins (needs `logged_for_date` and a red-flag date rule) | Only today can be logged; past days view-only |
| 3 | Doctor notes in the bottom nav or under More | **Decided (DEC-112):** under More, plus a Home status card |
| 4 | Chip icons: Lucide only, or custom | Lucide only (design system) |
| 5 | Ring colours: tints of primary or distinct hues | Tints of primary (section 5.2) |
| 6 | Empty states for history charts and calendar | Claude Code proposes with `/impeccable onboard`; owner approves |
| 7 | Estimate band width on the ring | Not built; the "estimate" label is shown |
| 8 | Typography choice | **Decided 2026-11-21 (DEC-111):** the owner picked Fraunces + Figtree after the 375 px comparison |
| 9 | Licence for the nine illustrations | Prototype only; buy or replace before public release |
| 10 | Which Playwright skill is installed | Confirm with `/skills` |

---

## Appendix A: Full breakdown of the two Clue recordings

Source: 50 frames from recording 1 (25 s) and 39 frames from recording 2 (20 s), 2 frames per second, plus full-resolution stills for measuring. Both are Android, 3-button navigation. Sizes assume a 1080 px wide screen at about 420 dpi and may be off by 10 to 15 percent. Where behaviour is inferred, it is flagged.

### A.1 Recording 1: the daily Track sheet

A full-screen modal for logging one day. Fixed top (header and week strip), scrolling body, sticky Save. The bottom navigation is hidden while it is open.

**Timeline.** 0 to 1 s: blank cream screen and spinner, header and strip already drawn. 1 to 9 s: body renders (search field, Period, Spotting, Feelings) and the user scrolls through Pain, PMS, a locked Sleep quality group, a Sleep duration card and the start of Sex life. 9 to 19 s: user scrolls up and taps chips; selecting turns the chip solid and Save teal; selecting again clears it and Save returns to grey. About 20 s: the user closes with X (nothing saved) and the Calendar tab appears.

| Component | What it is | Behaviour |
|---|---|---|
| Close (X) | Teal X, top left | Dismisses; no discard prompt seen |
| Title | The date, centred | Always the day being edited |
| Customise icon | Sliders glyph | Clue help: turn categories on or off and reorder them (40+ categories) |
| Jump-to-today | Calendar glyph with "20" | Not tapped |
| Week strip | Seven day cells, scrolls horizontally | Selected day: teal outline. Today: dark outline. Past day with data: pale teal pill. Future day: greyed. Numerals bottom-right. Clue help: the strip changes the day being logged |
| Search field | Grey rounded field | Scrolls with the body, returns on scroll up |
| Category title | Bold about 20 sp with teal "Learn more >" | Opens explanatory content |
| Chip | Pill with icon and label | Tinted by category; selected = solid fill with white label; toggles on tap |
| Save | Full-width pill, sticky | Grey and disabled until a chip is chosen, then teal; floats over content, hiding the last chips |

**Categories seen:** Period (Light, Medium, Heavy, Super heavy; pink), Spotting (Red, Brown), Feelings (14 options; peach), Pain (11 options including Pain free; lavender), PMS, Sleep quality (locked, Clue Plus), Sleep duration (numeric card), Sex life (cut off).

**Worth noting:** colour is the category key; icons carry meaning (weather faces for feelings, body parts for pain); "Pain free" makes a zero day a real entry; "Learn more" sits beside the input; everything is one long scroll about four screens tall.

### A.2 Recording 2: the Cycle home and ring

**Timeline.** 0 to 1.5 s: splash (logo animating). 1.5 to 2.5 s: blank screen and spinner with the bottom bar faded. About 2.5 s: first render (header, mode chip, ring, predictions text). About 4 s: a teal promo banner slides in and pushes everything down about 11 percent of the screen. About 5 to 6.5 s: a full-screen research modal, dismissed with X. 7 to 12 s: the user drags the ring marker. About 12.5 s: Calendar tab, half a second of spinner.

**Ring anatomy.** Grey base arc (about 300 degrees, clockwise from the top); red drop at the top (tappable quick log); red period arc fading to salmon; red dots as tracking dots; thick teal arc for the fertile window with an ovulation marker; white "Day N" marker bubble whose outline takes the phase colour; a trailing white dot at today; a three-line centre stack (date, headline, link).

**Centre text by position (Clue):** today in the luteal phase "8 more days until next period"; Day 29 "Your period may start tomorrow"; Day 1 "5 more days of your period"; follicular days "Your next period is due Nov 28"; fertile days "Potential fertile day". The copy does three jobs: countdown, progress count, fixed due date.

**Scrub behaviour:** everything updates on one gesture; old and new text cross-fade and briefly overlap; the countdown once disagreed with the date (6 then 7); the marker jumped from Day 29 to Day 1 (Clue says it moves both ways, so likely a fast drag). A floating chevron covered part of the "How do you feel today?" card.

**Chrome:** "Current cycle" title with a More menu; a mode chip (Clue has five modes, including Pregnancy); a predictions empty-state paragraph.

### A.3 The calendar (both recordings)

One continuous vertical scroll of months; weekday row pinned; month name not pinned. Top bar: Filter (up to 3 logged experiences), a red drop for fast period logging, and a jump-to-today icon that appears only when today is scrolled off. Cells are soft grey rounded squares with bottom-right numerals; today has a dark outline.

| Look | Meaning |
|---|---|
| Solid dark red | Heavy or super heavy bleeding |
| Solid red / salmon | Medium / light bleeding or tail |
| Solid teal | Fertile window |
| Teal with pale circle and dot | Ovulation |
| Same colour at about half strength | Predicted (future) days |
| Small red tick | Tracking dot (colour = category) |

Consecutive coloured days merge into a **range pill**: rounded left end on the first day, rounded right end on the last, and the rounded end restarts when a span wraps to a new week row. Tap a day = editable overview; double tap = open tracking for that day (Clue help). A purple "Unlock my cycle predictions" pill floated over the bottom and covered today's row in one frame.

### A.4 Shell and patterns

Five-item bottom bar with a raised filled centre Track button; active tab shown as a soft pill; Track opens as a modal with X; one strong teal accent (it collides with the fertile colour); inline teal "Learn more >" links; **blank white spinner screens on every load** (no skeletons).

### A.5 Extracted visual system (sampled)

| Role | Value |
|---|---|
| Page background | `#FDFBF7` |
| Primary teal | `#00829D` |
| Teal text | `#107875` to `#217370` |
| Heavy red / base red / salmon | `#A70015` / about `#E5323B` / `#FF8880` |
| Promo purple | `#AF569C` |
| Chip washes (pink, peach, lavender) | `#FFECEC`, `#FFECE4`, `#EBEEFD` |
| Neutral cell / disabled button | `#F8F6F5` / `#B0AEAC` |

Type: rounded geometric sans; ring headline about 28 sp semibold, category title about 20 sp bold, chip label 15 to 16 sp, links 13 to 15 sp, marker caption about 10 sp. Shapes: pills for chips, buttons and nav highlight; about 8 dp for cells; large radius for banner and modal. Icons: custom flat filled illustrations in content, thin outline glyphs in chrome. **None of this is copied into Alovia**; the palette and fonts are Alovia's own.

### A.6 Interaction and motion inventory

| # | Trigger | What changes | Time |
|---|---|---|---|
| 1 | Launch | Logo animation on white | about 1.5 s |
| 2 | Splash ends | Rounded-corner reveal, then spinner | about 1 s |
| 3 | Data arrives | Ring, text and nav appear together | under 0.5 s |
| 4 | Banner arrives | Inserts at top and pushes content down | under 0.5 s |
| 5 | Modal arrives | Screen dims, red card | under 0.5 s |
| 6 | Drag ring marker | Bubble, outline colour, date, headline, link change | continuous |
| 7 | Text change during drag | Cross-fade with overlap | about 0.5 s |
| 8 | Floating chevron | Appears over the card, vanishes later | seconds |
| 9 | Tap a nav tab | Content blanks with a spinner | about 0.5 s |
| 10 | Track sheet opens | Blank sheet, then content | about 1 s |
| 11 | Scroll Track | Header and strip fixed; search scrolls away | continuous |
| 12 | Tap a chip | Ripple tint, then solid fill | about 0.3 s |
| 13 | First chip selected | Save grey to teal | about 0.3 s |
| 14 | Last chip cleared | Save back to grey | about 0.3 s |
| 15 | Close sheet | Sheet leaves | about 0.5 s |
| 16 | Scroll far from today | Jump-to-today appears | on scroll |

Gestures seen: vertical scroll, horizontal scroll on the week strip, drag on the ring marker, taps. No swipe-to-delete, long press, pinch or visible haptics (a recording cannot show haptics).

### A.7 Shortcomings in Clue and the Alovia rule each one produced

| # | Area | Finding | Severity for Alovia | Alovia rule |
|---|---|---|---|---|
| 1 | Accessibility | Ring scrub appears gesture-only | High | Owner accepts drag only; compensations in 7.2 |
| 2 | Accessibility | Colour is the only encoding for flow, fertility, prediction | High | Text and icon with every status; dashed outline for suggested |
| 3 | Accessibility | Chips about 40 dp | Medium | 44 px minimum |
| 4 | Accessibility | Tiny marker caption (about 10 sp) and light-grey year | Medium | Marker caption 14 px; no light-grey text under 4.5:1 |
| 5 | Clinical safety | Chips are flat taps with no severity or duration | High | Inline severity and duration rows |
| 6 | Clinical safety | Urgent symptoms not separated from everyday ones | High | Warning signs group first, urgent-tinted |
| 7 | Clinical safety | "Pain free" and "Fine" read as reassurance | Medium | Wording rules ban "normal" and "nothing to worry about" |
| 8 | Clinical safety | No note that entries are not monitored live | Medium | Standing line from the existing message keys |
| 9 | Commercial | Banner, research modal, paywall pill within 10 seconds | High | None; notification bar carries only Journey section 10 types |
| 10 | Commercial | Padlocks on education and a symptom group | High | No locked health content |
| 11 | Commercial | Paywall pill covers today's calendar row | Medium | Nothing floats over data |
| 12 | Layout | Banner shifts the ring down about 11 percent | Medium | Load together; no late insertion shifts |
| 13 | Layout | Floating chevron covers card text | Low | No floating scroll hints over content |
| 14 | Layout | Sticky Save overlaps chips | Medium | Bottom padding equals bar plus safe area |
| 15 | Layout | Numerals bottom-right look misaligned beside capsules | Low | Numerals centred in cells |
| 16 | Loading | Blank white screen plus spinner on every load | Medium | Skeletons |
| 17 | Loading | Nav tabs faded while loading | Low | Nav stays enabled |
| 18 | Interaction | Centre text lags the marker and can disagree | Medium | Compute from state, synchronously |
| 19 | Interaction | Marker jumped between days | Low | Clamp and test drag speed |
| 20 | Interaction | No confirmation or undo for a cleared chip or closed sheet | Low | Draft kept 30 minutes |
| 21 | Information | Long single-scroll Track page, no jump between categories | Medium | Short list; group headers; PUQE in its own sheet |
| 22 | Information | Teal means both "interactive" and "fertile" | Low | One meaning per colour; red only for urgent |
| 23 | Information | Fade carries unexplained meaning | Low | Explain in the legend, or avoid |
| 24 | Information | Red ticks unexplained on screen | Low | Visible legend link |
| 25 | Information | Light flow and predicted days look alike | Medium | Different shapes and a dashed outline |
| 26 | Commercial | Reviewers report full-screen pop-ups when opening a page or tracking (anecdotal) | Medium | No pop-ups; confirmations are inline |

### A.8 Contrast measurements (WCAG AA: 4.5:1 text, 3:1 large text and UI)

| Element | Colours | Ratio | Result |
|---|---|---|---|
| Predicted fertile numerals | `#F8F6FF` on `#7BBDC9` | 1.97 | Fail |
| Predicted period numerals | `#FBF9F8` on `#EB9496` | 2.17 | Fail |
| Disabled Save label | `#FFFFFF` on `#B0AEAC` | 2.21 | Fail (disabled, but hard to read as a state) |
| Future date in the strip | `#ADABA9` on `#F7F5F3` | 2.10 | Fail (disabled) |
| Solid fertile numerals | `#FFFDFF` on `#00829D` | 4.43 | Marginal |
| Promo banner text | `#FFFFFF` on `#00829D` | 4.49 | Marginal |
| Teal "Learn more" | `#217370` on `#FDFBF7` | 5.42 | Pass |
| Ring phase link | `#107875` on `#FEFCF9` | 5.17 | Pass |
| Chip labels | `#35261E` on `#FFEDE6` | 12.79 | Pass |
| Inactive nav label | `#4C4C4C` on `#FFFFFF` | 8.59 | Pass |

### A.9 Answered from Clue's own help pages (checked 2026-11-21)

Chips toggle (tap to select, tap again to deselect); the date strip changes the day being logged; the sliders icon is "Customize"; Filter shows up to 3 logged experiences; calendar tap shows an editable overview and double tap opens tracking; the red drop is fast period logging; red ticks are tracking dots; padlocks are Clue Plus (paid: 10 premium categories, 12-month predictions); the ring marker moves both ways; the mode chip switches among five modes; Clue has a free Pregnancy mode with weekly fetal development updates (the closest reference for Journey, and the best subject for a third recording).

### A.10 Owner answers to the open questions (2026-11-21)

| # | Question | Answer | Where it landed |
|---|---|---|---|
| 1 | Save and unsaved choices | "Saved successfully"; keep unsaved choices briefly, then drop | 7.5 |
| 2 | Several choices at once | Yes | 7.5 |
| 3 | Padlock on phase link | Clue-only; nothing to decide | n/a |
| 4 | Ring keyboard and haptics | Drag only with haptics, no keyboard path | 7.2, section 2 |
| 5 | Ring at the end of the cycle | Ends when the pregnancy ends | 7.1 states |
| 6 | Offline | Online only; failed Save keeps the draft | 7.5 |
| 7 | Empty state | Not answered | Open item 6 |
| 8 | Ring scrub window | Whole ring with guardrails | 7.2 |
| 9 | Centre image | Current month only; scrubbing never changes it | 7.2, 7.3 |
| 10 | Draft time and offline urgent message | Confirmed (30 minutes; fixed fallback) | 7.4, 7.5 |
| 11 | Centre text while scrubbing | Month caption fixed; viewed week shown in the headline and chip | 7.2 |
| 12 | Image set | The second (3 by 3) set | Section 12 |

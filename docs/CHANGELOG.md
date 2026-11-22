# Changelog — Alovia

User-visible changes per release (one release per finished phase). Work-session details go in `tracking/HISTORY.md`, not here.
Format: newest first. Versions: `0.<phase>.<patch>` until the first full release.

## [Unreleased] — Frontend redesign (`redesign/frontend`, 2026-11-21 to 2026-11-22)
Brief: `FRONTEND_REDESIGN.md`; decisions DEC-105 to DEC-118. No backend behaviour changed except two vocabulary fields and one message key (below).
### Changed
- Patient app: Fraunces + Figtree type; bottom bar Home, Calendar, Log (raised), Visits, More (Doctor notes moved to More); side bar on laptops.
- Patient Home: a pregnancy ring with today's month drawing (owner-supplied set, licence before release), a drag preview of any week (read-only, nothing saved), headline, size line, status cards for new doctor notes and results; two columns on laptops.
- Log symptoms: a sheet with warning signs first, chips, detail cards, a PUQE sheet with a live score band, Save disabled until a choice, a 30-minute device draft and a clear "not saved yet" message.
- Calendar: a scrolling list of months whose rows are pregnancy weeks ("W24"), distinct L1 / L2 markers, a legend, day details with each symptom, Jump to today; one month with a side panel on laptops.
- Doctor app: Geist type; a collapsible side bar, top bar with "/" patient search and user menu; home with level icons and summary tiles; patient list with per-module badges (never combined), sorting, pages, keyboard rows and phone cards; patient page header card, "View as table" for every chart, sticky form buttons on phones.
- Motion: sheets slide in, buttons respond to presses, patient tabs cross-fade, Home cards rise once; everything off with reduced motion.
- Quality: empty states for symptom history and an empty calendar day, readable line lengths, 44 px touch targets, long names no longer widen the page.
### Added (backend)
- Symptom vocabulary returns `puqe_bands` and `draft_ttl_minutes` (30, configurable); message key `msg_not_saved` (text pending doctor approval; one more rule-review row, 189 in total).
### Tests
- See TESTING.md "Frontend redesign additions": more sizes and themes, every-screen checks, ring and motion tests, a token contrast test and 24 visual snapshots.

## [0.5.0] — 2026-11-20 — Phase 5: Doctor Dashboard + Admin
### Added
- Doctor home: a needs-attention inbox (red flags, pattern changes, genetic assessments, records, pregnancy end; "Mark as seen" shows who and when to every assigned doctor; AI suggestions would sit last) and the patient list in priority order, with search and filters. Model classes are always written out, never colour only.
- Patients: create and edit records; one-time invite links (a new link replaces an unused one; joined patients cannot get another).
- Patient page with tabs. Overview: details, each latest result in its own box (no combined score), invite, activity log. Fetal and Maternal: forms built from the models' own field lists, unit switches with a conversion preview (HbA1c %, glucose mg/dL, temperature °C), training-range warnings (the prediction still runs), the HbA1c note for haemoglobin variants, results with class probabilities, top factors and limitations, sharing with the patient (template text + optional message, once), earlier results and trend charts. Genetic: review queue, confirm with a note or correct the inputs (a new assessment; the old one is kept; a second doctor is refused). Symptoms: check-ins with levels, rule IDs, pattern badges, notes and charts (read-only). Records: upload PDF/JPG/PNG to a private store (type, file signature and size checked) and download through 5-minute links. Notes (private or shared), appointments (each side edits only its own), dates (clinician-confirmed or ultrasound) and pregnancy status.
- Patient app: More → My results (only shared results, as text and the doctor's message); notifications for shared results, genetic reviews and doctor date changes; genetic review notes link to the genetic check.
- Rule review: every genetic, symptom and Journey rule row with its source; doctors tick "checked" and comment per rules version; export of the sign-off file; an optional start-up block until everything is signed.
- Admin (admin role only): invite doctors by email (with a Set password page), deactivate and reactivate, manage assignments (the last doctor cannot be removed), and the activity log (no clinical values).
- Training ranges computed from the owner's training notebooks (re-run: identical models), never typed by hand.
### Fixed
- Opening an invite link while already signed in as another patient no longer jumps silently into that patient's app; the page says who is signed in and offers Sign out.
### Notes
- All texts shown to patients and the limitation/warning texts stay "[Text pending doctor approval]" until a doctor approves them. AI features (Phase 6) are off.

## [0.4.0] — 2026-11-19 — Phase 4: Genetic Risk
### Added
- Genetic risk check (More → Genetic risk): what the patient knows about her own and her husband's status for haemoglobin conditions (β-thalassaemia, sickle cell, HbE/HbD; always asked), haemophilia and Marfan syndrome (behind entry questions), with "how do you know?" evidence and a consent reminder about the father's data.
- Fixed inheritance rules from the spec (45 haemoglobin pairings, 7 haemophilia and 4 Marfan rows): a chance ("1 in 4 (25%)", "not expected" — never 0%) only when the information is confirmed and consistent; otherwise the next step (testing, counselling, doctor review). Weak evidence counts as unknown; conflicts are sent to the doctor. Haemophilia always shows "if the baby is a boy" and "if the baby is a girl" together — the baby's sex is never asked or shown (PCPNDT Act).
- Result screen with the fixed disclaimer, next steps, and the doctor's note set apart; earlier checks; a "Genetic check" status card on the home screen.
- Doctor side (data only, screens in Phase 5): every assessment waits for doctor review and creates an inbox item, marked high priority when risk is indicated.
- A rule-review sheet for the reviewing doctor (`docs/modules/reviews/`).

## [0.3.0] — 2026-11-19 — Phase 3: Symptom Tracking
### Added
- Log symptoms: warning signs at the top (one tap) and everyday symptoms with only the details each asks for (severity, duration, body area, PUQE-24 nausea questions in the official wording, optional time and notes).
- Red-flag rules from the spec (25 rules, MCP-card based): advice shown at once — "Go to hospital now" (large, high contrast, Telangana ambulance numbers), "Contact your doctor today", or "Saved"; national mental-health helpline (Tele MANAS) with mood changes. Notes are never read by the rules and the patient is told so.
- Urgent button page ("I have an urgent symptom") that works even when the server cannot be reached: the warning-sign list and the advice are built into the app; the check-in is sent later.
- Symptom history: per-symptom charts by pregnancy week and the PUQE score over time, each with a table view.
- In the Journey: "Logged today" on the quick-log card, "This week's summary" (what she logged, next to what is common at this stage, kept apart), and symptom dots and distinct red-flag icons on the calendar.
- Doctor side (data only, screens in Phase 5): every L1/L2 check-in and pattern change (P1–P5) creates an inbox item; pattern changes are never shown to the patient.
- A rule-review sheet for the reviewing doctor (`docs/modules/reviews/`).
### Changed
- Patient messages and phone numbers now share one format across modules.

## [0.2.0] — 2026-11-17 — Phase 2: Pregnancy Journey
### Added
- Pregnancy dates: onboarding with three options (last period, doctor's due date, ultrasound), date rules D1–D3, confirmation before an estimate replaces a doctor's or scan date, full date history.
- Journey home: weeks and days, days to go, due date with "estimate" label, baby card with a gentle floating month drawing (placeholder drawings, reduced-motion respected) and a typical-size comparison, "This stage" content, quick-log shortcut, this-week strip, next appointment, nine swipeable month cards and month detail pages.
- Prototype content with sources on every card (Office on Women's Health, NHS under the Open Government Licence, MedlinePlus) and WHO fetal-growth weights for weeks 14–40 with Fluent Emoji comparison icons; a prototype banner on every content screen. All content awaits doctor review.
- Calendar tab: month view with milestone and appointment markers, day details, navigation from pregnancy start to due date plus two weeks; dashed "suggested" PMSMA check-up days (the 9th of each month in the 2nd and 3rd trimesters, from the official NHM page).
- Appointments tab: add, edit and delete her own appointments (date, optional time, title, note); doctor-added appointments are labelled and read-only.
- Notification bar: new week, new month, appointment soon and doctor-note notices, created when the app opens, each once; tap to open, dismiss to hide.
- Doctor notes tab: notes her doctor shared, newest first, read-only.
- "My pregnancy has ended": three choices, a no-default question about informing the doctor, a quiet home with support and safety messages, official Telangana helpline numbers (tap to call), and undo within 7 days.
- A doctor review sheet for every message, content item, size object and rule (`docs/review/journey_doctor_review.csv`), and a script for the owner to create admin accounts.
- Doctor app: doctors and admins accept the app-wide consent once at first sign-in.
- Activity log entries for sign-ins and for patient changes to dates, appointments and pregnancy status (never clinical values).
- Patient-facing messages show "[Text pending doctor approval]" until a doctor approves their wording.
### Changed
- HTTP 405 responses now use the error code `METHOD_NOT_ALLOWED`.

## [0.1.0] — 2026-11-17 — Phase 1: Foundation
### Added
- Backend (FastAPI, Python 3.14): settings, JSON logs with request IDs, `{data, error}` envelope, `GET /api/v1/health` (database, models), Supabase token verification, `GET /me`, `POST /me/consent`, invite check and invite-only patient linking.
- Database: Phase 1 tables (users, consents, doctors, patients, assignments, invites, audit log, fetal and maternal results) via Alembic migration 0001, tested on a separate test project.
- Fetal and maternal risk models moved unchanged; outputs identical to the old backend for 12 approved reference cases.
- Patient web app (installable): landing page with disclaimer, invite-only sign-up with 18+ and consent, sign-in/out, navigation shell with urgent button placeholder, theme switch, legal and about pages.
- Doctor web app: sign-in/out, role check, navigation shell (admin area for admins), theme switch, legal and about pages.
- Shared design tokens (light and dark, patient and doctor), fonts self-hosted, accessible components.
- Development seed data with invite links; one command for every check (`scripts/check_all`).
- Knowledge base collection moved into `knowledge-base/`.

## [0.0.0] — 2026-11-16
### Added
- Complete documentation set (PRD, UX flows, design system, architecture, database, API, security, code style, testing, environment, error handling, observability, deployment, decisions, roadmap), module specs, legal drafts and tracking files.

<!-- Template
## [0.N.0] — YYYY-MM-DD — Phase N: <name>
### Added
- …
### Changed
- …
### Fixed
- …
### Removed
- …
-->

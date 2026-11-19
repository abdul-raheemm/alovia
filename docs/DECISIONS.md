# Decisions — Alovia

Record every important decision here so it is not re-decided. Module-level decisions are also in each spec's "Final decisions" table; the most important are repeated here.
**New entries:** add at the bottom with the next number, status `Accepted`, and the date. Mark replaced decisions `Superseded by DEC-xxx`.

| ID | Date | Decision | Reason | Status |
|---|---|---|---|---|
| DEC-001 | 2026-10-02 | All database and storage access goes through FastAPI; frontends use Supabase only for sign-in | Direct access judged weak and risky | Accepted |
| DEC-002 | 2026-10-02 | Store `due_date`; derive gestational age at query time | Avoids stale values | Accepted |
| DEC-003 | 2026-10-11 | Pregnancy Risk Score retired; Module 3 = Genetic Risk; Module 7 = Symptom Tracking; no combined score | No valid basis for combining separate models | Accepted |
| DEC-004 | 2026-11-16 | Module specs written per module; project-wide docs consolidated after (this set) | Avoid repeated edits | Accepted |
| DEC-005 | 2026-11-16 | Rules (genetic, symptoms, journey) are YAML files in the repo; each result stores `rules_version` | Reviewable, testable, versioned | Accepted |
| DEC-006 | 2026-11-16 | Genetic: haemoglobin group table (incl. β-thal × sickle), Marfan as dominant condition, consanguinity flag, timing prompt, PCPNDT wording; patient sees calculated result with "review with doctor" (configurable) | Researched; India-relevant | Accepted |
| DEC-007 | 2026-11-16 | Symptoms: MCP-card red flags, L1/L2, any bleeding = L1, PUQE-24, doctor-only pattern rules, no kick counter, pregnancy only | Official Indian guidance; safety | Accepted |
| DEC-008 | 2026-11-16 | Journey is the patient home; 9 openly licensed month illustrations; Fluent Emoji size objects; content via a provider interface (prototype now, knowledge base later); pregnancy-end flow | Woman-centric novelty; licence safety | Accepted |
| DEC-009 | 2026-11-16 | Dashboard: many doctors per patient, minimal admin, inbox with "seen", doctor-controlled result sharing, unit switches, training-range warnings, invite codes, rule review screen, audit log, doctor + patient appointments | Human-in-the-loop, safety | Accepted |
| DEC-010 | 2026-11-16 | AI draft features AI-1…AI-4, "AI drafts, doctor approves", flags off until LLM chosen | Small, safe AI value | Accepted |
| DEC-011 | 2026-11-16 | RAG: safety check first, no answer without valid citations, dosage docs excluded, no own-result explanations, NHS verbatim Sources panel, built last | Safety; licence | Accepted |
| DEC-012 | 2026-11-16 | **Two separate web apps** (patient; doctor+admin) in one repository with shared packages | Owner choice; different users and looks | Accepted |
| DEC-013 | 2026-11-16 | **TypeScript** frontends (React + Vite + Tailwind + shadcn/ui) | Fewer errors | Accepted |
| DEC-014 | 2026-11-16 | Patient app installable to the phone home screen (PWA, opens the web app) | Owner choice | Accepted |
| DEC-015 | 2026-11-16 | Soft lavender accent; warmer patient palette, cooler doctor palette; light + dark themes; letter-mark "A" logo; Nunito (patient), Inter (doctor) | Owner choice; contrast-checked | Accepted (confirmed visually by the owner, 2026-11-17) |
| DEC-016 | 2026-11-16 | Fresh Supabase project; agent notifies the owner when URLs/keys are needed | Clean start | Accepted |
| DEC-017 | 2026-11-16 | Hosting: backend Render (free); frontends Vercel Hobby (free, non-commercial academic use) | Free, easy, fits Vite | Accepted |
| DEC-018 | 2026-11-16 | Python 3.12 for the backend | ML library compatibility | Superseded by DEC-030 |
| DEC-019 | 2026-11-16 | Fresh git repository at `C:\Users\Engineer\Desktop\Alovia` itself (no extra `alovia/` subfolder). The old `ml-test/` and `rag/` folders stay where they are, untouched, **listed in `.gitignore` from the first commit** and excluded from graphify, until the owner moves or deletes them | Short paths; safety of existing work | Accepted |
| DEC-020 | 2026-11-16 | Build order: Foundation → Journey → Symptoms → Genetic → Dashboard/Admin → AI drafts → RAG → Security hardening → Deployment; database built per phase | Owner choice | Accepted |
| DEC-021 | 2026-11-16 | **Security hardening last (Phase 8)**; only the minimum in `SECURITY.md` §0 earlier | Owner choice | Accepted |
| DEC-022 | 2026-11-16 | Row-Level Security is added in Phase 8 with the rest of security, not earlier. Known risk: tables readable with the public key until then; accepted because only synthetic data is used | Owner choice: security last | Accepted |
| DEC-023 | 2026-11-16 | Users 18+ only in v1 | DPDP children's-data rules | Accepted |
| DEC-024 | 2026-11-16 | Patients sign up **only through a doctor's invite link** (link carries a one-time code). The doctor creates the patient record first; the sign-up links the new login to it. No open patient self-sign-up in v1. | Every patient is linked to a doctor; no duplicate records | Accepted |
| DEC-025 | 2026-11-16 | Tracking files: CONTEXT, PROGRESS, HISTORY (per session, with "who"), ERROR_LOG (agent errors + lessons); CHANGELOG kept separately (per release, user-visible) | Owner request; different purposes | Accepted |
| DEC-026 | 2026-11-16 | `CLAUDE.md` holds agent rules (owner's prompt.md + blueprint AGENTS.md); `docs/AGENTS.md` points to it | Claude Code reads CLAUDE.md automatically | Accepted |
| DEC-027 | 2026-11-16 | No analytics, ads or tracking; essential storage only; so no cookie banner in v1 | Data minimisation | Accepted |
| DEC-028 | 2026-11-16 | Alembic migrations; agent asks before running any migration on Supabase | Reproducible schema; safety | Accepted |
| DEC-029 | 2026-11-16 | Self-hosted fonts; Lucide icons; no external CDNs | Privacy; licences | Accepted |
| DEC-030 | 2026-11-16 | Python 3.14 for the backend (replaces DEC-018) | The old ml-test venv was 3.14 and the model libraries support it; 3.15 is too new | Accepted |
| DEC-031 | 2026-11-17 | The consent version is written in `docs/legal/CONSENT_TEXT.md`; the backend keeps a copy of only the version string in a backend config file, and a test fails if the two differ | Only `backend/` is deployed (DEPLOYMENT.md), so the backend cannot read `docs/` at runtime | Accepted |
| DEC-032 | 2026-11-17 | For now, `users` rows and roles are created by admins and the owner; later, doctor accounts come through the admin invite (Flow A1) | Owner choice; keeps Phase 1 simple | Accepted |
| DEC-033 | 2026-11-17 | `users.id` equals the Supabase Auth user id but has **no foreign key** to `auth.users` | Keeps the schema testable on a plain test database; the backend already verifies the id from the token | Accepted |
| DEC-034 | 2026-11-17 | Test database = a separate, empty Supabase project `alovia-test` (`TEST_DATABASE_URL`); migration tests drop and recreate its tables and refuse to run against the main project | No local Postgres or Docker on the laptop; nothing to install | Accepted |
| DEC-035 | 2026-11-17 | Result tables (`fetal_results`, `maternal_results`) have only the `(patient_id, created_at DESC)` index; no separate `patient_id` index | The composite index already serves every lookup by `patient_id` | Accepted |
| DEC-036 | 2026-11-17 | A patient's `users` row (role `patient`) is created by `POST /patient/link` from the doctor's invite link (completes DEC-032) | Keeps sign-up invite-only (DEC-024) | Accepted |
| DEC-037 | 2026-11-17 | Frontend versions pinned exactly (ARCHITECTURE §3): React 19.3.1, react-router 8.5.1, @tanstack/react-query 5.107.1, Vite 8.3.8, Tailwind CSS 4.3.5, TypeScript 5.9.3, ESLint 9.39.5, Vitest 5.1.0, Playwright 1.65.1, @axe-core/playwright 4.14.0, vite-plugin-pwa 2.0.0, @supabase/supabase-js 2.119.0, react-hook-form 7.92.0, zod 4.6.7, lucide-react 1.73.0, marked 18.2.1, @fontsource nunito/inter 5.3.0 (full list in `frontend/package-lock.json`) | TypeScript 5 because openapi-typescript (generated API types, API.md §6) supports only TS 5; ESLint 9 because eslint-plugin-jsx-a11y supports only up to 9 (ESLint 9 is marked unsupported upstream — revisit in Phase 8) | Accepted (Phase 1 permission) |
| DEC-038 | 2026-11-17 | Invite failures — wrong, used, expired, or a patient record already linked — all return 404 `NOT_FOUND` with one message; `GET /invites/{code}/check` returns only `{valid}`. Codes use letters/digits without look-alikes, length and expiry from `backend/rules/dashboard/config.yaml` | Dashboard spec §8.2 and §25 test 9 (same message for every failure); API.md §6 ("not found" hides existence) | Accepted (Phase 1 permission) |
| DEC-039 | 2026-11-17 | Legal, consent and credits pages render the Markdown files in `docs/legal` directly; the sign-up checkboxes and the consent version are read from `CONSENT_TEXT.md`, so the apps cannot drift from the documents | One source of truth for legal text | Accepted (Phase 1 permission) |
| DEC-040 | 2026-11-17 | Patient navigation = the Journey spec's six items (Home, Calendar, Log symptoms, Appointments, Doctor notes, More), served from `backend/rules/journey/config.yaml` (`nav_items`); replaces the five-item list in DESIGN_SYSTEM §11 | Journey spec §4.1 makes the items configurable | Accepted |
| DEC-041 | 2026-11-17 | Until a doctor approves a message in `messages.yaml`, screens show a visible "[Text pending doctor approval]" placeholder — never text written by the agent | No medical wording from the agent (CLAUDE.md rule 5) | Accepted |
| DEC-042 | 2026-11-17 | Prototype Journey content (Journey §8.3) is built by the agent from pages it fetches from womenshealth.gov (S1) and OpenStax (S2), with source URL and access date on every item, for owner review (option C) | Owner choice | Accepted (OpenStax part superseded by DEC-051) |
| DEC-043 | 2026-11-17 | The agent fetches the WHO fetal growth chart values (S3) and the Microsoft Fluent Emoji icons (S6) and prepares a draft size-reference table; each week's comparison object is then reviewed by a doctor (R2) | Owner choice | Accepted |
| DEC-044 | 2026-11-17 | `inbox_items` moves from the Phase 3 migration into migration 0002, so the pregnancy-end flow can notify the doctor (Journey §11.3) | The table is needed one phase earlier | Accepted |
| DEC-045 | 2026-11-17 | Phase 2 frontend additions pinned exactly: motion 14.14.0, react-day-picker 9.14.0 (the 9.x line, not 10.x: stable API the agent knows well) | ARCHITECTURE §3 names both libraries | Accepted (owner approved both installs) |
| DEC-046 | 2026-11-17 | Doctors and admins accept the app-wide consent (same text and version) once, at their first sign-in; the doctor app shows it before anything else | Owner decision (Phase 1 follow-up) | Accepted |
| DEC-047 | 2026-11-17 | HTTP 405 uses the error code `METHOD_NOT_ALLOWED` (API.md §3) | Owner decision: the standard code | Accepted |
| DEC-048 | 2026-11-17 | Sign-ins are written to `audit_log` ("signed in"): sign-in happens in Supabase, so the backend logs the first `GET /me` of each new Supabase session (`session_id` claim) | Owner decision; Dashboard spec §20 lists sign-in | Accepted |
| DEC-049 | 2026-11-17 | Patient-side changes are written to `audit_log` now (dates changed, appointment created/edited/deleted, pregnancy status changed), in the same transaction as the change, with no clinical values in `details` | Owner decision; Dashboard spec §20 | Accepted |
| DEC-050 | 2026-11-18 | The placeholder month drawings stay for the prototype; no openly licensed 9-month set was found (womenshealth.gov stage images are third-party copyrighted, Servier has no series). They must be replaced or removed before release (Journey §7.1) | Owner choice (option a) | Accepted |
| DEC-051 | 2026-11-18 | OpenStax is removed as a Journey content source (spec D9, §7.2, §8.3, S2) | Its live licence is CC BY-NC-SA 4.0 and forbids LLM ingestion; NC licences are not allowed | Accepted |
| DEC-052 | 2026-11-18 | Appointment dates and calendar ranges stay limited to 1900-01-01 .. 2999-12-31 (technical limit, no stricter product rule) | Owner choice | Accepted |
| DEC-053 | 2026-11-18 | The agent's interpretations where the Journey spec is silent are accepted: appointment date/time in the config timezone; calendar milestones hidden after the end; week strip after quick log; past appointments newest first; new_week/new_month for the current week only, hidden after the end; a date-only appointment is "soon" until its day passes; undo does not notify the doctor and keeps any inbox item; "My records" is a short list of links until the records pages exist; the end entry is hidden after the end | Owner review | Accepted |
| DEC-054 | 2026-11-18 | The pregnancy-end entry and heading keep the spec's wording "My pregnancy has ended" (§11.1) | Owner approval | Accepted |
| DEC-055 | 2026-11-18 | Admins are created only by the owner: Supabase dashboard user + `scripts/make_admin.py` (closes the Dashboard spec §21 [OPEN]) | Owner choice; simplest for the prototype | Accepted |
| DEC-056 | 2026-11-18 | Suggested check-ups are on: PMSMA, the 9th of every month from week 14 (2nd and 3rd trimesters), copied with URL, quote and date from the official NHM Maternal Health page into config.yaml (R3); the MCP card gives no week-by-week timing | Owner: use any official source | Accepted |
| DEC-057 | 2026-11-18 | Support helplines: "Ambulance 102, 108" and "Women Helpline 181" from the official Telangana State Portal emergency contacts page (§13.3), shown on the §11.4 support screen; no official counselling line was found | Owner: take the Telangana page | Accepted |
| DEC-058 | 2026-11-18 | The owner accepts R1 (month mapping), R2 (content items and size objects) and R4 (after-pregnancy safety basis) for the prototype. Doctor sign-off (spec §16) is still required before any release; items stay `unreviewed` until then | Owner approval; the owner is not a doctor | Accepted |
| DEC-059 | 2026-11-18 | Patient symptom charts use Recharts (ARCHITECTURE §3): installed recharts 3.10.1 (3.11.0 was one day old) with react-is 19.3.1 forced for the whole tree by an npm override (React 19 needs the matching react-is) | Owner: as recommended (also needed by Phase 5 doctor charts) | Accepted |
| DEC-060 | 2026-11-18 | Urgent button when the backend cannot be reached: the app shows the L1 advice for any warning sign (safety principle §1.3) and keeps the check-in in memory to send later; the rule table is not copied into the app | Owner: as recommended | Accepted |
| DEC-061 | 2026-11-18 | Advice screens use the spec's level names as headings ("Go to hospital now", "Contact your doctor today", "Saved"); message bodies stay "[Text pending doctor approval]" until approved; the patient app bundles a copy generated from `backend/rules/symptoms/messages.yaml`, kept in sync by a test | Owner: as recommended | Accepted |
| DEC-062 | 2026-11-18 | L1 emergency number = Telangana "Ambulance 102, 108" (DEC-057 page); national mental-health helpline (D15) = Tele MANAS 14416 / 1-800-891-4416, copied from the PIB (MoHFW) release of 29 May 2024 | Owner: as recommended | Accepted |
| DEC-063 | 2026-11-18 | PUQE-24 question and answer wording copied word for word from the official S5 sheet (point markers removed); bands stay as the spec (3-6 mild); the sheet's "4 - 6" is flagged for the rule review (A2) | Owner: fetch the sheet (E); spec rule tables are the build source | Accepted |
| DEC-064 | 2026-11-18 | After a pregnancy has ended, the Log and Urgent screens show the after-pregnancy safety message and helplines instead of the pregnancy form (postpartum out of scope, D1); symptom history stays visible | Owner: as recommended | Accepted |
| DEC-065 | 2026-11-18 | "Have not yet felt the baby move" is offered when the pregnancy week is unknown (safety principle §1.3) | Owner: as recommended | Accepted |
| DEC-066 | 2026-11-18 | Migration 0003 (symptom_checkins, symptom_logs) tested on alovia-test, then applied to the main project | Owner: as recommended | Accepted |
| DEC-067 | 2026-11-19 | The check-in examples in Symptom spec §10 and API.md §5 are corrected to `matched_rules: ["L1-03"]`: rule L2-07 excludes a headache that matched L1-03/L1-04, and the rule tables are the source of truth (§0 rule 4, §14 test 1) | Owner approval | Accepted |

## Template for new entries

```
## DEC-0xx — <title>
Date: YYYY-MM-DD   Status: Accepted
Context: what problem existed
Decision: what was decided
Alternatives: …
Reason: why
Consequences: benefit / trade-off
```

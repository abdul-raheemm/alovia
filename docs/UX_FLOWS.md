# UX Flows — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
Detailed rules for each step live in the module specs. This document fixes the **order of screens** and the **states** every screen must handle.

---

## 0. Standard states (every data screen)

| State | Behaviour |
|---|---|
| Loading | Skeleton placeholders in the shape of the content; no spinners longer than 300 ms without a skeleton |
| Empty | Friendly one-line message + the main action (e.g. "No symptoms logged yet" + "Log a symptom") |
| Error | Plain message from `docs/ERROR_HANDLING.md`, a Retry button, and no technical detail |
| Success | Short confirmation (toast), then return to the previous context |
| Offline / backend asleep | "Connecting… this can take up to a minute the first time" (Render cold start), then error state if it fails |

The **urgent button** and **safety messages are never hidden** by loading or error states.

---

## 1. Patient app

### Flow P1 — Sign up through the doctor's invite link (DEC-024)
1. The patient opens the invite link from her doctor (`<patient-app>/join?code=…`). The app checks the code (`GET /invites/{code}/check`).
   - Invalid, used or expired: "This invite link isn't valid. Please ask your doctor for a new one." No sign-up form.
2. Landing page without a link: what Alovia is, medical disclaimer, **Sign in**, links to legal pages, and "New here? Ask your doctor for an invite link." (no open sign-up).
3. Sign up (only from a valid link): email, password, **"I am 18 or older" checkbox**, **consent checkbox** (unticked) linking Privacy Policy, Terms and the app-wide consent text (`docs/legal/CONSENT_TEXT.md`).
4. Email confirmation (Supabase Auth).
5. First sign-in → the backend links the login to the invited record (`POST /patient/link`) → Flow P3.
- **Failure:** clear field errors; existing email → "An account with this email exists. Sign in instead."

### Flow P2 — (merged into P1)
Linking happens automatically from the invite link. A signed-in patient is always linked to at least one doctor.

### Flow P3 — Onboarding dates (Journey spec §5)
1. Choose: last period date / due date from doctor / ultrasound result.
2. Enter date(s) → validation → home.
- **Skip** allowed: home shows the onboarding card only.

### Flow P4 — Home (Journey spec §4.3)
Header (weeks + days, due date, "estimate" label) → urgent button → baby card → this stage → quick log → weekly summary → next appointment → status cards. Notification bar at top; nav bar at bottom (phone) / side (laptop).

### Flow P5 — Log a symptom (Symptom spec §4)
1. Log symptoms → Warning signs group (top) + Everyday symptoms.
2. Select → details → Submit.
3. Result screen: L1 "Go to hospital now" / L2 "Contact your doctor today" / L0 "Saved".
- L1 screen: large, high-contrast, emergency number `[OPEN]`, MCP card reminder, "I understand" button. No animation.

### Flow P6 — Urgent button
Any screen → urgent button → Warning signs list only → one tap + Submit → L1/L2 advice.

### Flow P7 — Month cards and calendar
Home → swipe month cards → month detail. Calendar tab → month view with markers → tap a day → day details.

### Flow P8 — Appointments
Appointments tab → list (upcoming / past) → Add → date, optional time, title, note → Save. Doctor-added items show "Added by your doctor" and cannot be edited.

### Flow P9 — Genetic check (Genetic spec §4)
More → Genetic risk → consent reminder → haemoglobin section → haemophilia entry question → Marfan entry question → consanguinity → Submit → result screen (calculated with "Review with your doctor", or no number with next step) → later: doctor's note.

### Flow P10 — Results and doctor notes
More → My results: only results the doctor shared (plain-language text + doctor message). Doctor notes tab: shared notes, newest first.

### Flow P11 — Pregnancy ended (Journey spec §11)
More → "My pregnancy has ended" → three choices → "inform my doctor?" (no default) → confirm → support/safety screen → quiet home. Undo within 7 days.

### Flow P12 — Settings and privacy
Settings → theme (light / dark / system) → reduce motion → pregnancy dates → linked doctor → legal pages → **Request deletion of my data** (confirmation screen explaining what is deleted) → sign out.

### Flow P13 — Knowledge assistant (Phase 7)
More (or "Ask about this week") → chat → answer with Sources panel → feedback.

---

## 2. Doctor app

### Flow D1 — Sign in
Doctor accounts are invited by the admin. Invite email → set password → sign in → Home.

### Flow D2 — Home
Needs-attention inbox (top) + patient list (sorted per Dashboard spec §6). Search and filters.

### Flow D3 — Create patient and invite
New patient → name (+ optional age, notes) → Save → "Invite patient" → invite link shown with a Copy button → doctor sends it to the patient (WhatsApp, SMS, email — outside the app). Expires in 7 days; a new link replaces an unused old one.

### Flow D4 — Enter CTG or vitals
Patient → Fetal or Maternal tab → form (units, range warnings) → Run prediction → result with explanation and limitations → saved.

### Flow D5 — Share a result
Result → Share with patient → preview (template + optional message; AI draft when enabled) → Confirm.

### Flow D6 — Review inbox items
Inbox item → opens the record → act → Mark as seen.

### Flow D7 — Genetic review
Genetic review queue → assessment → Confirm with note **or** Correct inputs → reviewed.

### Flow D8 — Records, notes, appointments, dates
Patient tabs: upload/download records; write private or shared notes; add appointments; set clinician-confirmed due date; set pregnancy ended.

### Flow D9 — Rule review
Rule review → module → each row: checked + comment → Export sign-off.

---

## 3. Admin (inside the doctor app, admin role only)

### Flow A1 — Invite a doctor
Admin → Doctors → Invite (email, name, specialty) → invite sent.

### Flow A2 — Assign doctors
Admin → Assignments → search patient → add/remove doctors → set primary. Removing the last doctor is blocked.

### Flow A3 — Activity log
Admin → Activity log → filter by user, action, date.

### Flow A4 — Data deletion requests (Phase 8)
Admin → Deletion requests → review → Execute → confirmation logged.

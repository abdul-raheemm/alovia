# Product

<!-- impeccable:product-schema 1 -->

> Durable product truth for design work (written by `/impeccable init`, 2026-11-21, owner-confirmed).
> Visual rules live in `docs/DESIGN_SYSTEM.md` (pointed to by the root `DESIGN.md`); the redesign
> brief is `docs/FRONTEND_REDESIGN.md`. Where this file and the specs disagree, the specs and
> `CLAUDE.md` win.

## Platform

web

## Users

- **Patients:** pregnant women in India (Hyderabad / Telangana focus), 18 or older, English
  readers, using a smartphone. They follow their pregnancy week by week, log symptoms, learn what
  is typical at their stage and, above all, learn when to seek care. They also see their
  appointments, their doctor's shared notes and results their doctor chose to share.
- **Doctors:** obstetric doctors managing several pregnant patients, mostly on a laptop, sometimes
  on a phone. Their first job is to see who needs attention; then they enter clinical values,
  review patient-entered data and decide what the patient sees.
- **Admins:** manage doctor accounts and doctor-patient assignments and read the activity log.
  They never see clinical data.

## Product Purpose

One connected system: a pregnant woman follows her pregnancy, logs symptoms and gets safe,
sourced information, while her own doctor sees what matters and gets explainable decision
support. Success means earlier attention to warning signs, a woman who knows who to contact and
how fast, and a doctor who sees the right patient first.

## Positioning

The woman's own pregnancy journey is the home of the product, connected to her own doctor.
Safety advice comes from fixed, doctor-signed rules computed on the server, never from AI. AI only
drafts for the doctor, who approves. There is no combined risk score, and no health content is
ever locked, sold or advertised against.

## Operating Context

- Patient app: a mobile-first installable web app (PWA), used in short moments during the day;
  it must also look properly designed on a desktop. Doctor app: desktop-first web, also usable
  on a phone.
- The patient's day-to-day: check the week, log a symptom, press the always-visible urgent button
  when something is wrong, read a short "this stage" card, look back at the calendar.
- The doctor's day-to-day: a needs-attention inbox, a patient list in priority order, patient
  tabs (predictions, genetic review, symptoms, records, notes, appointments, pregnancy status),
  rule review and admin.
- India's MCP card (Mother and Child Protection card) and official Government of India /
  Telangana helplines are the reference points for danger signs and phone numbers.

## Capabilities and Constraints

- Built so far (release 0.5.0): pregnancy journey (dates, month cards, calendar, appointments,
  notifications, pregnancy end), symptom tracking with server-side red-flag levels (L0, L1, L2)
  and PUQE-24, genetic risk (rule-based inheritance estimates), doctor dashboard, admin.
- Later: AI drafts for doctors (flags off until a free LLM is chosen), a sourced knowledge
  assistant, security hardening, deployment.
- Red-flag levels are computed only on the backend; the apps show the level and the message key.
- Clinical wording comes only from doctor-approved message keys or sourced knowledge-base content;
  texts without approval show "[Text pending doctor approval]". Baby content is always "a typical
  baby at this stage", never "your baby".
- Baby content, the ring and the month image disappear when a pregnancy ends.
- Synthetic or test data only until security hardening is complete.
- Navigation items, the month map, durations, draft time and message keys come from config, never
  from code.
- Undecided (do not invent): the LLM provider, the estimate band on the ring, "nothing to report
  today", back-filled check-ins, empty states for history and calendar, final typography
  (`docs/FRONTEND_REDESIGN.md` section 15).

## Brand Commitments

- Name: **Alovia**. Logo: a letter mark "A" on a lavender circle until a real logo exists.
- Voice: patient side warm, short sentences, no jargon, never alarming unless urgent, never
  "normal" or "nothing to worry about"; doctor side precise, neutral, clinical terms allowed.
- The colour palette is fixed by the owner (`docs/DESIGN_SYSTEM.md` section 3). Red is reserved
  for L1 red flags, errors and destructive actions.
- No ads, launch modals, promo banners, padlocks or paywalls.

## Evidence on Hand

- Nine month illustrations supplied by the owner and reported as doctor-approved (stock images,
  watermarked previews; prototype and demo use only, licence or replace before public release).
- Size comparisons: Microsoft Fluent Emoji (MIT) with WHO and womenshealth.gov values.
- Prototype journey content with sources in `backend/content/`; fetal and maternal ML models
  trained on public datasets (UCI Cardiotocography, Hossain 2025, both CC BY 4.0).
- Absent, and never to be fabricated: patient testimonials, real patient data, usage numbers,
  clinical validation results, doctor-approved wording for the pending texts.

## Product Principles

1. **Safety before delight.** The urgent path is always one tap away and nothing competes with it.
2. **The doctor decides.** Rules and AI support; every clinical outcome a patient sees passed a
   doctor or a doctor-signed rule.
3. **Sourced or silent.** Show a source, or show nothing; never a guess.
4. **Calm by default.** No alarm, celebration or motion unless it carries meaning; none on L1.
5. **Her data, her doctor, nobody else.** Access is per assigned doctor; admins see no clinical data.

## Accessibility & Inclusion

- WCAG 2.1 AA: text 4.5:1, large text and UI shapes 3:1; colour is never the only signal.
- Touch targets at least 44 by 44 px; patient body and input text at least 16 px.
- `prefers-reduced-motion` and the in-app "Reduce motion" setting are respected everywhere.
- Recorded exception: the pregnancy ring marker is drag-only with no keyboard path; all week
  content stays reachable through month cards and previous/next week buttons
  (`docs/FRONTEND_REDESIGN.md` section 7.2).

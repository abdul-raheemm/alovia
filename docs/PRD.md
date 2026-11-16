# Product Requirements Document — Alovia

**Version:** 3.0 (replaces `archive/PRD_v2.md`)
**Date:** 2026-11-16
**Owner:** Raheem (3-person capstone team, MJCET, AI & DS)
**Status:** Approved for build. Items tagged `[OPEN]` are not decided; do not build guesses for them.

---

## 1. Product Overview

**Product name:** Alovia
**One-line description:** A pregnancy companion web app for women, with a doctor dashboard, that tracks the pregnancy journey and symptoms, gives safe educational guidance, and supports doctors with explainable AI risk predictions.
**Product type:** Two web applications (patient app, doctor app) sharing one backend. Academic capstone prototype.
**Primary platform:** Web, usable on mobile phones and laptops. The patient app can be added to the phone home screen (installable web app).

**Core idea (the project's novelty):** Alovia is **woman-centric**. The patient's Pregnancy Journey is the home of the product; clinical tools support it. AI supports doctors but never replaces them (human-in-the-loop).

---

## 2. Problem

- Pregnancy apps for women focus on lifestyle content and give no clinical link to their own doctor.
- Clinical decision-support tools are doctor-only and disconnected from the woman's daily experience.
- Generic AI chatbots can give unverified or unsafe medical answers.
- In India, official danger-sign guidance (MCP card) and haemoglobin-disorder screening are recommended, but tracking and follow-up are fragmented.

**Current alternatives:** consumer apps (week-by-week content, trackers), hospital systems (clinician-only), general chatbots.

---

## 3. Goals

**Primary goal:** one connected system where a pregnant woman follows her pregnancy, logs symptoms and gets safe, sourced information, while her doctor sees what matters and gets explainable AI support.

**Secondary goals:**
- Earlier attention to warning signs through rule-based red flags.
- Transparent, rule-based genetic inheritance estimates with counselling guidance.
- Explainable ML predictions (SHAP) for fetal and maternal risk.
- A grounded, cited knowledge assistant.
- A v1 foundation that can be extended.

---

## 4. Target Users

### Patient — "Priya"
Pregnant woman in India (Hyderabad/Telangana focus), smartphone user, English reader, 18 or older (see §11).
- **Needs:** know what stage she is at; know what is typical; know when to seek care; record symptoms; see her doctor's notes and appointments.
- **Pain points:** generic or alarming content; unclear when a symptom is urgent; information scattered.

### Doctor — "Dr. Rao"
Obstetric doctor managing several pregnant patients.
- **Needs:** see who needs attention first; enter clinical values and get explainable predictions; review patient-entered data; share results safely.
- **Pain points:** too many screens; black-box AI; patients' symptoms between visits are invisible.

### Admin
Project/platform administrator: creates doctor accounts, assigns doctors to patients, views the activity log. Never sees clinical data.

---

## 5. User Stories

**Patient**
- As a patient, I want to enter my last period date or my doctor's due date so that the app shows my current week.
- As a patient, I want a home screen that shows my week, a typical baby illustration and size, and what is typical now.
- As a patient, I want to log symptoms quickly and be told immediately if I should seek care.
- As a patient, I want an always-visible urgent button.
- As a patient, I want to enter what I know about my and my husband's genetic status and learn the chance of inherited conditions, with a doctor reviewing it.
- As a patient, I want to see my appointments, my doctor's notes and results my doctor has shared.
- As a patient, I want to stop the journey gently if my pregnancy ends.
- As a patient, I want to ask pregnancy questions and get answers with sources (later phase).
- As a patient, I want to request deletion of my data.

**Doctor**
- As a doctor, I want a list of my patients with urgent ones first.
- As a doctor, I want to enter CTG values or maternal vitals and see a prediction with its explanation and limitations.
- As a doctor, I want to decide when and how a result is shared with the patient.
- As a doctor, I want to review genetic assessments and symptom histories.
- As a doctor, I want to upload records, write notes and add appointments.
- As a doctor, I want AI drafts (summary, messages, notes) that I can edit before use.

**Admin**
- As an admin, I want to invite doctors and assign them to patients.

---

## 6. Core Features (summary; full rules in `docs/modules/`)

| # | Module | Purpose | Spec |
|---|---|---|---|
| 4 | **Pregnancy Journey** | Patient home: dates, gestational age, 9 month cards, size comparison, calendar, appointments, notifications, pregnancy-end flow | `modules/pregnancy_journey_module_spec.md` |
| 7 | **Symptom Tracking** | Logging, MCP-card-based red flags (L1/L2), PUQE-24, doctor-only pattern changes | `modules/symptom_tracking_module_spec.md` |
| 3 | **Genetic Risk Assessment** | Rule-based inheritance estimates (haemoglobin group, haemophilia, Marfan) with doctor review | `modules/genetic_risk_module_spec.md` |
| 1, 2 | **Fetal and Maternal Risk (ML)** | XGBoost + SHAP predictions entered by doctors | `modules/ml_models_spec.md` |
| 6 | **Doctor Dashboard + Admin** | Patient list, inbox, data entry, sharing, reviews, records, notes, appointments, AI drafts, rule review | `modules/doctor_dashboard_module_spec.md` |
| 5 | **Knowledge Assistant (RAG)** | Cited answers from the curated knowledge base, strict safety rules | `modules/rag_assistant_module_spec.md` |

**Acceptance criteria and edge cases** for each feature are in its spec (Tests and Do-not sections) and in `docs/TESTING.md`.

**Cross-cutting features**
- Sign-in for patients, doctors and admins (Supabase Auth); one app-wide consent at sign-up.
- Legal pages: privacy policy, terms of use, storage/cookie notice, medical disclaimer (`docs/legal/`).
- Data deletion request (`docs/SECURITY.md` §7).

---

## 7. Non-Goals (v1)

- Combined or weighted overall risk score (retired).
- Diagnosis, treatment advice, medicine dosing.
- Predicting or revealing the baby's sex (PCPNDT Act).
- Postpartum features, newborn tracking.
- Push notifications (in-app only), email marketing.
- Payments of any kind.
- OCR / reading uploaded reports; automated genetic report reading.
- Regional languages (English only).
- Multi-clinic (multi-tenant) support.
- Clinical use with real patients (prototype uses synthetic/test data only).

---

## 8. MVP Scope

**Must have:** Journey, Symptom Tracking, Genetic Risk, ML predictions through the dashboard, Doctor Dashboard + Admin, sign-in, legal pages, deletion request, both themes (light/dark), mobile + laptop layouts.

**Nice to have:** AI draft features (on when the LLM is chosen), installable patient app (PWA), suggested check-up dates (when the official schedule is copied).

**Future:** RAG assistant (Phase 7, after the knowledge base), postpartum, regional languages, more genetic conditions, OCR.

---

## 9. Success Metrics

| Metric | Target |
|---|---|
| Red-flag rules | 100% of rule tests pass; urgent chat messages caught 100% in the evaluation set |
| Genetic engine | 100% of rule-row tests pass (45 haemoglobin pairs + haemophilia + Marfan) |
| ML regression | Every confidence value and top SHAP factor identical to the old backend for the reference cases |
| RAG (Phase 7) | Citation validity 100% after checks; refusals correct; latency within 3–5 s (warm) |
| Performance | Prediction < 1–2 s; dashboard load < 2 s (demo data, warm service) |
| Accessibility | WCAG 2.1 AA checks pass on core screens |
| Usability | Patient can onboard and log a symptom in under 2 minutes in a test session |

---

## 10. Constraints

- **Technical:** free tiers (Supabase free, Render free, Vercel Hobby); cold starts on Render; Supabase 500 MB database limit.
- **Team:** 3 students; one builder per module; review by Raheem.
- **Design:** soft lavender accent; separate patient and doctor looks; light + dark themes.
- **Legal:** India's DPDP Act and Rules (phased to May 2027), PCPNDT Act, CDSCO medical device software guidance (see `docs/SECURITY.md` §10), source licences (NHS OGL, etc.).
- **Timeline:** academic semester `[OPEN]` exact dates.

---

## 11. Assumptions

- All data is synthetic or test data until a compliant setup exists.
- Users are 18 or older in v1 (DEC-023; see `docs/legal/COMPLIANCE_CHECKLIST.md` item 17).
- Doctors enter clinical values; patients enter symptoms, pregnancy dates and genetic answers.
- One pregnancy per patient record.
- English only.

---

## 12. Open Questions

Collected from all specs; each spec lists its own. Main ones:
- LLM and embedding provider (`[OPEN]`).
- Helpline and emergency numbers (copied from official pages during build).
- Business/contact details for legal pages.
- Training data files and notebook test cases for ML regression and training ranges.
- Doctor reviewer for rules, illustrations and message texts.

---

## 13. Definition of Done

A module is done when:
- [ ] Its spec's requirements are implemented.
- [ ] Its tests (spec + `docs/TESTING.md`) pass.
- [ ] Lint, type checks and builds pass for backend and frontends.
- [ ] The critical flows for that module work on a phone-sized and a laptop-sized screen, in light and dark themes.
- [ ] Documentation and tracking files are updated (`PROGRESS.md`, `HISTORY.md`, `CHANGELOG.md`, and any changed doc).
- [ ] The owner has reviewed and approved the change.

Security hardening is done in Phase 8 (`docs/SECURITY.md`).

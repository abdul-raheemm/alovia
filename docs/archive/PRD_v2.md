# Product Requirements Document (PRD)
## Alovia — AI-Powered Pregnancy Monitoring and Clinical Decision-Support System

**Version:** 2 (supersedes 1.1)
**Date:** 2026-10-11
**Audience:** Internal team reference (not a department submission document)
**Status:** Living document. Sections marked `[TBD]` are open items. Sections marked `[ON HOLD]` are deliberately paused and must not be built until revised.

---

## Change Log (v1.1 → v2)

| # | Section | Change |
|---|---|---|
| 1 | §1, §2 | Overview and goals now include genetic risk assessment and symptom tracking. |
| 2 | §3 | Patients now enter their own symptoms and pregnancy dates; clinical data stays doctor-entered. Who enters genetic data is `[TBD]`. |
| 3 | §4, §4.3 | Module 3 changed from the Pregnancy Risk Score (definition void, module retired) to **Genetic Risk Assessment** (rule-based). The combined risk score is not part of this version. |
| 4 | §4.4 | Journey redefined: nine illustrated month cards, pregnancy calendar, due date from LMP or a clinician-confirmed date. Risk-tier personalization removed. |
| 5 | §4.6 | Dashboard shows fetal, maternal and genetic results separately, plus symptom histories. |
| 6 | §4.7 | New Module 7: Symptom Tracking. |
| 7 | §6, §7, §8 | Out-of-scope items, open items and versioning note updated. |

---

## 1. Overview

Pregnancy requires continuous monitoring of maternal and fetal health, timely identification of potential risks, and access to reliable, personalized health information. Existing digital tools are split between consumer-facing tracking apps (lifestyle-focused, no clinical insight) and enterprise clinical decision-support systems (clinician-only, disconnected from patient life).

This project builds a unified platform that combines machine-learning-based risk prediction, rule-based genetic risk assessment, symptom tracking, a grounded AI knowledge assistant, personalized pregnancy guidance, and clinician oversight, following a **human-in-the-loop** model where AI supports, but never replaces, professional medical judgment.

---

## 2. Goals

- Enable earlier identification of maternal and fetal health risks through ML-based prediction.
- Help parents understand potential inherited risks to their child through transparent, rule-based estimates, with guidance to seek genetic counselling.
- Give patients personalized, stage-specific pregnancy guidance instead of generic content.
- Let patients record symptoms over time, highlight those that may need prompt medical attention, and share the history with their doctor.
- Provide patients a safe, source-grounded way to get answers to pregnancy questions without receiving unverified or hallucinated medical advice.
- Give doctors a consolidated view of patient risk, trends, and AI-generated insights (with explanations) to support, not replace, clinical decisions.
- Establish a foundation (v1) that can be extended in future iterations. This is explicitly not a final or complete product.

---

## 3. Users & Roles

| Role | Description |
|---|---|
| **Patient** | Pregnant individual using the patient-facing web app. In v1 the patient **views** their pregnancy information, fetal, maternal and genetic results and personalized journey content, **records symptoms and pregnancy dates**, and uses the knowledge assistant. |
| **Doctor** | Healthcare professional managing multiple patients via the doctor-facing web app. In v1 the doctor **enters all clinical data** (CTG values, vitals) and reviews results, trends, and records. |
| **Admin** | Manages platform-level concerns (user accounts, doctor-patient assignment, system oversight). Included for prototyping purposes. **Admin is a role only for now; it may become a full module in the future.** |

**Data entry:** clinical inputs (CTG values, vitals) are doctor-entered, matching real clinical workflow. Patients enter their own symptoms and pregnancy dates (last menstrual period or a clinician-confirmed due date). Who enters the parents' genetic information is not yet defined `[TBD]`. Whether any further inputs become patient-enterable is open `[TBD]`.

**Access model:**
- One doctor manages multiple patients.
- Single-deployment system (not multi-tenant across separate clinics/hospitals) for this version.
- A patient can only access their own data; a doctor can only access their assigned patients' data. These rules are enforced by the backend API (see TRD §5).

---

## 4. Modules (Feature Scope)

Seven modules are in the prototype scope. Module numbers are kept stable so that references across documents do not shift. Module 3 was the Pregnancy Risk Score, whose definition is void; it is replaced by **Genetic Risk Assessment**. **Symptom Tracking** is Module 7.

### 4.1 Fetal Risk Prediction
- ML classification of fetal health status (Normal / Suspect / Pathological) using 21 CTG-derived parameters.
- Dataset: UCI Cardiotocography dataset (2,126 records, 2,116 after removal of 10 exact duplicates), labeled by expert obstetricians.
- Model: tuned XGBoost, selected by cross-validation over Logistic Regression, Random Forest and SVM.
- Explainability via SHAP: surfaces the contributing factors behind each prediction, not just the label.
- **Input method (v1):** the doctor enters the 21 values manually.
- **Known limitation `[documented]`:** the 21 inputs are computer-derived CTG measurements (the training data was produced by SisPorto-style analysis software). Real-world CTG interpretation is mostly done by reading the trace by eye, and computerized CTG analysis is not universally available, which is more common in well-resourced hospitals. This affects how usable the fetal model is for settings without such analysis. Auto-filling the values from a photo of a CTG report was explored and found not viable as a general feature (see §6). **How Alovia addresses input availability is on hold and not yet decided `[ON HOLD]`.**

### 4.2 Maternal Risk Prediction
- ML classification of maternal risk level (Low / Mid / High).
- Inputs (8 features): age, systolic blood pressure, diastolic blood pressure, body temperature, heart rate, BMI, HbA1c, fasting blood glucose.
- Dataset: the 8-feature multi-facility dataset by Hossain et al. (2026), 6,058 records after cleaning to the paper's published criteria.
- Model: tuned XGBoost with SHAP explainability.
- **Scope decision:** a single multi-class model for general risk level, not separate per-condition models (preeclampsia/GDM/anemia). Condition-specific sub-models are a possible future addition, pending dataset availability.

### 4.3 Genetic Risk Assessment
- Estimates the likelihood that a child inherits selected genetic disorders from both biological parents, using predefined inheritance rules. **Rule-based; no trained ML model in this version.**
- **Inputs:** for each parent, known genetic disorders, whether affected or a known carrier, and relevant genetic test findings, entered through structured forms. Automated interpretation of uploaded genetic reports is not required. Who enters this information is `[TBD]`.
- **Method:** a deterministic rule engine matches the parents' findings against a small, carefully selected set of conditions with well-established inheritance patterns (a Punnett-square calculation for selected Mendelian patterns). The supported conditions are `[TBD]`. Every rule and worked example must be checked against reliable medical or genetics references.
- **Output:** for each assessed condition, the probability that the child is affected, the probability of being a carrier where relevant, and a short plain-language explanation. Example: if both parents are carriers of the same autosomal recessive condition, each pregnancy has a 25% chance of an affected child, 50% of a carrier and 25% of neither.
- If the input is insufficient for a reliable estimate, the module says that further genetic information or professional assessment is needed. It recommends genetic counselling when risk is indicated.
- Results are preliminary educational estimates, not a diagnosis or a substitute for clinical genetic testing or counselling, and must not present a condition as certain. Family history alone cannot confirm carrier status.
- Operates independently of the fetal and maternal prediction models.
- Parental genetic information is sensitive; consent requirements are `[TBD]` (see TRD §5).
- **Future scope:** more supported conditions and more complex inheritance patterns, which need different calculations.

### 4.4 Personalized Pregnancy Journey
- Week/month-specific content driven by the patient's gestational age: fetal development info, expected maternal changes, do's/don'ts, nutrition guidance, warning signs, checklists.
- **Nine-month timeline:** one illustration per month of pregnancy, shown as interactive month cards (illustration, month, corresponding gestational-week range, short milestones). Selecting a card opens a detail view with a larger illustration, milestones, common maternal changes, common symptoms, and general prenatal-care guidance including topics to discuss with a healthcare professional. Illustrations show typical stages, not an individual fetus, and must be appropriately licensed, medically reviewed artwork.
- **Pregnancy calendar:** shows estimated gestational age, current week, approximate month, estimated due date, milestones (such as a new week or month) and appointments entered by the user.
- **Onboarding dates:** the user enters the first day of the last menstrual period (LMP), or a clinician-confirmed due date or ultrasound-based gestational age. An LMP-based estimate uses the conventional 280-day method and is labelled an estimate; clinician-confirmed dating takes precedence.
- **Gestational age** is derived from a stored **due date** (see DRD), in weeks and days for calculations, so it stays current as time passes. Months are display labels only, because months do not map to fixed four-week periods.
- Content is predefined and medically reviewed, selected by gestational age. It is not generated by an AI model.
- Recent symptom entries (Module 7) may be summarized on the current month's page.
- Risk-tier personalization is removed along with the old Module 3.

### 4.5 Pregnancy Knowledge Assistant (RAG Chatbot)
- Answers pregnancy-related questions using Retrieval-Augmented Generation grounded on a curated, trusted knowledge base, not open-ended model knowledge.
- Personalizes answers using the patient's gestational age where relevant.
- **Hard requirement:** never provides diagnosis or treatment advice. It redirects such questions to "consult your doctor". This is a non-negotiable ethical guardrail.
- **Source citation is required** in responses (previously "where feasible"). The knowledge base labels every document with its publisher, URL, review date and licence so that citations are possible.
- **Target scope:** users in India (with Telangana/Hyderabad content where official sources exist). English is the primary language; official regional-language (Telugu/Hindi/Urdu) material is optional and low priority.
- **Knowledge base:**
  - Minimum 600 documents, ideally 1,000+, roughly up to 3 million words in total (sized for the free database tier).
  - Sources are limited to trusted organizations: international bodies (e.g. MedlinePlus, CDC, NICHD/NIH, WHO, NHS, NICE, Australian Government health sites, HSE Ireland, UNICEF/UNFPA), Indian national sources (e.g. MoHFW, NHM, National Health Portal, ICMR, ICMR-NIN, POSHAN Abhiyaan, Ministry of Women & Child Development, FOGSI patient material), and official Telangana/Hyderabad sources.
  - Only content whose licence allows reuse (Tier A and Tier B, see knowledge base guide) is copied. Content that is copyrighted without clear reuse permission (e.g. ACOG, RCOG leaflets, March of Dimes, Mayo Clinic, BabyCenter) is recorded as reference only and not copied. **ACOG, named as a candidate in v1.0, is therefore not a copyable source.**
  - Each source's terms are checked for use in AI/retrieval systems and excerpt reuse before it is used.
  - Includes explainers for the vitals and CTG concepts behind the risk models. Whether the assistant may explain a patient's own risk result is not yet decided `[TBD]`.
- Regional mix aimed for: international ≥ 40%, India national ≥ 35%, Telangana/Hyderabad as quality content allows.
- LLM choice: `[TBD]`.

### 4.6 Doctor Dashboard
- Patient list/overview: gestational age, **fetal, maternal and genetic results shown separately**. There is no combined risk score in this version.
- Drill-down per patient: health trends over time, AI risk assessments with contributing factors (a rule breakdown for the genetic result), symptom histories, medical records.
- Real, working medical report upload/handling (ultrasound, blood reports, prescriptions), functional for v1, not mocked. Files are stored in Supabase Storage and accessed through the backend.
- Doctor visibility of symptom histories depends on patient consent `[TBD]`.

### 4.7 Symptom Tracking
- Patients log symptoms such as nausea, vomiting, fatigue, headaches, abdominal discomfort, back pain, breast tenderness, food cravings, appetite changes and mood changes. For pain or discomfort they can also record the affected body region, duration, severity, time of occurrence and notes.
- Entries are organized by date and tied to the pregnancy timeline. History is shown over time (frequency, severity, duration) so users and doctors can review changes. The rules for flagging pattern changes are `[TBD]`.
- **Safety:** rule-based checks defined from clinical guidance flag potentially urgent symptoms (for example severe abdominal pain, heavy vaginal bleeding, fainting) and prompt the user to seek medical assessment. The module never assumes a symptom is harmless because of the pregnancy stage, does not diagnose, and keeps educational content, user-reported symptoms and clinically confirmed information distinct. The red-flag rule set and its source are `[TBD]`.
- Symptom histories are visible to the patient's doctor on the dashboard; the consent mechanism is `[TBD]`.

---

## 5. Non-Functional Expectations (Prototype-Level)

These are realistic targets for a prototype, not production-grade SLAs:

| Area | Target |
|---|---|
| ML prediction response (maternal/fetal) | Under 1-2 seconds |
| RAG chatbot response | Under 3-5 seconds |
| Dashboard page load | Under 2 seconds (demo-scale data) |
| Concurrency | Designed for demo-scale (single-digit concurrent users), not production load; scaling explicitly out of scope for v1 |
| Security | Role-based access (patient/doctor/admin separation) enforced by the backend API. All database access goes through the backend. Full security hardening is not required for the prototype, but the minimum database lockdown in TRD §5 applies. |

**Cold-start note:** if the backend runs on a free hosting tier, the first request after inactivity can be slow and miss the targets above. The targets apply to a warm service unless stated otherwise.

---

## 6. Out of Scope (v1)

- Multi-tenant support (multiple clinics/hospitals): single deployment only.
- Production-grade load handling / scaling.
- Full security hardening (encryption at rest, penetration-tested auth, rate limiting, etc.): basic role separation only.
- Condition-specific maternal models (preeclampsia/GDM/anemia individually).
- Auto-filling the 21 CTG inputs from a photo or scan of a CTG report (explored and found not viable as a general feature: CTG output is mostly a waveform, and the 21 values come from specialized signal-processing software).
- Clinical validation on real patients. Both models are trained on public datasets and have not been validated on Alovia's target population.
- Combined (weighted) pregnancy risk score: retired from this version; the old Module 3 definition is void.
- A trained ML model for genetic risk, and automated interpretation of uploaded genetic reports (the module is rule-based with manual structured entry).
- AI-generated fetal development content (Journey content is predefined and medically reviewed).
- Diagnosis or interpretation of symptoms beyond rule-based red-flag prompts.
- Real patient data. All data used so far is public or synthetic.

---

## 7. Open Items / Research in Progress

- [ ] Genetic Risk Assessment: supported conditions, who enters parental data, and consent `[TBD]`.
- [ ] Symptom Tracking: red-flag rule set and its clinical source, pattern-change rules, and consent for doctor visibility `[TBD]`.
- [ ] Journey: licensed, medically reviewed fetal illustrations and the source of the content `[TBD]`.
- [ ] How to address CTG input availability in settings without computerized CTG analysis `[ON HOLD]`.
- [ ] Which inputs beyond symptoms and pregnancy dates patients may enter themselves, and how they are validated.
- [ ] Whether the knowledge assistant may explain a patient's own risk result.
- [ ] Final LLM API choice (free-tier/low-cost options being evaluated).
- [ ] Knowledge base collection in progress (see knowledge base guide).
- [x] Maternal risk dataset: closed (8-feature Hossain et al. dataset).
- [x] Module 3: closed. The Pregnancy Risk Score is retired and replaced by Genetic Risk Assessment.

---

## 8. Versioning Note

This is **version 2**. Version 1.1 remains the baseline for comparison. "v1" elsewhere in this document means the first product version (the prototype), not the document version. Future iterations will track changes against this version.

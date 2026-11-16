# Technical Requirements Document (TRD)
## Alovia — AI-Powered Pregnancy Monitoring and Clinical Decision-Support System

**Version:** 2 (supersedes 1.1)
**Date:** 2026-10-11
**Audience:** Internal team reference (not a department submission document)
**Status:** Living document. Sections marked `[TBD]` are open items. Sections marked `[ON HOLD]` are deliberately paused.

---

## Change Log (v1.1 → v2)

| # | Section | Change |
|---|---|---|
| 1 | §1, §2 | Rule-based layer added (genetic inheritance engine, symptom red-flag checks). Calendar library and illustration assets added to the stack. OCR recorded as future scope. |
| 2 | §3 | Data model: genetic assessment, symptom, appointment and journey content entities added; the Module 3 entity removed. |
| 3 | §4.3 | The void Pregnancy Risk Score replaced by Genetic Risk Assessment. |
| 4 | §4.4 | Journey: month cards, calendar, due-date rules; risk-tier variation removed. |
| 5 | §4.6, §4.7 | Dashboard adds genetic results and symptom histories; backend work list extended. |
| 6 | §4.9 | New: Symptom Tracking (Module 7). |
| 7 | §5 | Note on sensitive genetic and symptom data. |
| 8 | §8 | Open decisions updated. |

---

## 1. Architecture Overview

```
React (Patient Web App + Doctor Web App)
   │                              │
   │ sign-in / sign-out only      │ all data requests
   ▼                              │ (Bearer token)
Supabase Auth                     ▼
(issues the JWT)         FastAPI (REST API), hosted on Render
                                  │
          ┌───────────────────────┼─────────────────────────┐
          ▼                       ▼                         ▼
     ML Models              RAG Pipeline          Supabase PostgreSQL
 (XGBoost + SHAP,       (LangChain + pgvector      (SQLAlchemy; includes
  loaded at startup)     + embedding API + LLM)     pgvector tables)
                                                            +
                                                  Supabase Storage
                                                  (private bucket for
                                                   medical reports)
```

- **Frontend:** two separate web apps (patient-facing, doctor-facing) sharing a common design system where practical.
- **Backend:** a single FastAPI service exposing REST APIs consumed by both frontends. **The frontend never reads or writes the database or storage directly.** The only direct contact between the frontend and Supabase is sign-in/sign-out through Supabase Auth.
- **Data layer:** a single Supabase-managed PostgreSQL instance (single deployment, not multi-tenant), with the `vector` extension enabled for the RAG store.
- **ML layer:** maternal and fetal prediction models served by the backend. The RAG pipeline runs as a separate logical component within the same backend service for v1.
- **Rule-based layer:** the genetic inheritance engine and the symptom red-flag checks are deterministic Python logic inside the same backend service. They use no trained model and are not shown separately in the diagram.

---

## 2. Tech Stack

### Frontend
- React.js
- JavaScript
- HTML/CSS
- Tailwind CSS
- Recharts / Chart.js (risk visualizations, health graphs, symptom history)
- A React-compatible calendar library (pregnancy calendar)
- Supabase client library used **for authentication only**

Used for: patient dashboard, doctor dashboard, pregnancy timeline and calendar, symptom log, genetic risk forms and results, risk visualizations, AI assistant interface.

### Backend
- Python
- FastAPI
- REST APIs
- Pydantic (data validation)
- JWT verification of Supabase-issued tokens (see §5)

FastAPI was chosen because the ML models are Python-native, avoiding a cross-language bridge between the API layer and model inference.

### Database
- Supabase-managed PostgreSQL
- SQLAlchemy (ORM) used by FastAPI
- `pgvector` extension for embeddings

**Stores:** patient profiles, pregnancy details, health measurements, fetal data, risk predictions, doctor-patient relationships, medical record metadata, chat history, and the knowledge base documents and chunks. It also stores genetic assessments, symptom logs, appointments, journey content and the genetic condition rules.

### Authentication
- **Supabase Auth** for now. A move to a stronger, backend-controlled JWT scheme is a planned future direction and is not committed (see §5).

### ML Stack (Fetal + Maternal Risk)
- Pandas, NumPy
- Scikit-learn
- XGBoost (**selected for both modules**)
- Matplotlib (evaluation/visualization during development)
- SHAP (explainability, `TreeExplainer`)
- joblib (model persistence)

### Rule Engines (Genetic Risk + Symptom Red-Flag)
- Python functions and conditional logic; deterministic, no trained model.

### RAG / Knowledge Assistant Stack
- Python
- **LangChain** (orchestration; chosen)
- Embeddings: an embedding API `[TBD — provider]`
- Vector store: **pgvector on Supabase** (replaces FAISS from v1.0)
- LLM API: free-to-use / low-cost option `[TBD]`

### Storage (Medical Report Uploads)
- **Supabase Storage**, private bucket, accessed only by the backend.
- Future consideration (not v1 priority): AWS S3 / Cloudinary.
- Future scope (not v1): OCR (Tesseract / EasyOCR) for uploaded reports.
- Fetal development illustrations (Journey): licensed, medically reviewed image assets. They are not patient data, and where they are stored is `[TBD]`.

---

## 3. Data Model (High-Level Entities)

The full specification is in `DRD_v2.md`. In summary:

- **User** (base, linked to Supabase Auth) → Patient | Doctor | Admin (role-based)
- **Patient Profile**: demographics, **due date** (gestational age is derived from it), last menstrual period and how the due date was set, optional link to a patient login
- **Health Measurements / Fetal Data**: submitted inputs for the maternal and fetal models, time-series per patient
- **Predictions**: stored outputs of the maternal and fetal models with SHAP contributing factors, timestamped, append-only
- **Medical Records**: metadata for uploaded files (ultrasound, blood reports, prescriptions) linked to a patient; file bytes live in Supabase Storage
- **Chat History**: RAG assistant conversation logs per patient, with the sources retrieved
- **Doctor-Patient Relationship**: mapping table (one doctor → many patients)
- **Knowledge Base**: document records and embedded chunks for the RAG assistant (not patient data)
- **Genetic Assessments**: parental findings and per-condition results for each run, plus a reference table of supported conditions and their rules
- **Symptom Logs**: dated, patient-entered symptom entries
- **Appointments**: user-entered appointments for the pregnancy calendar
- **Journey Content**: predefined, medically reviewed content by month and gestational week (not patient data)

---

## 4. Module-Level Technical Notes

### 4.1 Fetal Risk Prediction
- **Dataset:** UCI Cardiotocography (id 193). 2,126 records; 10 exact duplicates (confirmed by matching raw signal timestamps) removed, leaving **2,116**. Class distribution: Normal 1,648 / Suspect 293 / Pathological 175.
- **Input:** 21 pre-computed CTG features: `LB, AC.1, FM.1, UC.1, DL.1, DS.1, DP.1, ASTV, MSTV, ALTV, MLTV, Width, Min, Max, Nmax, Nzeros, Mode, Mean, Median, Variance, Tendency`. The raw interval columns are deliberately excluded (upstream of the 21 features, not independent information).
- **Output:** 3-class classification (Normal / Suspect / Pathological) + SHAP contributing factors.
- **Class imbalance:** handled by class weighting (`class_weight='balanced'`, applied through `sample_weight` for XGBoost). SMOTE was evaluated as unnecessary and shelved.
- **Model selection:** Logistic Regression, Random Forest, SVM and XGBoost were compared. A single 80/20 split favoured Random Forest, but 5-fold cross-validation reversed it, so **XGBoost was selected on CV, not on the single split**. Tuned with `RandomizedSearchCV` (50 iterations, 5-fold, scored on macro F1).
- **Results:** CV macro F1 0.922; test macro F1 0.916; Pathological recall 97% (34/35), Suspect recall 85%, Normal recall 96%. Zero Pathological cases were predicted as Normal.
- **Extended testing done:** overfitting check, class-median sanity check, error analysis (errors are mostly adjacent-class boundary confusions), learning curve (close to, but not fully, saturated).
- **Persistence:** joblib model + `feature_order.json`, label mapping and metadata JSON; load-and-verify test passed.
- **Known limitation:** inputs are computer-derived CTG measurements that are not universally available (see PRD §4.1). Approach to be addressed is `[ON HOLD]`. Inputs are entered manually by the doctor.

### 4.2 Maternal Risk Prediction
- **Dataset:** Hossain et al. (2026), BMC Medical Informatics and Decision Making. The raw export (6,103 rows) was cleaned to the paper's published criteria (age outside 15–48, body temperature outside 95.0–104.0 °F, diastolic BP below 50 mmHg), giving exactly **6,058 rows**.
- **Input (8 features):** age, systolic BP, diastolic BP, body temperature (°F), heart rate (bpm), BMI (kg/m²), HbA1c (**mmol/mol**), fasting blood glucose (**mmol/L**). Exact names and order are defined by the saved `feature_order.json`. The two glucose column names were relabeled to their true units; no values were changed.
- **Output:** 3-class classification (Low / Mid / High) + SHAP contributing factors.
- **Class balance:** near-perfect (about 33% each); no class weighting or SMOTE needed.
- **Model selection:** XGBoost selected after a statistical tie with Random Forest in cross-validation (0.9919 vs 0.9921), on secondary grounds (CV stability, shared tooling with the fetal pipeline). Tuned with the same search.
- **Results:** CV macro F1 0.9924; test macro F1 0.9909 (11 errors of 1,212). Zero High-risk cases were predicted as Low. The dataset is highly separable, so results are near its ceiling and should not be read as expected real-world performance.
- **Scope decision:** single multi-class model for v1 (see PRD §4.2).
- **Persistence:** same pattern as fetal; load-and-verify passed.

### 4.3 Genetic Risk Assessment
- Replaces the void Pregnancy Risk Score. A deterministic rule engine; **no trained ML model** in this version.
- **Pipeline:** input processing (validate parental findings, convert to a consistent format) → condition matching (conditions where the combination of parental findings affects the child's risk) → inheritance rules (a Punnett-square calculation for selected Mendelian patterns) → probability calculation (affected, and carrier where applicable) → results generation (structured results, explanation, warnings for incomplete information).
- **Condition data:** supported conditions, inheritance patterns, relevant findings and medically reviewed rules are stored in the database (DRD). The supported set is small and carefully selected `[TBD]`. Every rule and worked example must be checked against reliable medical or genetics references and covered by test cases.
- **Output per condition:** probability of the child being affected, probability of being a carrier where relevant, and a short explanation. If the input is insufficient, the result says that further genetic information or professional assessment is needed. Reference case: two carriers of the same autosomal recessive condition give 25% affected, 50% carrier, 25% neither.
- Results are educational estimates, not a diagnosis. Genetic counselling is recommended when risk is indicated.
- Entry is manual through structured forms; automated interpretation of uploaded genetic reports is not required. Who enters the data is `[TBD]`.
- Independent of the fetal and maternal models. Route-level design is `[TBD]`.
- Future scope: more conditions and more complex inheritance patterns.

### 4.4 Personalized Pregnancy Journey
- Primarily a structured content/rules layer, not ML-driven. Content is predefined and medically reviewed, not generated by an AI model.
- **Input:** current gestational age, derived from the patient's stored due date at query time. Weeks and days are used for calculations; months are display labels only.
- **Due date:** entered at onboarding as the last menstrual period (LMP), or a clinician-confirmed due date or ultrasound-based gestational age. An LMP estimate uses the 280-day method and is labelled an estimate; clinician-confirmed dating takes precedence.
- **Month cards:** nine cards, each with an illustration, month label, gestational-week range and short description from the content store. A detail view adds milestones, maternal changes, common symptoms and general guidance.
- **Calendar:** estimated gestational age, current week, approximate month, due date, week and month milestones, and user-entered appointments, using a React-compatible calendar library.
- Content is curated by the team, stored in the database or structured content files, and served through the API by gestational week or month.
- Risk-tier variation is removed along with the old Module 3.

### 4.5 Pregnancy Knowledge Assistant (RAG)
- **Pipeline:** curated knowledge base files → chunking → embeddings → pgvector store (Supabase) → retrieval → LLM generation → cited response.
- **Knowledge base format:** each document is a Markdown file with a YAML label block (publisher, URL, review date, licence, region, audience, topics, trimester, week range, and safety flags such as `contains_dosage`, `contains_treatment_advice`, `time_sensitive`). The labels are stored with each chunk and used for filtering and citations.
- **Week convention:** gestational weeks counted from the last menstrual period (LMP). The patient's gestational age (§4.4) uses the same convention.
- **Filtering:** retrieval filters on the week range, **not on trimester alone**, because sources draw trimester boundaries differently. Retrieval also filters on audience (patient-facing answers should draw on `patient` or `both` documents).
- **Handling of safety flags** (whether dosage-containing or treatment-advice documents are excluded or restricted in patient answers): `[TBD — decide during the RAG build]`.
- **Guardrails:** the system prompt and retrieval scoping enforce that only grounded, retrieved content informs answers. Explicit refusal/redirect logic applies to diagnostic or treatment questions.
- **Citations are required:** each answer cites the sources of the chunks it used.
- **Size budget:** the knowledge base is capped at roughly 3 million words (about 7,500 chunks) to fit the free database tier of 500 MB. The embedding dimension depends on the chosen embedding provider `[TBD]` and fixes the vector column size, so it must be decided before the tables are created.

### 4.6 Doctor Dashboard
- Consumes: patient list, per-patient trends (BP/weight/glucose/fetal measurements over time), fetal, maternal and genetic outputs with contributing factors (a rule breakdown for the genetic result), symptom histories, uploaded medical records.
- Fetal, maternal and genetic results are shown **separately**; there is no combined score in this version.
- All data is fetched through FastAPI. Real (non-mocked) integration with the backend for v1.

### 4.7 Backend as Built, and Work Required
**Built and verified today:** a single FastAPI service. The `RiskModel` class builds each model's Pydantic input schema from its saved `feature_order.json` (no hardcoded field lists). Both joblib models and both SHAP explainers load at startup. Endpoints: `GET /health`, `GET /schema/fetal`, `GET /schema/maternal`, `POST /predict/fetal`, `POST /predict/maternal`. Two bugs found by testing against real notebook cases were fixed: SHAP array indexing (wrong output for single-row predictions), and SHAP direction labels that did not depend on the predicted class (now relative to it). Every confidence value and top SHAP factor then matched the notebook results. Deployed on Render.

**Work required by the "FastAPI is the only gateway" decision:** today the backend only predicts; patient records and result history are written to Supabase directly by the test frontend. The backend must take over, at minimum:
- verifying the Supabase-issued token and resolving the user's role (§5);
- patient create / read / update, and doctor-patient assignment;
- storing each fetal and maternal prediction (append-only) with its inputs;
- listing a patient's result history and trends;
- medical report upload, listing and download (Supabase Storage);
- the knowledge assistant endpoint and chat history;
- Journey content by gestational week or month, pregnancy dates, due-date calculation and appointments;
- genetic risk assessment (run, store, retrieve);
- symptom logging, history and red-flag checks;
- admin operations.

Route-level design for these is `[TBD]`.

### 4.8 Test Frontend (Temporary)
A Bolt-built test tool exists for verifying the two models end-to-end. It talks to Supabase directly and uses static template text for the patient view. It is a **temporary test tool, not the target architecture**. Before anything is deployed publicly, its direct-access database policies must be removed (see §5) and its function replaced by the real frontends calling FastAPI.

### 4.9 Symptom Tracking (Module 7)
- Patient-entered, dated symptom entries (symptom, severity, duration, body region for pain, time of occurrence, notes), stored per patient and returned as history for charts (Recharts / Chart.js). Entries are tied to the pregnancy timeline through the patient's due date.
- **Red-flag checks:** rule-based, defined from clinical guidance, they prompt the user to seek medical assessment for potentially urgent symptoms (for example severe abdominal pain, heavy vaginal bleeding, fainting). The rule set and its source are `[TBD]`. There is no diagnosis or automated interpretation beyond these rules.
- Rules for flagging worsening or newly appearing symptoms are `[TBD]`.
- Doctors see the symptom histories of their assigned patients; the consent mechanism is `[TBD]`.

---

## 5. Authentication & Security (Prototype Scope)

**Authentication**
- **Supabase Auth** issues the JWT. The frontend uses Supabase **only to sign in and out**; every data request goes to FastAPI with the token as a Bearer header.
- FastAPI verifies the token on every request using the project's Supabase JWT verification key, then looks up the user's role in the application's `users` table.
- Password storage and hashing are handled by Supabase Auth. The application does not store passwords.
- **Planned direction (not committed):** a later move to a stronger, backend-controlled JWT scheme. To keep that move small, token verification should live in one place in the backend (a single dependency or module).

**Authorization (enforced by FastAPI)**
- Role-based access control: Patient / Doctor / Admin.
- Patients are restricted to their own records; doctors are restricted to their assigned patients.
- Genetic and symptom data are sensitive health data. Data minimization, encrypted transport and consent are required before any real-world use; the consent design is `[TBD]`.

**Minimum database lockdown (applies even at prototype stage)**
Because the frontend holds the public Supabase key (needed for sign-in), Supabase's automatic table API would otherwise allow direct reads and writes. Therefore:
- Row-Level Security is **enabled on every table with no policies granting access to the public or signed-in roles** (deny by default). Only the backend, using server-side credentials, accesses the data.
- The Storage bucket for medical reports is **private**.
- The service credentials and database connection string exist only in the backend's environment variables, never in frontend code or the repository.
- The test frontend's open policies are removed before public deployment (§4.8).

**Explicitly out of scope for v1:** full security hardening (encryption at rest beyond the provider's default, penetration testing, rate limiting, etc.), documented as design intent for future iterations.

**Compliance note:** Supabase's free and standard tiers are not HIPAA-compliant. This is not a concern while all data is public or synthetic, but real patient data must not be used without a compliant setup.

---

## 6. Non-Functional Requirements

| Area | Target | Notes |
|---|---|---|
| ML prediction latency | < 1–2s | Classic ML models (RF/XGBoost) are fast even unoptimized. Applies to a warm service. |
| RAG chatbot latency | < 3–5s | Dependent on the LLM API choice `[TBD]`. |
| Dashboard load time | < 2s | At demo-scale data volumes. |
| Concurrency | Single-digit concurrent users | Production-scale load explicitly out of scope. |
| Cold start | Not covered by the targets above | A free-tier backend host can be slow on the first request after inactivity. |

---

## 7. Deployment

- **Backend:** FastAPI on **Render** (Python 3, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`), deployed from GitHub and verified against the live URL.
- **Database, auth and storage:** Supabase.
- **Frontend hosting:** `[TBD, flexible]`.
- **Deployment model:** single instance, single deployment (no multi-tenancy).
- **Things to verify before relying on the free tiers:** Render's free tier can sleep when idle; Supabase's free tier has a 500 MB database limit and may pause inactive projects. Also check, when connecting the backend to the database, whether Supabase's pooled connection string is needed for the host's network setup.

---

## 8. Open Decisions

- [ ] Embedding model/API choice (also fixes the vector dimension).
- [ ] LLM API choice (free/low-cost).
- [ ] Frontend hosting platform.
- [ ] Route-level API design for the backend work in §4.7.
- [ ] Which inputs beyond symptoms and pregnancy dates patients may enter themselves, and validation.
- [ ] Handling of dosage and treatment-advice documents in patient answers.
- [ ] Genetic Risk Assessment: supported conditions, who enters parental data, consent `[TBD]`.
- [ ] Symptom Tracking: red-flag rule set and its source, pattern-change rules, consent for doctor visibility `[TBD]`.
- [ ] Journey: licensed, medically reviewed illustrations and where the image assets are stored `[TBD]`.
- [ ] Approach to CTG input availability `[ON HOLD]`.
- [x] Vector store: pgvector (closed).
- [x] RAG orchestration: LangChain (closed).
- [x] Maternal dataset: closed.
- [x] Authentication: Supabase Auth (closed for v1).
- [x] File storage: Supabase Storage (closed).
- [x] Module 3: the Pregnancy Risk Score is retired and replaced by Genetic Risk Assessment (closed).

---

## 9. Versioning Note

This is **version 2**. Version 1.1 remains the baseline. Expect further revisions as `[TBD]` and `[ON HOLD]` items are resolved.

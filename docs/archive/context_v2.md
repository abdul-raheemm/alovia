# Context Document — Alovia Project Progress
**Purpose:** Full working record of what's been built, how, and why — so any teammate can get oriented without needing to ask Raheem to re-explain earlier decisions.
**Last updated:** 2026-10-11 (aligned with PRD v2, TRD v2, DRD v2)

---

## Change Log (previous version → this version)

| # | Section | Change |
|---|---|---|
| 1 | §1 | Module list updated: Module 3 is now Genetic Risk Assessment, Symptom Tracking added as Module 7, Journey redefined. |
| 2 | §4 | Backend work list extended for the new modules. |
| 3 | §5 | Patient-entered inputs updated. |
| 4 | §6 | **Replaced.** The Pregnancy Risk Score is retired; the new module definitions are recorded. |
| 5 | §8, §9 | 2026-10-11 decisions added; open items updated. |
| 6 | §10, §11 | New §10 on the Review-1 submission; the document map is now §11. |

---

## 1. Project Overview

Alovia is a capstone AI pregnancy-monitoring and clinical decision-support system, built with a 3-person team. Seven modules are in scope per the PRD: Fetal Risk Prediction, Maternal Risk Prediction, Genetic Risk Assessment (Module 3, replacing the void Pregnancy Risk Score), Personalized Pregnancy Journey, a RAG Knowledge Assistant, a Doctor Dashboard, and Symptom Tracking (Module 7). Admin is a role for now and may become a module in the future. This document covers progress through the two ML models, their backend integration, a test frontend, the retirement of the Pregnancy Risk Score, the RAG knowledge base work, and the module definitions added on 2026-10-11.

---

## 2. Fetal Risk Prediction Model

### Dataset & Cleaning
- **Source:** UCI Cardiotocography dataset (id=193), downloaded directly as the official `.xls` file. Standard, widely-used dataset for this exact task — SisPorto software auto-generates 21 standardized CTG features per record, labeled by expert obstetricians into 3 classes: Normal / Suspect / Pathological (`NSP`).
- **Loading quirk:** the official file's `Data` sheet has a hidden two-row header (real column names sit one row below where pandas would naively read them) — required `header=1` to load correctly.
- **Cleaning:** sliced to the real 2,126 patient rows (trailing rows were footer/summary junk, not real data), dropped blank spacer columns, and — after checking for duplicates — found and removed **10 exact-duplicate rows** (verified via matching raw signal timestamps, not just matching features, confirming they were true duplicate entries, not coincidence). Final clean dataset: **2,116 records**.
- **Feature selection:** used the 21 pre-computed standard CTG features (`LB, AC.1, FM.1, ...` etc.) as `X`, `NSP` as `y`. A separate raw-interval feature group (`b, e, AC, FM, ...`) was deliberately excluded — it's upstream/overlapping signal that the 21 standard features were derived from, not independent information; noted as a possible future feature-engineering experiment, not needed for v1.

### Model Selection & Tuning
- **Class imbalance:** real (Normal ~78%, Suspect ~14%, Pathological ~8%) — used `class_weight='balanced'` (via `sample_weight` for XGBoost) rather than SMOTE, evaluating that baseline first before considering synthetic oversampling.
- **Candidates tested:** Logistic Regression, Random Forest, SVM, XGBoost.
- **Important methodological finding:** on a single 80/20 stratified split, Random Forest looked like the winner (macro F1 0.923 vs. XGBoost's 0.916). **5-fold cross-validation reversed this** — XGBoost's CV mean (0.907) beat RF's (0.885) with lower variance too. This became a standing lesson for the rest of the project: never trust a single train/test split for model selection.
- **XGBoost selected**, tuned via `RandomizedSearchCV` (50 iterations, 5-fold, scored on `f1_macro` — not accuracy, given the imbalance). CV improved 0.907 → 0.922. Final test performance: **97% Pathological recall (34/35), 85% Suspect recall, 96% Normal recall**, macro F1 0.916.
- **SMOTE evaluated as unnecessary** given strong post-tuning recall — shelved rather than stacked on top of class weighting.

### Explainability
- SHAP (`TreeExplainer`) built and verified. Top global drivers matched real clinical CTG interpretation: low `Mean`/`Median` fetal heart rate + high `ASTV`/`ALTV` (abnormal variability measures) push toward Pathological; low `ASTV` pushes toward Normal.

### Extended Pre-Deployment Testing (4 checks, done for both models)
1. **Overfitting check** (train vs. test vs. CV): mild, acceptable gap (0.066), consistent with CV — not concerning.
2. **Class-median sanity check:** fed the model each class's real median feature profile; all 3 correctly classified with 0.978–0.999 confidence.
3. **Error analysis:** manually inspected all 24 test-set misclassifications. Nearly all were adjacent-class boundary confusion (Normal↔Suspect) tied to borderline `ASTV` values — not random errors. **Zero Pathological cases were ever predicted as Normal** (the clinically worst failure mode never occurred). One 2-class-jump outlier flagged as possible original-dataset label ambiguity, not a model defect.
4. **Learning curve:** validation performance still climbing slightly at max training size (not fully data-saturated, but close) — dataset isn't badly undersized for this task.

### Persistence
Saved via `joblib` (model) + 3 JSON files (feature order, label mapping, metadata). Load-and-verify test confirmed the saved model reproduces identical predictions and the exact same macro F1 — a faithful, working copy.

### Known limitation (documented in PRD v2)
The 21 inputs are computer-derived CTG measurements (the training data came from SisPorto-style software). Real-world CTG reading is mostly by eye, and computerized CTG analysis is not universally available — it is more common in well-resourced hospitals. Auto-filling the values from a photo of a CTG report was explored and found not viable as a general feature (CTG output is mostly a waveform; the 21 values come from specialized signal-processing software, so extraction would be a signal-reconstruction problem, not OCR). Current approach: the doctor enters the values manually. **How to address input availability in settings without computerized CTG analysis is on hold and not decided.**

---

## 3. Maternal Risk Prediction Model

### Dataset & Cleaning
- **Source upgrade:** moved from the older 6-feature UCI Maternal Health Risk dataset to the newer **8-feature IoT-validated dataset (Hossain et al., 2026, BMC Medical Informatics and Decision Making)** — adds BMI and HbA1c to the original six vitals, sourced across 9 healthcare facilities.
- **Raw file caught a real issue:** the downloaded CSV (6,103 rows) turned out to be the dataset's **pre-cleaning raw export**, not the paper's published 6,058-row clean version. Rather than inventing our own outlier thresholds, we found and read the actual paper (PMC13005474) to get their exact validated cleaning criteria:
  - `Age` outside 15–48 (1 row — a literal `Age=250` entry)
  - `Body Temperature` outside 95.0–104.0°F (43 rows — including a physically impossible 39.6°F reading)
  - `Diastolic BP` below 50 mmHg (1 row)
  - Applying these exact filters landed on **exactly 6,058 rows** — an exact match to the published figure, confirming correctness.
- **Unit correction (not a data error, a labeling issue):** cross-checked against the paper and found `Blood Glucose(HbA1c)` is actually in **mmol/mol** (not percent) and `Blood Glucose(Fasting hour-mg/dl)` is actually in **mmol/L** (not mg/dl, despite the column name). Renamed both columns for clarity; no values were changed.
- **Duplicate check:** found one pair of rows with identical vitals but different Patient IDs/Names — judged to be a genuine coincidence between two real patients (not a data entry duplicate, unlike the fetal case), and kept.

### Model Selection & Tuning
- Classes here are **near-perfectly balanced** (~33% each) — no class-weighting or SMOTE needed, a real point of difference from fetal.
- Same 4 candidates tested. Results closely reproduced the source paper's own published numbers independently (Logistic Regression ~56% accuracy in both; tree ensembles ~99% in both) — strong external validation that our pipeline was built correctly.
- **RF vs. XGBoost was a genuine statistical tie after CV** (0.9921 vs. 0.9919, well within noise) — unlike fetal, where CV gave a clear answer. XGBoost was chosen on secondary grounds: slightly more stable CV variance, shared tooling/code patterns with the already-built fetal pipeline, and it matches the source paper's own deployment recommendation given their equivalent tie.
- Tuned via the same `RandomizedSearchCV` approach (no `sample_weight` needed this time). Small, real improvement (CV 0.9919→0.9924, test macro F1 0.9893→0.9909).

### Explainability
SHAP verified against both our own model and the paper's independently-reported feature ranking (Diastolic BP, Body Temp, Systolic BP as top predictors) — a genuine external cross-check, not just internal consistency. A worked waterfall example showed a real hypertensive-crisis-level BP reading (162/102) and a diabetic-threshold HbA1c value correctly driving a High-risk prediction.

### Extended Pre-Deployment Testing
Same 4 checks as fetal, with two interesting findings unique to this dataset:
- The **class-median sanity check initially failed** (2 of 3 synthetic "typical" profiles misclassified) — traced to the fact that maternal class medians are much closer together per-feature than fetal's were, so stitching together 8 independent medians produces an unrealistic synthetic combination. Re-tested using **real test-set rows closest to each class median** instead, which resolved 2 of 3 cases; the third (a real High-risk case predicted as Mid) was confirmed via full error analysis to be a genuine boundary case with no single strong risk indicator, not a systemic problem.
- **Zero High-risk cases were ever predicted as Low-risk** (the worst-case failure mode, same standard as fetal's zero-Pathological-as-Normal).
- **Learning curve showed a genuine plateau** (unlike fetal's still-rising curve) — this dataset has more than enough data for the task.

### Persistence
Same joblib + JSON pattern as fetal. Load-and-verify test passed identically (exact prediction match, exact macro F1 reproduction).

---

## 4. Backend (FastAPI)

Built in a separate session, then debugged and fully verified using real test cases pulled from the training notebooks above (not synthetic guesses), which is what made the following bugs catchable.

- **Architecture:** a single FastAPI service. `RiskModel` class dynamically builds each model's Pydantic input schema directly from its saved `feature_order.json` — no hardcoded field lists, so the API always matches what the model actually expects. Loads both joblib models + builds both SHAP `TreeExplainer`s at startup. Endpoints: `GET /health`, `GET /schema/fetal`, `GET /schema/maternal`, `POST /predict/fetal`, `POST /predict/maternal`.
- **Bug #1 (real, found via testing):** the SHAP array-shape detection logic checked `array.shape[0] == number_of_features` to decide how to index into it — but for a single-row prediction, `shape[0]` is always the sample count (`1`), never the feature count, so that check always failed. This silently produced wrong SHAP output for the Normal-class case (looked plausible, wasn't) and crashed outright for Suspect/Pathological. Root cause: the actual SHAP shape (`n_samples, n_features, n_classes`), which had been explicitly verified against the real test data in the training notebook, didn't match what the backend's indexing logic assumed. Fixed to slice correctly against the confirmed shape.
- **Bug #2:** SHAP direction labels were generic ("increases risk" / "decreases risk") regardless of which class was actually predicted — meaning a factor "increasing" toward a Normal prediction was mislabeled. Fixed to be relative to the predicted class ("supports 'X' prediction" / "pushes away from 'X' prediction").
- **Minor fix:** switched `payload.dict()` → `payload.model_dump()` (Pydantic 2.9 — avoids a deprecation warning, not a functional bug).
- **Verification:** after both fixes, re-ran every real test case from both notebooks (fetal Normal/Suspect/Pathological, maternal Low/Mid/High + a known documented misclassification case) against the live API. **Every confidence value and every top SHAP factor matched the notebook results exactly** — strong confirmation the backend faithfully reproduces both models' real, already-validated behavior.
- **Deployment:** pushed to GitHub, deployed on Render (Python 3, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`), verified working against the live URL.
- **Still to build (decided 2026-10-02):** FastAPI is now the **only** gateway to the database and storage. The backend is prediction-only today, so it must take on token verification, patient and result persistence, history/trends, medical report upload and download, the knowledge assistant, journey content, pregnancy dates and appointments, symptom logging with red-flag checks, genetic risk assessment, and admin operations. Route design is not yet done. See TRD v2 §4.7.

---

## 5. Test Frontend (Bolt + Supabase) — Temporary Tool

- **Purpose:** a visual test tool to confirm both models actually work end-to-end with realistic data entry — explicitly not the final production frontend. **It talks to Supabase directly, which is not the target architecture** (the real frontends will go through FastAPI only). Its open database policies must be removed before public deployment.
- **Key real-world framing decision:** doctors enter patient data (never patients themselves) — matches actual clinical workflow. This meant the tool needed real data persistence (patient profiles + result history), not just stateless predict-and-forget calls like the original plan assumed. (In the main build patients enter symptoms and pregnancy dates; any other patient inputs are not yet defined.)
- **Doctor Dashboard:** patient list, create/update patient profiles, per-patient fetal + maternal entry forms (grouped into logical sections — e.g. Baseline & Variability, Histogram Statistics for fetal; Vitals, Blood Pressure, Metabolic for maternal), full technical results (probabilities as bar charts, SHAP factors as an impact table). Clinical visual tone (navy/teal), deliberately not generic SaaS styling.
- **Patient View:** read-only, no forms — shows whatever the doctor most recently entered, using **static template text** per predicted class (3 fetal classes, 3 maternal classes) rather than AI-generated explanations, since the frontend tool can't run an LLM live. Warm, calm visual tone, deliberately different from the doctor view (not just a color toggle on the same layout).
- **Data storage:** Supabase (`patients`, `fetal_results`, `maternal_results` tables) — FastAPI stays prediction-only; Supabase only stores data, doesn't run any ML.
- **Built with Bolt** (not Lovable, despite the original build prompt being written with Lovable's conventions in mind — the prompt content was tool-agnostic enough to apply directly).
- **Testing:** verified with both the exact real test cases from the notebooks, and a second round of **genuinely new synthetic scenarios** (grounded in real clinical patterns from the SHAP analysis, but not pre-verified against the model) — confirmed working as expected across both rounds.

---

## 6. Pregnancy Risk Score (Module 3): Retired and Replaced

- **Decision (2026-10-11):** the Pregnancy Risk Score definition is void and the module is retired. Module 3 is now **Genetic Risk Assessment**, and **Symptom Tracking** is added as Module 7. The combined (weighted) score is not part of this version.
- **Genetic Risk Assessment:** a rule-based estimate of the likelihood that a child inherits selected genetic disorders from both parents (for example, two carriers of an autosomal recessive condition give 25% affected, 50% carrier, 25% neither). No trained ML model, a small set of conditions, manual structured entry, counselling recommended, not a diagnosis. See PRD §4.3.
- **Symptom Tracking:** a patient-entered daily symptom log (severity, duration, body region for pain), history over time, rule-based red-flag prompts for urgent symptoms, and histories visible to the doctor. See PRD §4.7.
- **Journey redefined:** nine illustrated month cards, a pregnancy calendar, a due date from the last menstrual period or a clinician-confirmed date, and predefined medically reviewed content. See PRD §4.4.
- Features that waited on the old Module 3 (overall score on the dashboard, overall patient view, risk-tier Journey personalization) are dropped for now. The dashboard shows fetal, maternal and genetic results separately, and the Journey is selected by gestational age only.
- The `pregnancy_risk_scores` table is removed from the DRD and must not be created.
- Numbering (PRD is authoritative): 1 Fetal, 2 Maternal, 3 Genetic Risk Assessment, 4 Journey, 5 Knowledge Assistant, 6 Doctor Dashboard, 7 Symptom Tracking.
- The first version is the baseline; the modules are expected to grow (for example more genetic conditions and inheritance patterns).

---

## 7. RAG Knowledge Assistant and Knowledge Base

- **Stack decided:** LangChain for orchestration, **pgvector on Supabase** as the vector store (replaces FAISS from TRD v1.0), an embedding API for embeddings. **LLM and embedding provider are not chosen yet.**
- **Rules:** educational only, never diagnosis or treatment (redirect to "consult your doctor"); answers grounded in the knowledge base; **citations required**; the assistant uses the patient's gestational age (derived from the stored due date) to personalize answers.
- **Knowledge base plan:** 600 files minimum, 1,000+ ideal (about 3 million words at most, sized for the free Supabase tier), from trusted organizations only: international bodies, Indian national sources, and official Telangana/Hyderabad sources. Only content with a reusable licence (Tier A/B) is copied; copyrighted sources such as ACOG are reference-only. Each file carries a label block (publisher, URL, review date, licence, region, audience, topics, trimester, week range, safety flags).
- **Process:** collected step by step following `knowledgebase.md` and checked with `validate_kb.py`. The collection was originally assigned to a teammate and is now being done by Raheem, with an AI assistant acting as guide (it never writes medical text or invents metadata).
- **Pending:** `knowledgebase.md` v2.1 and a `validate_kb.py` patch (licence/AI-use check, resolve the contradiction about who runs the script, wider dosage keyword rule, tolerate malformed YAML and BOM, require `trimester` as text, heading/URL/trimester checks). To be applied when collection resumes.

---

## 8. Decisions

### 2026-10-02 (documentation revision)

| Topic | Decision |
|---|---|
| Module 3 (Pregnancy Risk Score) | On hold (superseded 2026-10-11, see §6) |
| Admin | A role only for now; may become a module later |
| Authentication | Supabase Auth for now; later a stronger backend-controlled JWT (not committed) |
| Login path | Frontend uses Supabase only to sign in/out; all data requests go to FastAPI with the token |
| File storage | Supabase Storage (private bucket) |
| Database access | Through FastAPI only, never directly from the frontend (direct access judged weak and risky) |
| Gestational age | Store `due_date`; derive weeks at query time |
| CTG limitation | Documented; how to address it is on hold |
| Patient input | Doctor-entered in v1; some patient-entered inputs expected later; not finalized (symptoms and pregnancy dates added 2026-10-11) |
| Dashboard / patient view while Module 3 is on hold | Show fetal and maternal results separately (the genetic result is also shown separately since 2026-10-11) |

### 2026-10-11 (module changes)

| Topic | Decision |
|---|---|
| Pregnancy Risk Score | Definition void; module retired |
| Module 3 | Genetic Risk Assessment (rule-based, no ML) |
| Symptom Tracking | New Module 7 |
| Journey | Redefined: nine illustrated month cards, pregnancy calendar, LMP or clinician-confirmed due date |
| Patient input | Patients enter symptoms and pregnancy dates; clinical data stays doctor-entered |
| Document naming | `PRD_v2`, `TRD_v2`, `DRD_v2`, `context_v2` |
| Scope | First version is the baseline; room is kept for later improvement |

---

## 9. Open Items

- Genetic Risk Assessment: supported conditions, who enters parental data, consent.
- Symptom Tracking: red-flag rule set and its source, pattern-change rules, consent for doctor visibility.
- Journey: licensed, medically reviewed illustrations and where the image assets are stored.
- Approach to CTG input availability (on hold).
- Which other inputs patients can enter themselves.
- Embedding provider (fixes the vector size), LLM, frontend hosting.
- Route-level API design for the backend work in §4.
- Whether the assistant may explain a patient's own risk result.
- Handling of dosage-containing and treatment-advice documents in patient answers.
- Knowledge base collection, then `knowledgebase.md` v2.1 and the script patch.

---

## 10. Review-1 Submission (notice dated 2026-10-03)

- **Required:** a seminar PPT (title, problem statement, literature survey highlighting the base paper, research gaps, abstract, existing system, proposed system overview, references). Hardcopies on the day: a one-page abstract on the department template, the base paper and the two most relevant papers.
- **Literature survey norms:** 10 to 20 papers, 60 to 70% from the last three years, at most 2 review papers, IEEE citation style, comparison table in the department template, research gaps clearly stated.
- **Status:** the final abstract is adopted (fetal, maternal, genetic, Journey, symptom tracking, RAG, dashboard). The survey target is 10 to 15 papers. The base paper and the two relevant papers are not yet chosen. Corrections to `Alovia_Project_Report.pdf` are listed in `report_changes_needed.md`.

---

## 11. Document Map

| File | Version | Notes |
|---|---|---|
| `PRD_v2.md` | 2 | Supersedes `PRD_v1.1.md` |
| `TRD_v2.md` | 2 | Supersedes `TRD_v1.1.md` |
| `DRD_v2.md` | 2 | Supersedes `DRD_v1.1.md` |
| `context_v2.md` | updated 2026-10-11 | This file; supersedes `context.md` |
| `knowledgebase.md` | 2.0 | v2.1 pending |
| `validate_kb.py` | current | Patch pending |

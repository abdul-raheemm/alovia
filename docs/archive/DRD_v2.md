# Database Requirements Document (DRD)
## Alovia — AI-Powered Pregnancy Monitoring and Clinical Decision-Support System

**Version:** 2 (supersedes 1.1)
**Date:** 2026-10-11
**Audience:** Team reference, with enough detail to set up the database without needing more context
**Database engine:** PostgreSQL on Supabase (managed PostgreSQL), with the `vector` extension (pgvector) enabled. A later move to another managed or self-hosted Postgres would not change the SQL.
**Access path:** **All access to the database and to file storage goes through FastAPI.** The frontend never connects to the database or storage directly. It contacts Supabase only to sign in and out.

---

## Change Log (v1.1 → v2)

| # | Section | Change |
|---|---|---|
| 1 | §2 `patients` | `lmp_date` and `due_date_source` added to the columns to apply. |
| 2 | §3 | New tables: `symptom_logs`, `appointments`, `journey_content`, `genetic_conditions`, `genetic_assessments`. |
| 3 | §3 `pregnancy_risk_scores` | Removed. The module is retired and replaced by Genetic Risk Assessment. Do not create this table. |
| 4 | §4, §5, §6 | Relationships, security and open items updated. |

---

## 1. Design Principles

- **Relational, not document-based.** The data model has real referential relationships (a prediction belongs to a patient, a patient is assigned to a doctor) that need enforced integrity.
- **JSONB for variable-shape ML output.** SHAP contributing factors (a variable-length list) and class probabilities are stored as `JSONB`.
- **Append-only prediction history.** Fetal and maternal predictions are never edited or deleted; each new prediction is a new timestamped row. This preserves an audit trail and supports trends.
- **UUIDs as primary keys** throughout, to avoid exposing sequential or guessable IDs for patient records.
- **Files outside the database.** File bytes never go in Postgres; only a storage reference does.
- **The knowledge base is not patient data.** It is stored in its own tables and is never linked to a specific patient.

---

## 2. Tables Already Built & Verified (Test Frontend, Supabase)

These exist today and were tested end-to-end against the deployed FastAPI backend. **They were created for the temporary test frontend, which accesses them directly. Any open access policies on them must be removed before public deployment (see §5).**

### `patients`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `name` | text | |
| `notes` | text, nullable | free-form doctor notes |
| `created_at` | timestamptz | |

**Changes to apply for the full system:**

| Column to add | Type | Notes |
|---|---|---|
| `due_date` | date, nullable | **Decision made:** store the due date, not the weeks. Gestational age is derived at query time. |
| `user_id` | uuid, nullable, unique, FK → `users.id` | Links a patient record to a patient login. Nullable because in v1 doctors create patient records, and a patient may not have a login yet. |
| `lmp_date` | date, nullable | First day of the last menstrual period, if the patient entered it. |
| `due_date_source` | text, nullable | How `due_date` was set: `lmp_estimate` / `clinician_confirmed` / `ultrasound`. Clinician-confirmed dating takes precedence over an LMP estimate. |

**Deriving gestational age** (weeks counted from the last menstrual period, the same convention as the knowledge base): the due date is 280 days after the last menstrual period, so gestational age in days = `280 − (due_date − today)`, and gestational weeks = whole weeks of that value. Do not store the derived value, because it goes stale. Pregnancy months shown in the Journey are display labels derived from the weeks and are not stored.

### `fetal_results`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `input_values` | jsonb | the 21 submitted CTG feature values |
| `predicted_class` | text | `Normal` / `Suspect` / `Pathological` |
| `confidence` | float | |
| `class_probabilities` | jsonb | `{Normal: x, Suspect: y, Pathological: z}` |
| `top_contributing_factors` | jsonb | list of `{feature, impact, direction}` |
| `created_at` | timestamptz | |

### `maternal_results`
Same shape as `fetal_results`, for the 8 maternal inputs (age, systolic BP, diastolic BP, body temperature, heart rate, BMI, HbA1c, fasting glucose). `predicted_class` values: `Low` / `Mid` / `High`.

### Recommended additions to both result tables (not yet built)
| Column | Type | Notes |
|---|---|---|
| `entered_by` | uuid, nullable, FK → `doctors.id` | Who submitted the reading. Inputs are doctor-entered in v1. |
| `model_version` | text, nullable | Which saved model produced the prediction, so old results stay interpretable if a model is retrained. |

---

## 3. Tables Required for the Full System (Not Yet Built)

### `users`
Application-level identity and role. **Credentials are handled by Supabase Auth, so no password hash is stored here.**
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK, FK → Supabase Auth user id | Same value as the Supabase Auth user id |
| `email` | text, unique | |
| `role` | text | `patient` / `doctor` / `admin` |
| `created_at` | timestamptz | |

### `doctors`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `user_id` | uuid, unique, FK → `users.id` | |
| `name` | text | |
| `specialty` | text, nullable | |

### `doctor_patient_assignments`
The mapping table (one doctor → many patients).
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `doctor_id` | uuid, FK → `doctors.id` | |
| `patient_id` | uuid, FK → `patients.id` | |
| `assigned_at` | timestamptz | |

The backend uses this table to decide which patients a doctor may see.

### `medical_records`
Real (non-mocked) upload and handling, per PRD §4.6.
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `uploaded_by` | uuid, FK → `doctors.id` | |
| `file_type` | text | e.g. `ultrasound`, `blood_report`, `prescription` |
| `storage_path` | text | Object path in the **private** Supabase Storage bucket. The backend creates short-lived download links on request; no permanent public URL is stored. |
| `original_filename` | text | |
| `uploaded_at` | timestamptz | |

### `chat_history`
RAG assistant conversation logs, per PRD §4.5.
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `role` | text | `user` / `assistant` |
| `message` | text | |
| `retrieved_sources` | jsonb, nullable | List of the sources used for an assistant message, each as `{doc_id, chunk_id, title, source_org, url}`, so a citation can be traced back to `kb_documents` and `kb_chunks`. |
| `created_at` | timestamptz | |

### `kb_documents` (knowledge base, one row per clean file)
Populated from the front-matter labels of the files in the knowledge base (the `manifest.csv` produced by the validation script has the same columns).
| Column | Type | Notes |
|---|---|---|
| `doc_id` | text, PK | e.g. `NHS-WEEKLY-024`; equals the file name |
| `title` | text | |
| `source_org` | text | One fixed spelling per source |
| `source_type` | text | `government` / `intergovernmental` / `professional_body` / `nonprofit` / `academic` |
| `licence_tier` | text | `A` or `B` |
| `licence` | text | Exact licence name as read from the source's terms page |
| `attribution` | text, nullable | |
| `url` | text | |
| `date_accessed` | date | |
| `published_or_reviewed` | text | `YYYY`, `YYYY-MM`, `YYYY-MM-DD` or `unknown`, so it is stored as text |
| `region` | text | `international` / `india` / `telangana` / `hyderabad` |
| `country` | text | |
| `language` | text | `en` / `te` / `hi` / `ur` |
| `doc_type` | text | `patient_education` / `guideline` / `factsheet` / `glossary` / `scheme_info` / `faq` / `myth_buster` |
| `audience` | text | `patient` / `clinician` / `both` |
| `topics` | text[] | First item is the primary topic |
| `trimester` | text | `1` / `2` / `3` / `all` / `postpartum` |
| `week_start` | integer, nullable | Gestational weeks 1–42, LMP convention |
| `week_end` | integer, nullable | |
| `contains_treatment_advice` | boolean | |
| `contains_dosage` | boolean | |
| `time_sensitive` | boolean | |
| `priority` | text | `P1` / `P2` / `P3` |
| `raw_file` | text | Path to the saved original |
| `part` | text, nullable | e.g. `3/12` if split from a longer document |
| `notes` | text, nullable | |
| `word_count` | integer | |

### `kb_chunks` (knowledge base, embedded text)
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `doc_id` | text, FK → `kb_documents.doc_id` | |
| `chunk_index` | integer | Position within the document |
| `content` | text | |
| `embedding` | vector(`N`) | **`N` depends on the embedding model and must be decided before the table is created** `[TBD]` |
| `week_start`, `week_end`, `trimester`, `audience`, `region` | copied from the document | Copied onto each chunk so retrieval can filter without a join |

Retrieval filters on the **week range**, not on trimester alone. The knowledge base is capped at roughly 3 million words (about 7,500 chunks) to stay within the free-tier size limit.

The tables below are derived from the Journey, Symptom Tracking and Genetic Risk Assessment module specifications. Exact columns may be refined during the build.

### `symptom_logs`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `entry_date` | date | Date of the entry |
| `symptom` | text | From a predefined list (nausea, fatigue, headache, back pain, food craving, mood change, and so on) |
| `severity` | text or integer | Perceived severity; scale `[TBD]` |
| `duration` | text or integer | How long the symptom lasted; unit `[TBD]` |
| `body_region` | text, nullable | Affected region, for pain or discomfort |
| `occurred_at` | time, nullable | Time of occurrence |
| `notes` | text, nullable | |
| `created_at` | timestamptz | |

Patient-entered. Red-flag status is computed by backend rules; whether it is also stored is `[TBD]`. Whether food cravings need a dedicated field is `[TBD]`. A doctor sees these rows for assigned patients, subject to consent `[TBD]`.

### `appointments`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `appointment_at` | timestamptz | |
| `note` | text, nullable | |
| `created_at` | timestamptz | |

User-entered, shown on the pregnancy calendar. Week and month milestones are derived from `due_date` and are not stored. Reminders are `[TBD]`.

### `journey_content` (reference data, not patient data)
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `month` | integer, nullable | 1 to 9 |
| `week_start`, `week_end` | integer, nullable | Gestational weeks, LMP convention |
| `content_type` | text | For example fetal development, maternal changes, common symptoms, guidance, nutrition, do's and don'ts, warning signs, checklist; final list `[TBD]` |
| `title` | text | |
| `body` | text | Predefined, medically reviewed text |
| `illustration_ref` | text, nullable | Reference to the image asset |
| `source_ref` | text | Source the content was reviewed against |

The content may instead be kept as structured content files (TRD §4.4).

### `genetic_conditions` (reference data, not patient data)
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `name` | text, unique | |
| `inheritance_pattern` | text | `autosomal_recessive` / `autosomal_dominant` / `x_linked`; other patterns later |
| `relevant_findings` | jsonb, nullable | Findings or variants the entry form asks for |
| `rule_notes` | text | |
| `source_ref` | text | Reference the rule was checked against |

The supported set is small and carefully selected `[TBD]`.

### `genetic_assessments`
| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `mother_findings` | jsonb | Submitted findings for the mother |
| `father_findings` | jsonb | Submitted findings for the father |
| `results` | jsonb | Per condition: probability affected, carrier probability where relevant, explanation, warnings |
| `entered_by` | uuid, nullable, FK → `users.id` | Who submitted it; who may enter this is `[TBD]` |
| `created_at` | timestamptz | |

Append-only, like predictions: each run is a new row. The father's findings are sensitive information about a third person; consent is `[TBD]`.

### `pregnancy_risk_scores` (removed)
Retired in v2. **Do not create this table.** Genetic Risk Assessment results are stored in `genetic_assessments`.

---

## 4. Relationships Summary

```
Supabase Auth user (1) ── (1) users
users (1) ──< doctors (1) ──< doctor_patient_assignments >── (1) patients
users (1) ── (0..1) patients        [patient login, nullable]

patients (1) ──< fetal_results
patients (1) ──< maternal_results
patients (1) ──< medical_records
patients (1) ──< chat_history

patients (1) ──< symptom_logs
patients (1) ──< appointments
patients (1) ──< genetic_assessments

kb_documents (1) ──< kb_chunks      [standalone; not linked to patients]
journey_content, genetic_conditions   [standalone reference data; not linked to patients]
chat_history.retrieved_sources  ──references──>  kb_documents / kb_chunks
```

---

## 5. Security & Access (Minimum Lockdown, and Future Scope)

**Applies now, even at prototype stage:**
- **All access goes through FastAPI.** The backend connects to the database and storage with server-side credentials that exist only in its environment variables.
- **Row-Level Security is enabled on every table with no policies for the public or signed-in roles** (deny by default). This matters because the frontend holds the public Supabase key for sign-in, and without it the database's automatic table API would allow direct access. This includes the knowledge base tables.
- **The Storage bucket is private.** Downloads use short-lived links created by the backend.
- **The test frontend's open policies on `patients`, `fetal_results` and `maternal_results` are removed before public deployment.**
- Role and ownership checks (a patient sees only their own rows, a doctor sees only assigned patients, per `doctor_patient_assignments`) are enforced in the backend.
- Symptom, appointment and genetic assessment rows are sensitive health data. The new tables follow the same deny-by-default rule. Consent for doctor visibility of symptoms, and for the parents' genetic data, is `[TBD]`.

**Documented for later, not required now:**
- Row-Level Security policies that mirror the backend's rules (patient own rows, doctor assigned patients) as a second layer of defense, so that a backend mistake cannot expose data.
- A move from Supabase Auth to a stronger backend-controlled JWT scheme, as noted in the TRD. Because identity is stored by Supabase Auth user id, this would need a deliberate migration plan.
- **PHI/compliance:** Supabase's free and standard tiers do not meet HIPAA requirements. This is not a concern while all data is public or synthetic, but real patient data needs a compliant setup (a higher tier with a signed agreement, or a suitably configured managed or self-hosted Postgres).
- Encryption at rest is provided by the managed provider at infrastructure level; additional measures are deferred per the PRD.

---

## 6. Open Items

- [ ] Embedding model and vector dimension `N` (blocks creation of `kb_chunks`).
- [ ] Genetic Risk Assessment: supported conditions, who enters parental data, and consent (including for the father's data) `[TBD]`.
- [ ] Symptom Tracking: severity scale, duration unit, cravings field, whether red-flag status is stored, and consent for doctor visibility `[TBD]`.
- [ ] Which inputs beyond symptoms and pregnancy dates patients may enter themselves (may require new tables or a source marker on existing ones).
- [x] Gestational age: `due_date` (closed).
- [x] File storage: Supabase Storage, private bucket (closed).
- [x] Module 3 / `pregnancy_risk_scores`: retired and replaced by `genetic_assessments` (closed).

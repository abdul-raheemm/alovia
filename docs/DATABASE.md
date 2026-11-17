# Database — Alovia

**Version:** 3.0 (replaces `archive/DRD_v2.md`) · **Date:** 2026-11-16
**Rule for agents:** do not create tables, columns or relationships that are not in this document. If something is missing, stop and ask; then update this document first.

---

## 1. Database Engine
- **PostgreSQL** on **Supabase**, a **fresh project** created by the owner (the old test project is not reused).
- Extensions: `pgcrypto` (for `gen_random_uuid()`, usually enabled), `vector` (pgvector, Phase 7).
- **Access:** only the FastAPI backend connects, with the connection string from its environment. Frontends never query tables.
- **Migrations:** Alembic, in `backend/migrations/`. One migration per phase/module (see §13).

---

## 2. Naming Conventions

| Item | Convention |
|---|---|
| Tables | `snake_case`, plural (`symptom_checkins`) |
| Columns | `snake_case` |
| Primary keys | `id uuid primary key default gen_random_uuid()` (exceptions: `users.id` = Supabase Auth id; `kb_documents.doc_id` text; `size_reference.week` integer) |
| Foreign keys | `<singular>_id` (e.g. `patient_id`), `on delete restrict` unless stated |
| Timestamps | `timestamptz`; `created_at not null default now()`; `updated_at` only on editable tables, set by the backend |
| Enumerations | `text` + `CHECK (col in (...))` (easier to migrate than Postgres enums) |
| Variable structures | `jsonb` |
| Booleans | `not null default false` unless stated |

---

## 3. Tables

Legend: **PK** primary key, **FK** foreign key, **U** unique, **N** nullable. Columns are `not null` unless marked N.

### 3.1 Identity and access (Phase 1)

**`users`** — one row per signed-in person
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | = Supabase Auth user id (`auth.users.id`); no foreign key to `auth.users` (DEC-033) |
| email | text U | |
| role | text | `patient` / `doctor` / `admin` |
| is_active | boolean | default true |
| created_at | timestamptz | |

**`consents`** — app-wide consent records (legal: form consent)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users | |
| consent_version | text | e.g. `2026-11-v1`; matches `docs/legal/CONSENT_TEXT.md` |
| age_confirmed_18_plus | boolean | |
| accepted_at | timestamptz | |

**`doctors`**
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users U | |
| name | text | |
| specialty | text N | |
| is_active | boolean | default true |
| created_at | timestamptz | |

**`patients`**
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK users U N | null until the patient links a login |
| name | text | |
| age | integer N | |
| notes | text N | doctor-private notes (never shown to the patient) |
| due_date | date N | source of all gestational-age calculations |
| lmp_date | date N | |
| due_date_source | text N | `lmp_estimate` / `clinician_confirmed` / `ultrasound` |
| pregnancy_status | text | `active` (default) / `ended_birth` / `ended_loss` / `ended_not_specified` |
| pregnancy_ended_at | timestamptz N | |
| doctor_informed_of_end | boolean N | |
| created_by | uuid FK users N | |
| created_at, updated_at | timestamptz | |

**`doctor_patient_assignments`**
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| doctor_id | uuid FK doctors | |
| patient_id | uuid FK patients | |
| is_primary | boolean | at most one true per patient among active rows (partial unique index) |
| assigned_by | uuid FK users | |
| assigned_at | timestamptz | |
| removed_at | timestamptz N | removed rows kept for history; one active row per (doctor, patient) (partial unique index) |

**`patient_invites`**
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| patient_id | uuid FK patients | |
| code_hash | text U | code stored only as a hash |
| created_by | uuid FK users | |
| created_at, expires_at | timestamptz | |
| used_at | timestamptz N | |
| used_by_user_id | uuid FK users N | |

**`audit_log`** (append-only)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| actor_user_id | uuid FK users N | null for system actions |
| action | text | list in Dashboard spec §20 |
| entity_type | text | |
| entity_id | text N | |
| patient_id | uuid N | no FK (kept after deletion requests) |
| details | jsonb N | **never** clinical values |
| created_at | timestamptz | |

**`deletion_requests`** (Phase 8)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid | no FK (kept after the user is deleted) |
| status | text | `pending` / `completed` / `rejected` |
| requested_at | timestamptz | |
| handled_by | uuid N | |
| handled_at | timestamptz N | |
| note | text N | |

### 3.2 Predictions — Modules 1 & 2 (Phase 1 move, Phase 5 additions)

**`fetal_results`** (append-only)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| patient_id | uuid FK patients | |
| input_values | jsonb | 21 features, model units |
| entered_values | jsonb N | values and units as typed (Phase 5) |
| range_warnings | jsonb N | list of feature names outside training range (Phase 5) |
| predicted_class | text | `Normal` / `Suspect` / `Pathological` |
| confidence | double precision | |
| class_probabilities | jsonb | |
| top_contributing_factors | jsonb | list of `{feature, impact, direction}` |
| entered_by | uuid FK doctors N | |
| model_version | text N | from model metadata |
| created_at | timestamptz | |

**`maternal_results`** — same columns; `predicted_class` in `Low` / `Mid` / `High`; `input_values` = 8 features.

**`result_shares`** (Phase 5)
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| result_type | text | `fetal` / `maternal` |
| result_id | uuid | id in the matching table (checked by the backend) |
| shared_by | uuid FK doctors | |
| template_key | text | |
| doctor_message | text N | |
| ai_draft_id | uuid N | FK to `ai_drafts` added in Phase 6 |
| created_at | timestamptz | |
Unique: (`result_type`, `result_id`).

### 3.3 Pregnancy Journey — Module 4 (Phase 2)

**`pregnancy_date_history`** (append-only)
`id` uuid PK · `patient_id` FK · `changed_by` FK users · `old_due_date` date N · `new_due_date` date N · `old_source` text N · `new_source` text N · `old_status` text N · `new_status` text N · `created_at`.

**`appointments`**
`id` uuid PK · `patient_id` FK · `appointment_at` timestamptz · `has_time` boolean · `title` text (≤100) · `note` text N (≤500) · `created_by` FK users · `source` text (`patient` / `doctor`) · `created_at`, `updated_at`. Hard delete allowed (planning data, not a clinical record).

**`notifications`**
`id` uuid PK · `patient_id` FK · `type` text (`new_week`, `new_month`, `appointment_soon`, `doctor_note`, `result_available`, `genetic_reviewed`, `dates_updated`) · `target_ref` text N · `created_at` · `read_at` N · `dismissed_at` N. Unique: (`patient_id`, `type`, `target_ref`) to avoid duplicates.

**`doctor_notes`** (append-only, shared with Module 6)
`id` uuid PK · `patient_id` FK · `doctor_id` FK doctors · `body` text · `visible_to_patient` boolean · `related_ref` text N · `created_at`. Only change allowed: `visible_to_patient` false → true.

**`journey_content`** and **`size_reference`** — created only when `content_source = knowledge_base` (Phase 7+). Until then content is read from `backend/content/*.yaml`.
- `journey_content`: `id` text PK · `granularity` text (`month`/`week`/`week_range`) · `month` int N · `week_start` int N · `week_end` int N · `content_type` text · `title` text · `body` text · `source` jsonb · `kb_doc_id` text FK kb_documents N · `review_status` text (`unreviewed`/`doctor_reviewed`) · `is_prototype` boolean.
- `size_reference`: `week` int PK · `length_cm` numeric N · `weight_g` numeric N · `object_icon_id` text · `object_name` text · `source` jsonb · `review_status` text.

### 3.4 Symptom Tracking — Module 7 (Phase 3)

**`symptom_checkins`** (append-only)
`id` uuid PK · `patient_id` FK · `source` text (`form`/`urgent_button`) · `pregnancy_week` int N · `red_flag_level` text (`L0`/`L1`/`L2`) · `matched_rules` jsonb · `message_keys` jsonb · `pattern_changes` jsonb · `rules_version` text · `created_at`.

**`symptom_logs`** (append-only)
`id` uuid PK · `checkin_id` FK symptom_checkins · `patient_id` FK · `symptom` text · `severity` text N · `duration` text N · `body_area` text N · `details` jsonb N · `occurred_at` time N · `notes` text N (≤500) · `created_at`.

### 3.5 Genetic Risk — Module 3 (Phase 4)

**`genetic_assessments`** (append-only; only review columns updated once)
`id` uuid PK · `patient_id` FK · `submitted_by` FK users · `inputs` jsonb · `results` jsonb · `rules_version` text · `show_numbers_to_patient` boolean · `risk_indicated` boolean · `priority` text (`normal`/`high`) · `review_status` text (`pending_review`/`reviewed`) · `reviewed_by` FK doctors N · `reviewed_at` N · `doctor_note` text N · `supersedes_id` FK genetic_assessments N · `created_at`.
**No `genetic_conditions` table** (rules are YAML files).

### 3.6 Doctor Dashboard — Module 6 (Phase 5)

**`inbox_items`** (created in Phase 2, DEC-044)
`id` uuid PK · `patient_id` FK · `type` text (`symptom_l1`, `symptom_l2`, `pattern_p1`…`pattern_p5`, `genetic_pending`, `genetic_high_priority`, `pregnancy_ended`, `record_uploaded`, `ai_note_flag`, `chat_urgent`) · `ref_table` text · `ref_id` uuid · `created_at` · `seen_by` FK doctors N · `seen_at` N. Never deleted.

**`medical_records`**
`id` uuid PK · `patient_id` FK · `uploaded_by` FK doctors · `file_type` text (`ultrasound`/`blood_report`/`prescription`/`other`) · `storage_path` text U · `original_filename` text · `note` text N · `uploaded_at` timestamptz.

**`rule_signoffs`**
`id` uuid PK · `module` text (`genetic`/`symptom`/`journey`) · `rules_version` text · `item_id` text · `checked` boolean · `comment` text N · `doctor_id` FK doctors · `created_at`.

**`ai_drafts`** (Phase 6)
`id` uuid PK · `feature` text (`AI-1`…`AI-4`) · `patient_id` FK N · `input` jsonb (no names/IDs) · `output` text N · `model_name` text · `prompt_version` text · `status` text (`accepted`/`edited`/`rejected`/`discarded`/`failed`) · `final_text` text N · `created_by` FK users N · `created_at`.

### 3.7 Knowledge Assistant — Module 5 (Phase 7)

**`kb_documents`** — one row per clean knowledge base file; columns = the file's front-matter labels (see `archive/DRD_v2.md` §3 `kb_documents`): `doc_id` text PK, `title`, `source_org`, `source_type`, `licence_tier`, `licence`, `attribution` N, `url`, `date_accessed` date, `published_or_reviewed` text, `region`, `country`, `language`, `doc_type`, `audience`, `topics` text[], `trimester` text, `week_start` int N, `week_end` int N, `contains_treatment_advice` bool, `contains_dosage` bool, `time_sensitive` bool, `priority` text, `raw_file` text, `part` text N, `notes` text N, `word_count` int.

**`kb_chunks`**
`id` uuid PK · `doc_id` FK kb_documents · `chunk_index` int · `content` text · `embedding` vector(**N** `[OPEN]`) · copied labels: `week_start`, `week_end`, `trimester`, `audience`, `region`, `licence`, `attribution`, `contains_dosage`, `contains_treatment_advice`, `time_sensitive`, `published_or_reviewed`, `date_accessed`.

**`chat_history`**
`id` uuid PK · `patient_id` FK · `role` text (`user`/`assistant`) · `message` text · `retrieved_sources` jsonb N · `category` text N · `urgent_match` boolean · `check_result` text N · `model_name` text N · `prompt_version` text N · `feedback` text N (`up`/`down`) · `created_at`.

---

## 4. Relationships

```
auth.users (1)──(1) users (1)──(0..1) doctors
                     │   └──(0..1) patients
                     └──< consents
doctors >──< patients        via doctor_patient_assignments (many-to-many)
patients (1)──< patient_invites, fetal_results, maternal_results, appointments,
                notifications, doctor_notes, pregnancy_date_history,
                symptom_checkins (1)──< symptom_logs,
                genetic_assessments, inbox_items, medical_records, chat_history
fetal_results / maternal_results (1)──(0..1) result_shares
kb_documents (1)──< kb_chunks          (reference data, not patient data)
journey_content.kb_doc_id ──> kb_documents
```

---

## 5. Constraints
- **Required:** all columns not marked N.
- **Unique:** `users.email`, `doctors.user_id`, `patients.user_id`, `patient_invites.code_hash`, `medical_records.storage_path`, `result_shares(result_type, result_id)`, `notifications(patient_id, type, target_ref)`.
- **Partial unique:** one active assignment per (doctor, patient); one primary doctor per patient.
- **Checks:** every enumeration listed above.
- **Business rules enforced by the backend** (not by constraints): a patient keeps at least one assigned doctor; review columns of `genetic_assessments` are written once; `doctor_notes.visible_to_patient` only goes false → true.

## 6. Indexes
| Index | Reason |
|---|---|
| `patient_id` on every patient table (result tables: covered by the composite index below, DEC-035) | All queries are per patient |
| `(patient_id, created_at desc)` on results, check-ins, assessments, chat_history | History screens |
| `inbox_items (patient_id) where seen_at is null` | Unseen items |
| `genetic_assessments (review_status, priority)` | Review queue |
| `appointments (patient_id, appointment_at)` | Calendar |
| `doctor_patient_assignments (doctor_id) where removed_at is null` | Doctor's patient list |
| `kb_chunks` HNSW index on `embedding` + b-tree on `audience`, `week_start`, `week_end` | Retrieval (Phase 7) |

## 7. Data Validation
Validated in the backend (Pydantic + module rules) before writing: vocabularies from the rule files, date rules (Journey §5.2), text length limits, upload type/size, unit conversions. The database constraints are a second line of defence.

## 8. Soft Delete
**No soft delete.** Clinical records are append-only. Hard deletes happen only for: appointments (by their creator), and data deletion requests (Phase 8, executed by an admin, logged in `audit_log` without clinical values).

## 9. Auditing
- `created_at` everywhere; `created_by` / `entered_by` / `submitted_by` / `uploaded_by` where a person acts.
- `audit_log` records actions (Dashboard spec §20).
- History tables: `pregnancy_date_history`; `supersedes_id` for genetic corrections.

## 10. Sensitive Data
All patient tables are sensitive health data (pregnancy, symptoms, genetic findings including the father's, predictions, records, chats).
- No government IDs, phone numbers, addresses or payment data are collected (data minimisation).
- Only the backend can read them; the service key never leaves the backend.
- **Row-Level Security is added in Phase 8** (owner decision DEC-022: security last). Until then only synthetic data is used (see `SECURITY.md` §0 known risk). In Phase 8: RLS enabled on every table with no policies for public/signed-in roles (deny by default).
- Full hardening in Phase 8 (`SECURITY.md`).

## 11. Migration Rules
1. Every schema change is documented here first.
2. Every change has an Alembic migration with a working `downgrade`.
3. Migrations are tested on a fresh database (`alembic upgrade head` from empty) before being applied to Supabase.
4. Never edit an applied migration; add a new one.
5. **The agent must ask before running any migration against the Supabase database** (CLAUDE.md).
6. No destructive change (drop/rename) without the owner's explicit approval.

## 12. Seed Data (development only)
`backend/scripts/seed_dev.py` creates clearly fake data: 1 admin, 2 doctors, 5 patients with names like "Test Patient 1", different gestational ages (8, 16, 24, 34, 41 weeks), sample appointments, check-ins at each level, one genetic assessment per status. Never real people's data. Never run against production without approval.

## 13. Migrations by Phase

| Phase | Migration creates |
|---|---|
| 1 Foundation | users, consents, doctors, patients, doctor_patient_assignments, patient_invites, audit_log, fetal_results, maternal_results |
| 2 Journey | pregnancy_date_history, appointments, notifications, doctor_notes, inbox_items (moved from Phase 3, DEC-044) |
| 3 Symptoms | symptom_checkins, symptom_logs |
| 4 Genetic | genetic_assessments |
| 5 Dashboard | result_shares, medical_records, rule_signoffs; new columns on result tables |
| 6 AI drafts | ai_drafts |
| 7 RAG | `vector` extension, kb_documents, kb_chunks, chat_history; journey_content, size_reference (when switching provider) |
| 8 Security | deletion_requests; enable Row-Level Security on every table; review of all policies |

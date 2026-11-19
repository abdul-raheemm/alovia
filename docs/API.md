# API — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
This document finalises the routes that each module spec listed as "proposed". The agent may suggest changes **before** implementing them; once implemented, this file is the contract.

---

## 1. Conventions
- Base path: `/api/v1`. JSON only (except file upload: `multipart/form-data`).
- Auth: `Authorization: Bearer <Supabase JWT>` on every route except `GET /api/v1/health`.
- Role prefixes: `/patient/...` (patient role), `/doctor/...` (doctor role), `/admin/...` (admin role). A doctor route touching a patient also checks the assignment.
- IDs are UUIDs. Times are ISO-8601 with timezone. Dates are `YYYY-MM-DD`.
- Lists: `?limit=` (default 25, max 100) and `?cursor=`; response includes `next_cursor`.
- POSTs that create records accept an optional `Idempotency-Key` header (prevents duplicate submissions on retry).
- Interactive docs: FastAPI `/docs` in development only (disabled in production, Phase 8).

## 2. Response envelope

Success:
```json
{ "data": { }, "error": null }
```
Error:
```json
{ "data": null, "error": { "code": "VALIDATION_ERROR", "message": "Due date gives a pregnancy longer than 42 weeks.", "fields": { "due_date": "D2" } } }
```

## 3. Error codes

| HTTP | code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid input (spec codes such as V1, V2, D1–D3, E1, E2 go in `fields`) |
| 401 | `AUTH_REQUIRED` | Missing/expired/invalid token |
| 403 | `FORBIDDEN` | Wrong role, or patient not assigned to this doctor |
| 404 | `NOT_FOUND` | Resource missing or not visible to this user (same message either way) |
| 405 | `METHOD_NOT_ALLOWED` | The route exists but not for this HTTP method (owner decision 2026-11-17) |
| 409 | `CONFLICT` | e.g. genetic assessment already reviewed; invite already used |
| 413 | `FILE_TOO_LARGE` | Upload over the limit |
| 415 | `UNSUPPORTED_FILE_TYPE` | Upload format not allowed |
| 429 | `RATE_LIMITED` | Phase 8 |
| 503 | `SERVICE_UNAVAILABLE` | Database, storage or an external API is down |
| 500 | `INTERNAL_ERROR` | Anything unexpected (no internal details returned) |

---

## 4. Routes

### 4.1 System and account (Phase 1)
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/health` | none | Liveness + models/rules loaded |
| GET | `/me` | any | User, role, linked patient/doctor record, consent status |
| POST | `/me/consent` | any | Record app-wide consent (`consent_version`, `age_confirmed_18_plus`) |
| GET | `/invites/{code}/check` | none | Check an invite link is valid before sign-up (returns only valid/invalid; rate-limited in Phase 8) |
| POST | `/patient/link` | patient | Link the new login to the invited patient record (code from the link), right after sign-up |

**`GET /invites/{code}/check`** → `data`: `{valid}`. Valid only if the code exists, is unused, not expired, and its patient record is not linked yet. Codes are case-insensitive.

**`POST /patient/link`** (valid token; no `users` row needed yet) body `{code}` → creates the `users` row (role `patient`, email from the token), links `patients.user_id`, marks the invite used, writes `audit_log` "invite used" — all in one transaction (DEC-036). Errors: every invalid invite → 404 `NOT_FOUND` "This invite link isn't valid. Please ask your doctor for a new one." (DEC-038); account already set up, or email already used → 409 `CONFLICT`; token without email → 400. Success → `data`: same shape as `GET /me`.

**`GET /me`** → `data`: `{user: {id, email, role}, patient: {id, name} | null, doctor: {id, name, specialty} | null, consent: {current_version, accepted}}`. `accepted` is true only for the current consent version. Never includes `patients.notes`. A valid token without a `users` row, or with `is_active = false`, gets 403 `FORBIDDEN` ("Your account is not set up yet."). Sign-in audit (Dashboard spec §20, owner decision 2026-11-17): the first `/me` call of a new Supabase sign-in session (the token's `session_id`) writes one `audit_log` row (`action` "signed in", `entity_type` "session", `entity_id` the session id, `patient_id` for patients, `details` `{role}`); later calls in the same session add nothing. Doctors and admins must accept the current consent once too: the doctor app shows the consent before anything else when `consent.accepted` is false (owner decision 2026-11-17).

**`POST /me/consent`** body `{consent_version, age_confirmed_18_plus}` (no other fields; boolean must be a real boolean). 400 `VALIDATION_ERROR` with `fields.consent_version` if not the current version, or `fields.age_confirmed_18_plus` if not true (DEC-023). Success → `data`: `{current_version, accepted: true}`; repeating it adds no second row.

### 4.2 Pregnancy Journey — Module 4 (Phase 2)
| Method | Path | Purpose |
|---|---|---|
| GET | `/patient/journey/home` | Everything for the home screen |
| PUT | `/patient/journey/dates` | Set/change dates (Journey §5) |
| GET | `/patient/journey/months/{month}` | Month detail |
| GET | `/patient/journey/calendar?from=&to=` | Calendar markers |
| GET, POST | `/patient/appointments` | List / create own |
| PUT, DELETE | `/patient/appointments/{id}` | Edit / delete own (patient-created only) |
| GET | `/patient/notifications` | Notification bar |
| POST | `/patient/notifications/{id}/read` · `/dismiss` | |
| GET | `/patient/doctor-notes` | Shared notes |
| POST | `/patient/pregnancy-end` · `/patient/pregnancy-end/undo` | Journey §11 |

**`GET /patient/journey/home`** (linked patient with current consent; others 403) → `data`: `{state: no_date|active|past_due|beyond_42|ended, dates: {due_date, lmp_date, due_date_source}, pregnancy: {completed_weeks, days, days_to_go, content_week, trimester, month, is_estimate} | null, nav_items: [{key, label}], show_prototype_banner, messages: {key: approved text | null}, notices: [keys]}`. `pregnancy` is null when there is no due date or the pregnancy has ended; message texts are null until a doctor approves them (DEC-041), and the apps then show "[Text pending doctor approval]".

**`PUT /patient/journey/dates`** body is one of (Journey §5.1) `{option: "lmp", lmp_date}`, `{option: "due_date", due_date}`, `{option: "ultrasound", scan_date, ga_weeks, ga_days}`, each with optional `confirm_override` (boolean). 400 `VALIDATION_ERROR` with `fields.<input> = D1|D2|D3` (Journey §5.2); replacing a clinician/ultrasound date with an LMP estimate without `confirm_override: true` → 409 `CONFLICT` with `fields.confirm_override = msg_confirm_override_clinician_date` (§5.3). Success → the refreshed home data; `notices` carries `msg_dates_updated_by_clinician` when a clinician/scan date replaces an estimate. Every change is written to `pregnancy_date_history`.

Task 5 additions to the home payload: `months: [{month, week_start, week_end}]` (empty unless the pregnancy is active with a usable due date), `stage_items` (§8.1 content items for the content week, types `fetal_development`/`body_changes`; week item beats a month item of the same type), `size` (§7.2 row or null — no sourced value means no comparison), `next_appointment` (`{appointment_at, has_time, title}` or null; a date-only appointment counts for its whole day). A stored due date outside rule D2's range never crashes `/home`: it falls back to the onboarding state and is logged (defensive guard, owner 2026-11-17).

**Appointment shape** (home `next_appointment`, the list and the calendar; changed in task 6): `{id, appointment_at, has_time, date, time, title, note, source: patient|doctor, can_edit}`. `date` and `time` (`HH:MM:SS`, null for date-only) are the patient's local values in the config timezone (`appointment_at` is sent in that offset too); apps show them as they are. `can_edit` is true only for her own (§9.3).

**`GET /patient/journey/calendar?from=YYYY-MM-DD&to=YYYY-MM-DD`** (inclusive local days) → `data`: `{start, end, milestones: [{date, kind: new_week|new_month|new_trimester|term|due_date, value}], appointments: [...], suggested_checkups: [{date, label}], suggested_source: {publisher, title, url, date_accessed} | null}`. Suggested check-ups (§9.2, DEC-056) come only from the official schedule in `config.yaml` and only for an active dated pregnancy. `start`/`end` are §9.1's navigation range (pregnancy start to due date + 2 weeks); they and the milestones are null/empty unless the pregnancy is active with a usable due date (§11.3: no baby markers after the end). `from` after `to` → 400 `VALIDATION_ERROR` (`fields.to`). Symptom dots arrive in Phase 3; suggested check-ups stay off (`suggested_checkups_enabled: false`, R3).

Appointment dates and calendar `from`/`to` must be between 1900-01-01 and 2999-12-31 (outside that a local date cannot be stored and read back; 400 `VALIDATION_ERROR`). Patient changes to dates, appointments and pregnancy status each add an `audit_log` row in the same transaction (DEC-049; `details` empty: no clinical values).

**`GET /patient/appointments`** → `data`: `{upcoming, past}`; upcoming soonest first, past most recent first; a date-only appointment is upcoming for its whole day. **`POST`** body `{date, time?, title, note?}` (no other fields; title 1-100 characters after trimming, note up to 500, an empty note is stored as none) → 201 with the appointment; `source` is always `patient`. **`PUT /{id}`** same body → the appointment. **`DELETE /{id}`** → `data: null` (hard delete, DATABASE.md §8). Editing or deleting a doctor-added appointment → 403 `FORBIDDEN`; another patient's or a missing one → 404 `NOT_FOUND`.

**`GET /patient/notifications`** → first creates the notifications that are due (Journey §10.2: on app open; at most one per `(patient, type, target_ref)`), then `data`: unread, undismissed `[{id, type, target_ref, created_at}]`, newest first. Created now: `new_week` / `new_month` (`target_ref` = the current content week / month; active pregnancy with a usable due date only; not back-filled), `appointment_soon` (appointment id; within `appointment_notice_hours`, a date-only one while its day has not passed), `doctor_note` (note id; each shared note). After the pregnancy ends, `new_week`/`new_month` are neither created nor returned (§11.3). `result_available`, `genetic_reviewed`, `dates_updated` come with the doctor actions (Phases 4-5). **`POST /patient/notifications/{id}/read`** and **`/dismiss`** → `data: null`; either removes it from the bar; another patient's or a missing id → 404.

**`GET /patient/doctor-notes`** → `data`: `[{id, body, doctor_name, created_on, related_ref}]`, only `visible_to_patient` notes, newest first; `created_on` is the local day (config timezone). Read-only.

**`POST /patient/pregnancy-end`** body `{status: ended_birth|ended_loss|ended_not_specified, inform_doctor}` (`inform_doctor` is required and must be a real boolean: the question has no default, §11.2; no other fields) → the refreshed home data. Stores `pregnancy_status`, `pregnancy_ended_at`, `doctor_informed_of_end`, logs the status change in `pregnancy_date_history`, and only when `inform_doctor` is true adds a `pregnancy_ended` inbox item (`ref_table` `pregnancy_date_history`, `ref_id` that row) in the same transaction. Already ended → 409 `CONFLICT`. **`POST /patient/pregnancy-end/undo`** → back to `active` within `resume_window_days` of the end (§11.6), logged in `pregnancy_date_history`; an inbox item already sent stays. Not ended, or the window has passed → 409. The home data also carries `helplines: [{label, numbers, source_title, source_url, date_accessed}]` (§13.3, from `messages.yaml`, DEC-057). The home data carries `ended: {status, ended_at, undo_until}` (`undo_until` null once the window has passed) when `state` is `ended`.

Phase 3 additions to the Journey: the home data carries `logged_today` (a check-in exists on her local day) and `weekly_summary: {week_start, week_end, days_logged, top_symptoms: [{symptom, label, count}] (up to 3), red_flag_days, common_at_stage: [content items]} | null` (null after the end; the week is Sunday to Saturday); the calendar carries `symptom_days: [{date, levels}]` (Journey §9.2: a dot for any check-in, a red-flag icon when a level is L1 or L2).

**`GET /patient/journey/months/{month}`** (1-9; linked patient with consent) → `data`: `{month, week_start, week_end, is_current, items}` with all content types for that month. 404 once the pregnancy has ended (§11.3: month cards stop).

### 4.3 Symptom Tracking — Module 7 (Phase 3)
| Method | Path | Purpose |
|---|---|---|
| GET | `/patient/symptoms/vocabulary` | Symptom list filtered by pregnancy week |
| POST | `/patient/symptoms/checkins` | Validate, run rules, save; returns level + message keys (never pattern changes) |
| GET | `/patient/symptoms/checkins` | Own history |
| GET | `/patient/symptoms/charts` | Own chart data |

### 4.4 Genetic Risk — Module 3 (Phase 4)
| Method | Path | Purpose |
|---|---|---|
| POST | `/patient/genetic/assessments` | Submit, run engine, save |
| GET | `/patient/genetic/assessments` · `/{id}` | Own history / one |

### 4.5 Shared results (Phase 5)
| Method | Path | Purpose |
|---|---|---|
| GET | `/patient/results` | Shared fetal/maternal results only (template + doctor message) |

### 4.6 Doctor — Module 6 and doctor sides of other modules (Phase 5)
| Method | Path | Purpose |
|---|---|---|
| GET | `/doctor/patients` | Patient list (Dashboard §6) |
| POST | `/doctor/patients` · PUT `/doctor/patients/{id}` | Create / edit |
| POST | `/doctor/patients/{id}/invite` | Create invite link with a one-time code (returned once) |
| GET | `/doctor/inbox` · POST `/doctor/inbox/{id}/seen` | Inbox |
| GET | `/doctor/predictions/schema/{model}` | Field list (`fetal` / `maternal`) |
| POST | `/doctor/patients/{id}/predictions/{model}` | Convert units, check ranges, predict, save |
| GET | `/doctor/patients/{id}/predictions?model=` | History |
| GET | `/doctor/patients/{id}/trends` | Trend data |
| POST | `/doctor/predictions/{model}/{result_id}/share` | Share with patient |
| GET | `/doctor/patients/{id}/symptoms` | Timeline, levels, pattern changes, charts |
| GET | `/doctor/genetic/review-queue` | Pending assessments |
| POST | `/doctor/genetic/assessments/{id}/review` | Confirm with note |
| POST | `/doctor/genetic/assessments/{id}/correct` | Corrected inputs → new assessment |
| GET, POST | `/doctor/patients/{id}/records` | List / upload |
| GET | `/doctor/records/{id}/download` | Short-lived signed URL |
| GET, POST | `/doctor/patients/{id}/notes` · POST `/doctor/notes/{id}/share` | Notes |
| GET, POST | `/doctor/patients/{id}/appointments` · PUT, DELETE `/doctor/appointments/{id}` | Doctor-created appointments |
| PUT | `/doctor/patients/{id}/dates` · POST `/doctor/patients/{id}/pregnancy-end` | Dates / status |
| GET | `/doctor/rules` · POST `/doctor/rules/{module}/{item_id}/signoff` · GET `/doctor/rules/{module}/export` | Rule review |

### 4.7 AI drafts (Phase 6, flags off by default)
| Method | Path | Purpose |
|---|---|---|
| POST | `/doctor/ai/summary/{patient_id}` | AI-1 |
| POST | `/doctor/ai/share-draft/{model}/{result_id}` | AI-2 |
| POST | `/doctor/ai/genetic-draft/{assessment_id}` | AI-3 |
| POST | `/doctor/ai/drafts/{id}/outcome` | Record accepted/edited/rejected |
(AI-4 runs inside `POST /patient/symptoms/checkins`; no route.)

### 4.8 Admin (Phase 5)
| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/admin/doctors` · PUT `/admin/doctors/{id}` | Invite, edit, deactivate |
| GET, POST, DELETE | `/admin/assignments` | Assign / remove, set primary |
| GET | `/admin/audit` | Activity log (no clinical values) |
| GET | `/admin/deletion-requests` · POST `/admin/deletion-requests/{id}/execute` | Phase 8 |

### 4.9 Privacy (Phase 8)
| Method | Path | Purpose |
|---|---|---|
| POST | `/me/deletion-request` | Patient requests deletion of her data |

### 4.10 Knowledge Assistant — Module 5 (Phase 7)
| Method | Path | Purpose |
|---|---|---|
| POST | `/patient/assistant/messages` | Ask; returns answer, sources, flags |
| GET | `/patient/assistant/history` | Own chat history |
| POST | `/patient/assistant/messages/{id}/feedback` | Up / down |

---

**Symptom routes (Phase 3, details):** `GET /patient/symptoms/vocabulary` → `{logging_open, pregnancy_week, severities, durations, labour_durations, body_areas, common: [...], warning: [... offered at this week], puqe_questions, puqe_source}`. `POST /patient/symptoms/checkins` body `{source: form|urgent_button, entries: [{symptom, severity?, duration?, body_area?, with_vision_problems?, with_swelling?, unable_to_keep_fluids?, puqe_answers?: [3 × 1-5], food?, name?, appetite?, occurred_at?: "HH:MM", notes? (≤500)}]}` (unknown fields refused) → 201 `{checkin_id, created_at, pregnancy_week, red_flag_level, matched_rules, message_keys}`. Errors: 400 `VALIDATION_ERROR` with `fields.<entries.N.field> = V1|V2` (nothing saved); 409 after the pregnancy has ended (DEC-064). An engine failure saves L2 with `["ERR"]` and `msg_safe_fallback` (V3). The check-in, its entries and the doctor inbox items (`symptom_l1`/`symptom_l2`, one `pattern_pN` per pattern code) are saved in one transaction. `GET /patient/symptoms/checkins` → own check-ins newest first with `entries` and `local_date`; `GET /patient/symptoms/charts` → `{symptoms: [{symptom, label, points: [{local_date, pregnancy_week, severity, duration}]}], puqe: [{local_date, pregnancy_week, score, band}]}`. Pattern changes never appear in patient responses (§14 test 8).

## 5. Example — create a symptom check-in

Request:
```json
POST /api/v1/patient/symptoms/checkins
{
  "source": "form",
  "entries": [
    { "symptom": "headache", "severity": "severe", "duration": "1_to_6_hours",
      "with_vision_problems": true, "with_swelling": false }
  ]
}
```
Response:
```json
{ "data": { "checkin_id": "…", "red_flag_level": "L1",
            "matched_rules": ["L1-03"],
            "message_keys": ["msg_level1_go_now"] },
  "error": null }
```

## 6. API Rules
- Validate every input in the backend; never trust the frontend.
- Check role and assignment on every request.
- Return the envelope and codes above; never stack traces or SQL errors.
- Never return another patient's data; "not found" and "not allowed" for patient resources both return 404 to avoid revealing existence.
- Keep the OpenAPI schema generated by FastAPI in sync; the frontend `shared` package types are generated from it (`npm run gen:api`).

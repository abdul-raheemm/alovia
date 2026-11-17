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

**`GET /me`** → `data`: `{user: {id, email, role}, patient: {id, name} | null, doctor: {id, name, specialty} | null, consent: {current_version, accepted}}`. `accepted` is true only for the current consent version. Never includes `patients.notes`. A valid token without a `users` row, or with `is_active = false`, gets 403 `FORBIDDEN` ("Your account is not set up yet.").

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
            "matched_rules": ["L1-03", "L2-07"],
            "message_keys": ["msg_level1_go_now"] },
  "error": null }
```

## 6. API Rules
- Validate every input in the backend; never trust the frontend.
- Check role and assignment on every request.
- Return the envelope and codes above; never stack traces or SQL errors.
- Never return another patient's data; "not found" and "not allowed" for patient resources both return 404 to avoid revealing existence.
- Keep the OpenAPI schema generated by FastAPI in sync; the frontend `shared` package types are generated from it (`npm run gen:api`).

# Alovia — Module 7: Symptom Tracking — Module Specification

**Version:** 1.0
**Date:** 2026-11-16
**Owner:** Raheem
**Status:** Final for build, except items tagged `[OPEN]` or `[CONFIRM AT RULE REVIEW]`.
**Related:** PRD v2 §4.7, TRD v2 §4.9, DRD v2 `symptom_logs` (this spec replaces that table definition, section 13).

---

## 0. How to use this document (read first)

These rules apply to anyone building from this document, including AI coding assistants.

1. **Use only what is written here.** Every symptom, input value, rule, level, threshold and output field is defined in this file.
2. **Never invent.** Do not add a symptom, rule, threshold, message or medical statement that is not in this file. If a case is not covered, stop and ask the owner.
3. **Tags:**
   - `[CONFIGURABLE]`: a setting in `config.yaml`, never hard-coded.
   - `[OPEN]`: not decided. Leave a clear placeholder; do not guess.
   - `[CONFIRM AT RULE REVIEW]`: the reviewing doctor must confirm before release (section 16).
4. **The rule tables in sections 7–9 are the source of truth.** The YAML rule files must match them row for row.
5. **Patient-facing text is not written here.** Only message keys and their intent (section 11). Final text goes in `messages.yaml`, approved by a doctor.
6. **Phone numbers are never written from memory.** They are copied from an official page during the build (section 11.3).
7. **One word, one meaning.** Use the glossary terms exactly.

---

## 1. Purpose and scope

### 1.1 What the module does
- Lets the patient log pregnancy symptoms, dated and tied to her pregnancy week.
- Checks every entry against fixed red-flag rules and immediately shows advice to seek care when needed.
- Shows the symptom history as charts to the patient and her doctor.
- Shows the doctor rule-based "pattern changes" (new or worsening symptoms).

### 1.2 What the module never does
- Never diagnoses or names a likely condition.
- Never says a symptom is normal or harmless because of the pregnancy stage.
- Never softens a red-flag rule because of the trimester.
- Never reads free-text notes for red flags (and says so to the patient).
- Never claims the doctor is watching entries live.
- Never offers kick counting (section 7.4).
- Never uses machine learning.

### 1.3 Safety principle
When in doubt, the stronger advice wins. A rule that cannot be evaluated (for example, no due date) is applied as if it matches.

---

## 2. Glossary

| Term | Meaning in this module |
|---|---|
| **check-in** | One submission by the patient. Contains one or more symptom entries. |
| **symptom entry** | One symptom inside a check-in, with its details. |
| **red-flag level** | Result of the rules for a check-in: `L0` (log only), `L2` (contact your doctor today), `L1` (go to hospital now). L1 is the most urgent. |
| **red-flag symptom** | A symptom in the "warning signs" group (section 5.2). Selecting it is enough to trigger its rule. |
| **common symptom** | A symptom in the "everyday symptoms" group (section 5.1). |
| **pattern change** | A doctor-only marker computed from the history (section 9). Codes P1–P5. |
| **PUQE score** | PUQE-24 score for nausea and vomiting, range 3–15 (section 8). |
| **pregnancy week** | Whole gestational weeks from the stored `due_date` (DRD formula). `null` if there is no due date. |
| **rules version** | Version string of the rule files, stored with every check-in. |
| **urgent button** | A permanent "I have an urgent symptom" button that opens the warning-signs group directly. |

---

## 3. Final decisions

| # | Topic | Decision | Date |
|---|---|---|---|
| D1 | Scope | Pregnancy only. Postpartum is not in version 1. | 2026-11-16 |
| D2 | Red-flag source | India's MCP card danger signs as the base, NHS guidance for detail (sources S1–S3) | 2026-11-16 |
| D3 | Levels | Two warning levels: L1 "go to hospital now", L2 "contact your doctor today", plus L0 | 2026-11-16 |
| D4 | Bleeding | Any vaginal bleeding is L1 (MCP card rule) | 2026-11-16 |
| D5 | Baby's movements | One-tap red flag. No kick counter (S4). | 2026-11-16 |
| D6 | Nausea and vomiting | Measured with PUQE-24 (S5, S6) | 2026-11-16 |
| D7 | Other severity | mild / moderate / severe | 2026-11-16 |
| D8 | Duration | Fixed ranges (section 5.4) | 2026-11-16 |
| D9 | Pattern changes | Shown to the doctor only. Thresholds are settings, reviewed by a doctor. | 2026-11-16 |
| D10 | Safety notices | Patient is told: not monitored live; notes are not read by the rules; urgent button always visible | 2026-11-16 |
| D11 | Mood | "Mood change" is a common symptom with a fixed support message. No depression questionnaire in v1. | 2026-11-16 |
| D12 | Storage of results | Red-flag level, matched rule IDs and shown messages are stored with every check-in | 2026-11-16 |
| D13 | Consent | The app-wide consent covers the doctor seeing symptom history | 2026-11-16 |
| D14 | Cravings | A common symptom with an optional "which food" text | 2026-11-16 |
| D15 | Mental-health helpline | A national helpline number, copied from an official page during the build `[OPEN]` | 2026-11-16 |
| D16 | Rule storage | YAML files in the repository; rules version stored per check-in | 2026-11-16 |
| D17 | Rule reviewer | A doctor using the platform signs off every rule before release (section 16) | 2026-11-16 |

---

## 4. User flows

### 4.1 Logging a check-in
1. The patient opens "Log symptoms". The page shows two groups: **Warning signs** (section 5.2) at the top, **Everyday symptoms** (section 5.1) below.
2. She selects one or more symptoms and fills in their details (section 5.3).
3. On submit, the backend validates (section 6), runs the rules (sections 7–9) and saves the check-in.
4. The patient sees the advice for the check-in's red-flag level (section 11.2).

### 4.2 Urgent button
Always visible in the app. It opens the Warning signs group only. Selecting any item there and submitting shows the L1 or L2 advice at once. Red-flag symptoms ask for no extra details, so this takes one tap plus submit.

### 4.3 History
The patient sees charts per symptom (how often, severity, duration) and the PUQE score over time, by pregnancy week.

### 4.4 Doctor
The doctor sees assigned patients' check-ins, red-flag levels, pattern changes and charts (section 12).

---

## 5. Input vocabulary (exact allowed values)

### 5.1 Everyday symptoms (common symptoms)

| ID | Shown as | Details asked |
|---|---|---|
| `nausea_vomiting` | Nausea / vomiting | PUQE questions (section 8), plus checkbox `unable_to_keep_fluids` |
| `fatigue` | Tiredness | severity, duration |
| `headache` | Headache | severity, duration, checkboxes `with_vision_problems`, `with_swelling` |
| `abdominal_discomfort` | Stomach / abdominal pain or discomfort | severity, duration, body area (`upper_abdomen` or `lower_abdomen`) |
| `back_pain` | Back pain | severity, duration |
| `breast_tenderness` | Breast tenderness | severity, duration |
| `food_craving` | Food craving | optional text: which food (max 100 characters) |
| `appetite_change` | Change in appetite | choice: `more`, `less` |
| `mood_change` | Mood change | severity |
| `other` | Something else | text name (max 100 characters), severity, duration, optional body area |

### 5.2 Warning signs (red-flag symptoms)
No severity or duration is asked. Selecting is enough.

| ID | Shown as | When shown |
|---|---|---|
| `vaginal_bleeding` | Bleeding from the vagina (any amount) | always |
| `fits` | Fits / convulsions | always |
| `vision_problems` | Blurred vision, flashing lights or spots | always |
| `fluid_leaking` | Water breaking or fluid leaking from the vagina | always |
| `high_fever` | High fever | always |
| `sudden_breathlessness` | Sudden breathlessness | always |
| `chest_pain` | Chest pain | always |
| `fainting` | Fainting | always |
| `baby_movements_reduced` | Baby moving less, or movements changed | pregnancy week ≥ `movements_from_week` (16), or week unknown |
| `baby_movements_never_felt` | Have not yet felt the baby move | pregnancy week ≥ `never_felt_from_week` (24) |
| `labour_pains` | Labour pains / regular tightenings | always; asks duration (section 5.4) |
| `severe_itching` | Severe itching | always |
| `sudden_swelling` | Sudden swelling of face, hands or body | always |
| `leg_pain_one_side` | Pain or swelling in one leg | always |
| `pain_passing_urine` | Pain or burning when passing urine | always |

### 5.3 Detail values

| Field | Allowed values |
|---|---|
| severity | `mild`, `moderate`, `severe` |
| body area (`other` only) | `head`, `chest`, `upper_abdomen`, `lower_abdomen`, `back`, `pelvis`, `legs`, `other` |
| time of occurrence | optional time of day (HH:MM) |
| notes | optional free text, max 500 characters, **never read by the rules** |

### 5.4 Duration ranges
`under_1_hour`, `1_to_6_hours`, `most_of_the_day`, `more_than_1_day`
For `labour_pains` only: `under_12_hours`, `more_than_12_hours`.

### 5.5 Pregnancy week
Computed at submission from `due_date` (DRD formula) and stored with the check-in. If there is no due date: `null`, and every week-based rule is applied as if it matches (section 1.3).

---

## 6. Validation

| Code | Problem | What happens |
|---|---|---|
| `V1` | No symptom selected, or a required detail missing | Return to the form with the field named. Nothing saved. |
| `V2` | A value not in section 5 | Return to the form with the field named. Nothing saved. |
| `V3` | Any unexpected engine failure | Save the check-in with `red_flag_level = L2`, rule ID `ERR`, show `msg_safe_fallback`, log the error. |

---

## 7. Red-flag rules (source of truth)

### 7.1 How the level is decided
1. Every rule whose condition matches **any entry in the check-in** is collected.
2. The check-in's level is the highest matched level: L1 > L2 > L0.
3. If nothing matches, the level is `L0`.
4. All matched rule IDs are stored, not only the winning one.

### 7.2 Level 1: "Go to hospital now"

| Rule ID | Condition | Source |
|---|---|---|
| L1-01 | `vaginal_bleeding` selected | S1 |
| L1-02 | `fits` selected | S1 |
| L1-03 | `headache` with `with_vision_problems` or `with_swelling` ticked (any severity) | S1, S3 |
| L1-04 | `headache` and `sudden_swelling` in the same check-in | S1, S3 |
| L1-05 | `vision_problems` selected `[CONFIRM AT RULE REVIEW]` (A1) | S3 |
| L1-06 | `fluid_leaking` selected | S1 |
| L1-07 | `high_fever` selected | S1 |
| L1-08 | `sudden_breathlessness` selected | S1, S2 |
| L1-09 | `chest_pain` selected | S3 |
| L1-10 | `fainting` selected | S2 |
| L1-11 | `abdominal_discomfort` with severity `severe` (either body area) | S2, S3 |
| L1-12 | `baby_movements_reduced` selected | S4 |
| L1-13 | `labour_pains` with duration `more_than_12_hours` | S1 |
| L1-14 | `labour_pains` and pregnancy week < `preterm_before_week` (37), or week `null` | S2 |

### 7.3 Level 2: "Contact your doctor today"

| Rule ID | Condition | Source |
|---|---|---|
| L2-01 | `severe_itching` selected | S3 |
| L2-02 | `sudden_swelling` selected (without `headache` in the check-in) | S3 |
| L2-03 | `leg_pain_one_side` selected | S3 |
| L2-04 | `pain_passing_urine` selected | S3 |
| L2-05 | `nausea_vomiting` with PUQE score ≥ 13 | S5, S6 |
| L2-06 | `nausea_vomiting` with `unable_to_keep_fluids` ticked | S6 |
| L2-07 | `headache` with severity `severe` (and no L1-03/L1-04 match) | S3 |
| L2-08 | `mood_change` with severity `severe` (also shows `msg_mood_support`) | — |
| L2-09 | `baby_movements_never_felt` selected | S4 |
| L2-10 | `labour_pains` at pregnancy week ≥ 37 and duration `under_12_hours` | — |
| L2-11 | **Catch-all:** any entry with severity `severe` not matched by another L1 or L2 rule | — |

### 7.4 Notes on specific rules
- **Baby's movements:** guidance advises not to wait until the next day when movements reduce or change, and does not recommend kick counting (S4). Do not build a counter, a "count 10 kicks" feature, or advice to drink something and wait.
- **Bleeding:** any amount is L1, following the MCP card (D4). Do not split by amount.
- **Trimester:** no rule is relaxed by pregnancy stage.

### 7.5 Messages added regardless of level
- Every check-in with `mood_change`: `msg_mood_support`.
- Every check-in with notes: `msg_notes_not_read` (shown once per check-in).

---

## 8. PUQE-24 score (nausea and vomiting)

Three questions about the **last 24 hours**. Each answer scores 1–5. Total = sum, range 3–15 (S5, S6).

| Question | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| How long have you felt nauseated or sick to your stomach? | not at all | 1 hour or less | 2–3 hours | 4–6 hours | more than 6 hours |
| How many times have you vomited? | none | 1–2 | 3–4 | 5–6 | 7 or more |
| How many times have you had retching or dry heaves without bringing anything up? | none | 1–2 | 3–4 | 5–6 | 7 or more |

`[CONFIRM AT RULE REVIEW]` (A2): copy the exact question and answer wording from the official PUQE-24 sheet before release. The nausea row above matches the sheet in S5. The vomiting and retching rows must be checked against it.

**Bands:** 3–6 `mild`, 7–12 `moderate`, 13–15 `severe` (S5, S6). The band is stored with the score. A score ≥ 13 triggers L2-05.

---

## 9. Pattern-change rules (doctor only)

Computed after every check-in from the patient's history within `pattern_window_days` (default 7). Never shown to the patient. All numbers are `[CONFIGURABLE]` and must be confirmed at rule review (A3).

| Code | Condition | Default setting |
|---|---|---|
| P1 | A common symptom is logged for the first time ever for this patient | — |
| P2 | An entry's severity is higher than every earlier entry of the same symptom within the window | window 7 days |
| P3 | The same common symptom is logged on at least `p3_min_days` different days within the window | 5 days |
| P4 | The PUQE band is higher than the band of the previous PUQE score | — |
| P5 | At least `p5_min_l2` check-ins at L2 within the window | 2 |

For `other`, P1–P3 compare by the exact text name (case-insensitive).

---

## 10. Output (stored per check-in)

```json
{
  "checkin_id": "uuid",
  "patient_id": "uuid",
  "created_at": "ISO-8601 timestamp",
  "source": "form",
  "pregnancy_week": 27,
  "rules_version": "1.0.0",
  "entries": [
    {
      "symptom": "headache",
      "severity": "severe",
      "duration": "1_to_6_hours",
      "with_vision_problems": true,
      "with_swelling": false
    }
  ],
  "red_flag_level": "L1",
  "matched_rules": ["L1-03"],
  "message_keys": ["msg_level1_go_now"],
  "pattern_changes": ["P1"]
}
```

**Field rules:**
- `source`: `form` or `urgent_button`.
- `pregnancy_week`: integer or `null`.
- `red_flag_level`: `L0`, `L1`, `L2`.
- `matched_rules`: all matched rule IDs (may include lower-level ones); `ERR` for V3.
- `pattern_changes`: list of P-codes; stored, but returned only to doctors.
- A PUQE entry also stores `puqe_answers` (three integers 1–5), `puqe_score` and `puqe_band`.

---

## 11. Patient-facing behaviour and wording

### 11.1 Wording rules
- Never say "normal", "harmless", "nothing to worry about", or name a possible condition.
- Advice is about **who to contact and how fast**, never about treatment or medicines.
- Advice appears immediately after submit and is not delayed by doctor review.

### 11.2 Message keys (intent only; final text in `messages.yaml`, doctor-approved)

| Key | Intent |
|---|---|
| `msg_level1_go_now` | Go to the nearest hospital now; take your MCP card; call the emergency number if you cannot travel |
| `msg_level2_contact_today` | Contact your doctor today; if it gets worse, go to hospital |
| `msg_level0_logged` | Your symptom is saved; tell your doctor at your next visit if it continues; use the urgent button if anything changes |
| `msg_mood_support` | You are not alone; talk to your doctor; national helpline number (section 11.3) |
| `msg_notes_not_read` | Notes are not checked automatically; use the warning signs list for anything urgent |
| `msg_not_monitored_live` | Your doctor does not see entries in real time; in an emergency go to hospital (shown on the log page and the urgent button page) |
| `msg_safe_fallback` | Something went wrong; if you feel unwell, contact your doctor or go to hospital |

### 11.3 Phone numbers
The emergency number and the mental-health helpline are `[OPEN]`. Each must be copied from an official Government of India or Telangana page during the build, with the page URL and the date recorded in `messages.yaml`. Never written from memory.

### 11.4 Educational text
Any general text about common symptoms comes from the knowledge base or the Journey content, with its source. This module adds none of its own.

---

## 12. Doctor view

- **Patient list order:** patients with an L1 check-in in the last `pattern_window_days` first, then L2 or P5, then the rest; newest first within each group. *(Superseded for the dashboard by Dashboard spec §6, which orders by unseen inbox items created from these same events — owner decision 2026-11-20, DEC-103.)*
- **Per patient:** check-in timeline with levels and matched rule IDs; pattern-change badges (P1–P5) with the symptom named; charts per symptom by pregnancy week; PUQE score chart with bands.
- **Read-only:** the doctor cannot edit or delete check-ins. Doctor comments on symptoms are `[OPEN]` (not in v1).

---

## 13. Data and files

### 13.1 Repository layout

```
symptom_module/
├── rules/
│   ├── config.yaml          # rules_version and section 13.2 settings
│   ├── symptoms.yaml        # section 5
│   ├── red_flags.yaml       # section 7
│   ├── puqe.yaml            # section 8
│   ├── patterns.yaml        # section 9
│   └── messages.yaml        # section 11 (final text, doctor-approved)
├── engine/
├── tests/
└── docs/
    ├── symptom_tracking_module_spec.md
    └── rule_review_signoff.md
```

### 13.2 `config.yaml` settings (all `[CONFIGURABLE]`)

| Setting | Default |
|---|---|
| `rules_version` | `1.0.0` |
| `pattern_window_days` | 7 |
| `p3_min_days` | 5 |
| `p5_min_l2` | 2 |
| `movements_from_week` | 16 |
| `never_felt_from_week` | 24 |
| `preterm_before_week` | 37 |

### 13.3 Database tables (replace DRD v2 `symptom_logs`)

**`symptom_checkins`**

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `source` | text | `form` / `urgent_button` |
| `pregnancy_week` | integer, nullable | at submission |
| `red_flag_level` | text | `L0` / `L1` / `L2` |
| `matched_rules` | jsonb | list of rule IDs |
| `message_keys` | jsonb | messages shown |
| `pattern_changes` | jsonb | P-codes |
| `rules_version` | text | |
| `created_at` | timestamptz | |

**`symptom_logs`** (one row per symptom entry)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `checkin_id` | uuid, FK → `symptom_checkins.id` | |
| `patient_id` | uuid, FK → `patients.id` | copied for fast queries |
| `symptom` | text | section 5 ID |
| `severity` | text, nullable | |
| `duration` | text, nullable | |
| `body_area` | text, nullable | |
| `details` | jsonb, nullable | checkboxes, PUQE answers/score/band, craving text, appetite choice, `other` name |
| `occurred_at` | time, nullable | |
| `notes` | text, nullable | |
| `created_at` | timestamptz | |

Append-only: no edits or deletes in v1. Row-Level Security deny-by-default is added in Phase 8 (DEC-022).

### 13.4 API endpoints (proposed)
`[OPEN]` Names to be aligned with the project-wide route design.

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/symptoms/checkins` | patient | Validate, run rules, save, return level and messages |
| GET | `/patients/{patient_id}/symptoms/checkins` | patient (own) / doctor (assigned) | History (pattern changes included for doctors only) |
| GET | `/patients/{patient_id}/symptoms/charts` | patient (own) / doctor (assigned) | Aggregated chart data |
| GET | `/doctor/symptoms/priority-list` | doctor | Section 12 ordering |
| GET | `/symptoms/vocabulary` | patient | Symptom list for the form, filtered by pregnancy week |

---

## 14. Tests (all must pass before release)

1. One test per rule in sections 7.2 and 7.3, including L1-03 vs L2-07 and L1-04 vs L2-02.
2. Highest-level-wins with mixed check-ins (L1 + L2 → L1; L2 + L0 → L2).
3. Week `null` → L1-14 applies, and `baby_movements_reduced` is offered.
4. Week boundaries: 15/16 for movements, 23/24 for never-felt, 36/37 for labour pains.
5. Catch-all L2-11 fires for a severe `back_pain` and for a severe `other`.
6. PUQE: score 3, 6, 7, 12, 13, 15 give the correct band; 13 triggers L2-05.
7. P1–P5, each with a passing and a failing history, using the default settings and one changed setting.
8. Pattern changes never appear in patient API responses.
9. Notes containing alarming words do **not** change the level (the rules ignore notes), and `msg_notes_not_read` is shown.
10. V1/V2 save nothing; V3 saves with L2 and `ERR`.

---

## 15. Out of scope (version 1) and Do not

**Out of scope:** postpartum symptoms and danger signs; newborn symptoms; depression or anxiety questionnaires; reminders and push notifications; doctor comments on entries; reading notes with AI; wearable or device data; editing or deleting entries.

**Do not:**
- Do not add symptoms, rules or thresholds that are not in this document.
- Do not relax a rule by trimester.
- Do not build a kick counter.
- Do not write phone numbers from memory.
- Do not show pattern changes to the patient.
- Do not delay red-flag advice for doctor review.
- Do not release before the rule review sign-off (section 16).

---

## 16. Rule review (before release)

A doctor using the platform checks every rule in sections 7–9, the PUQE wording, and every final message against the sources, and records each item in `docs/rule_review_signoff.md` (rule ID, checked yes/no, comment, name, date, rules version). Any rule change → raise `rules_version` → re-review the changed rows.

### 16.1 Assumptions to confirm

| ID | Assumption |
|---|---|
| A1 | Vision problems on their own (without headache) are L1. |
| A2 | PUQE vomiting and retching answer wording matches the official sheet. |
| A3 | Pattern defaults (7-day window, 5 of 7 days, 2 L2 check-ins) are sensible. |
| A4 | Labour pains at 37+ weeks under 12 hours are L2 ("contact your doctor"), not L1. |

---

## 17. Open items

| Item | Tag |
|---|---|
| Emergency number and mental-health helpline (official source) | `[OPEN]` |
| Final message text, doctor-approved | `[OPEN]` |
| Rule review sign-off, including A1–A4 | `[OPEN]` |
| API route names aligned with project-wide design | `[OPEN]` |
| Screen designs (log page, urgent button, charts, doctor view) | `[OPEN]` |
| Postpartum extension (future version) | `[OPEN]` |

---

## Sources

| ID | Source |
|---|---|
| S1 | MoHFW / NHM, Mother and Child Protection (MCP) Card, danger signs during pregnancy. https://nhm.gov.in/New_Updates_2018/NHM_Components/Immunization/Guildelines_for_immunization/MCP_Card_English_version.pdf ; summary in POSHAN Abhiyaan takeaway: https://wcd.nic.in/poshan/NNM-Web-Contents/LEFT-MENU/ILA/TakeAways/Takeaway_3_1_English.pdf |
| S2 | NHS, "Pregnancy symptoms you need to get help for" and "Stomach pain in pregnancy". https://www.nhs.uk/pregnancy/common-symptoms/pregnancy-symptoms-you-need-to-get-help-for/ ; https://www.nhs.uk/pregnancy/common-symptoms/stomach-pain |
| S3 | NHS trust patient guidance on urgent symptoms (severe headache, blurred vision, swelling, pain below ribs, leg pain, chest pain, itching). Milton Keynes University Hospital: https://www.mkuh.nhs.uk/?p=28141 ; NHS Tayside: https://www.nhstayside.scot.nhs.uk/OurServicesA-Z/MaternityServices/PROD_344701 |
| S4 | HSE Ireland, Reduced Fetal Movements plain-language summary (kick counting not recommended). https://hse.ie/eng/about/who/acute-hospitals-division/woman-infants/clinical-guidelines/reduced-fetal-movements-plain-language-summary.pdf ; MKUH reduced fetal movements guideline and leaflet: https://www.mkuh.nhs.uk/?p=50782 |
| S5 | Association of Ontario Midwives, PUQE-24 scale sheet (Motherisk). https://www.ontariomidwives.ca/sites/default/files/Clinical%20Topics/NVP%20algorithm%20-%20PUQE%20score%20-%20V01.pdf |
| S6 | Safer Care Victoria, Nausea and Vomiting in Pregnancy clinical guidance (Oct 2024). https://www.safercare.vic.gov.au/sites/default/files/2024-12/Nausea%20and%20vomiting%20in%20pregnancy%20October%202024_0.pdf |
| S7 | Review of Android apps for monitoring pregnancy symptoms and care, Ingénierie des Systèmes d'Information 29(2), 2024 (research gap). https://www.iieta.org/node/16916 |

> **Disclaimer:** this module records symptoms and gives rule-based prompts to seek care. It does not diagnose and does not replace a doctor or emergency services.

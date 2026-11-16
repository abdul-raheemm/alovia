# Alovia — Module 3: Genetic Risk Assessment — Module Specification

**Version:** 1.0
**Date:** 2026-11-16
**Owner / builder:** Raheem
**Status:** Final for build, except items tagged `[OPEN]`.
**Supersedes:** `genetic_module_build_plan.md` (v1, 2026-10-25) wherever the two differ. Differences are listed in section 18.

---

## 0. How to use this document (read first)

These rules apply to anyone building from this document, including AI coding assistants.

1. **Use only what is written here.** Every allowed input value, rule, percentage, status and output field is defined in this file.
2. **Never invent.** Do not add a percentage, rule, condition, input value, status or patient-facing sentence that is not in this file. If a case is not covered, stop and ask the owner.
3. **Tags:**
   - `[CONFIGURABLE]`: must be a setting in `config.yaml`, never hard-coded.
   - `[OPEN]`: not decided. Do not build a guess. Leave a clear placeholder and list it.
   - `[CONFIRM AT RULE REVIEW]`: an assumption the reviewing doctor must confirm before release (section 13.1).
4. **Rule tables in section 7 are the source of truth.** The YAML rule files must match them row for row. If they ever disagree, this document wins until it is updated.
5. **Patient-facing text is not written in this document.** Only message keys and their intent are defined (section 11). Final text lives in `messages.yaml` and must be approved by a doctor.
6. **One word, one meaning.** Use the terms exactly as defined in the glossary (section 2). Do not use synonyms in code, data or UI.

---

## 1. Purpose and scope

### 1.1 What the module does
Takes what a pregnant patient knows about her own and her husband's (the baby's biological father's) genetic status for a small set of well-known inherited conditions, applies fixed inheritance rules, and shows:
- the chance that the baby is affected, and the chance that the baby is a carrier, **only when the information is confirmed and consistent**;
- otherwise, a clear next step: testing, counselling, or doctor review.

It is an **educational estimate**, not a diagnosis.

### 1.2 What the module never does
- Never diagnoses, and never states that a baby will or will not have a condition.
- Never shows 0% or "no risk". It shows "not expected based on the information given".
- Never asks for, guesses, stores, or shows the sex of the baby (section 11.3, PCPNDT Act).
- Never predicts how severe a condition will be.
- Never reads or interprets uploaded genetic reports.
- Never uses machine learning.
- Never lets a doctor type a percentage by hand. Percentages come only from the rule engine.

### 1.3 Safety principle
A missing number is always safer than a wrong number. If anything is unknown, weak, conflicting or unsupported, the engine shows no number and gives the next step.

---

## 2. Glossary (fixed meanings)

| Term | Meaning in this module |
|---|---|
| **mother** | The pregnant patient using the app. |
| **father** | The baby's biological father. His data is entered by the patient. |
| **affected** | The person has the condition (diagnosed). |
| **carrier** | The person carries one copy of a variant and is usually healthy. Used for recessive and X-linked conditions only. |
| **tested_negative** | A test showed the person is not a carrier and not affected for that condition. |
| **not_affected** | The person does not have the condition. Used for Marfan syndrome and for the father in haemophilia. |
| **unknown** | The status is not known, or the evidence for it is weak (section 6.2). |
| **evidence** | How the person knows their status (section 5.3). |
| **haemoglobin group** | β-thalassaemia, sickle cell and related haemoglobin variants, assessed together in one rule table, because the variants combine with each other. |
| **condition status** | The result for one condition: `calculated`, `needs_testing_or_counselling`, `counselling_flag`, `conflict`, `error`, `not_assessed` (section 8.1). |
| **review status** | Where the whole assessment is in the doctor's workflow: `pending_review` or `reviewed` (section 10). **Not** the same as condition status. |
| **rule ID** | The ID of the rule-table row that produced a result, e.g. `HBB-12`. |
| **rules version** | The version string of the rule files used for a result, e.g. `1.0.0`. Stored with every assessment. |
| **risk indicated** | Defined exactly in section 9.4. |
| **not expected** | The rules give no route for this outcome from the information given. Displayed instead of 0%. |

---

## 3. Final decisions

| # | Topic | Decision | Date |
|---|---|---|---|
| D1 | Method | Rule-based inheritance engine, no ML | 2026-10-25 |
| D2 | Conditions | Haemoglobin group (β-thalassaemia, sickle cell, with HbE / HbD as recognised variants), haemophilia (X-linked recessive), Marfan syndrome (autosomal dominant) | 2026-11-16 |
| D3 | Who enters data | The patient enters both parents' data. The doctor reviews and may correct inputs (section 10.3). | 2026-10-25 |
| D4 | Patient sees result before review | Yes: calculated results are shown immediately with a "review with your doctor" message. `[CONFIGURABLE]` as `show_result_before_review` (default `true`). | 2026-11-16 |
| D5 | Conflicts and errors | Never show a number. The case goes to the doctor. | 2026-10-25 |
| D6 | Rule storage | YAML files in the code repository are the master copy. Each assessment stores the rules version. No `genetic_conditions` database table. | 2026-11-16 |
| D7 | Rule reviewer | A doctor using the platform reviews every rule row once before release, and again after any rule change (section 13). | 2026-11-16 |
| D8 | Case reviewer | The patient's assigned doctor reviews each assessment (section 10). | 2026-11-16 |
| D9 | Consent | One application-wide consent covers mother, father and patient data. | 2026-10-25 |
| D10 | Haemoglobin group | β-thalassaemia and sickle cell are assessed together, including the β-thalassaemia × sickle cell pairing. | 2026-11-16 |
| D11 | Evidence values | Add `hplc_report` and `sickle_status_card`. `blood_count_only` and `family_history_only` count as weak evidence (treated as `unknown`). | 2026-11-16 |
| D12 | Consanguinity | In version 1, as a flag and counselling message only. It never changes a number. | 2026-11-16 |
| D13 | Timing prompt | When risk is indicated, prompt the patient to speak to her doctor soon and set the doctor-review priority to `high`. | 2026-11-16 |
| D14 | Input order | Both parents' forms are always shown. The father's answers default to `unknown`. A testing nudge explains who should be tested next. | 2026-11-16 |
| D15 | Wording | Haemophilia results worded "if the baby is a boy / a girl". Marfan wording says "inheriting the condition", never severity. "No family history" never means "no risk". | 2026-11-16 |
| D16 | Disclaimer | Fixed wording, section 11.2. | 2026-10-25 |

---

## 4. User flow

### 4.1 Patient flow
1. The patient opens the Genetic Risk page. If the app-wide consent has not been accepted, the page asks for it first.
2. **Haemoglobin group section** (always shown): status and evidence for the mother, then for the father.
3. **Haemophilia section:** entry question first (section 5.5). Full form only if the answer is `yes` or `not_sure`.
4. **Marfan section:** entry question first (section 5.5). Full form only if the answer is `yes` or `not_sure`.
5. **General questions:** consanguinity (section 5.4).
6. The patient submits. The backend validates the input (section 6.1).
   - Missing or invalid input (errors `E1`, `E2`): returned to the form to fix. Nothing is saved.
7. The engine runs, and the assessment is saved with `review_status = pending_review`.
8. The patient sees the result screen (section 11.4).
9. After the doctor reviews, the patient also sees the doctor's note.

### 4.2 Doctor flow
1. The doctor opens the review queue (section 10.1).
2. The doctor opens an assessment and sees inputs, rule IDs, results, warnings, flags and the patient's gestational age (if a due date is stored).
3. The doctor does one of the following:
   - confirms and adds a counselling note;
   - corrects inputs (creates a new assessment, section 10.3) and adds a note.
4. `review_status` becomes `reviewed`.

---

## 5. Input vocabulary (exact allowed values)

### 5.1 Haemoglobin group status (per parent)

| Value | Short code | Meaning |
|---|---|---|
| `tested_negative` | N | Tested, no haemoglobin variant found |
| `beta_thal_carrier` | B | β-thalassaemia carrier (trait / minor) |
| `sickle_carrier` | S | Sickle cell carrier (trait, HbAS) |
| `hbe_carrier` | E | HbE carrier |
| `hbd_carrier` | D | HbD carrier |
| `beta_thal_major` | BB | Has β-thalassaemia major (affected) |
| `sickle_cell_disease` | SS | Has sickle cell disease (affected) |
| `other_or_unclear` | O | Report shows another or an unclear variant, or a combined (compound) condition |
| `unknown` | U | Not tested or not known |

### 5.2 Haemophilia status

| Parent | Allowed values |
|---|---|
| mother | `tested_negative`, `carrier`, `affected`, `unknown` |
| father | `affected`, `not_affected` |

Haemophilia A and B are treated the same `[CONFIRM AT RULE REVIEW]` (A3). The father is never `carrier` or `unknown` (section 6.3, C2).

### 5.3 Marfan syndrome status (per parent)
`affected`, `not_affected`, `unknown`

### 5.4 Evidence ("how do you know?")

| Value | Strength | Allowed with |
|---|---|---|
| `hplc_report` | strong | haemoglobin group only |
| `sickle_status_card` (national sickle cell genetic status card, S5) | strong for sickle status only | haemoglobin group, statuses `tested_negative`, `sickle_carrier`, `sickle_cell_disease` only |
| `test_report` | strong | all conditions |
| `doctor_told` | strong | all conditions |
| `blood_count_only` | **weak** | haemoglobin group only |
| `family_history_only` | **weak** | all conditions |

Evidence is required for every status except `unknown`.

### 5.5 Entry questions (haemophilia and Marfan only)
"Has anyone in your family or your husband's family been diagnosed with [condition], or has either of you been told you have or carry it?"
Allowed: `yes`, `no`, `not_sure`.
- `no`: condition status `not_assessed`. No form, no number.
- `yes`: show the full form.
- `not_sure`: show the full form. All answers may be `unknown`.

The haemoglobin group has no entry question. It is always assessed, because Indian guidance recommends haemoglobin carrier screening for all pregnant women (Sources S6, S7).

### 5.6 Previous child (per condition, asked inside each shown section)
"Has a previous child of this couple been diagnosed with [condition]?"
Allowed: `yes`, `no`, `not_sure`, `no_previous_child`.

### 5.7 Consanguinity (general)
"Are you and your husband related by blood (for example, cousins)?"
Allowed: `yes`, `no`, `not_sure`.

### 5.8 Gestational age
Not entered here. Taken from the patient's stored `due_date` if present, using the DRD formula. If there is no due date, the timing prompt still shows, without a week number.

---

## 6. Validation, evidence handling and conflicts

### 6.1 Validation (before the engine runs)

| Code | Problem | What happens |
|---|---|---|
| `E1` | A required field is missing | Return to the form with the field named. Nothing saved. |
| `E2` | A value is not in section 5, or the evidence is not allowed with that status/condition (section 5.4) | Return to the form with the field named. Nothing saved. |

### 6.2 Evidence handling (applied before the rule tables)

| Case | Treated as | Warning key |
|---|---|---|
| Evidence `blood_count_only` (any haemoglobin status) | `unknown` | `warn_blood_count_not_enough` |
| Evidence `family_history_only` (any status, any condition) | `unknown` | `warn_family_history_not_enough` |
| Haemoglobin `tested_negative` with evidence `sickle_status_card` | `unknown` `[CONFIRM AT RULE REVIEW]` (A1) | `warn_card_checks_sickle_only` |

Reasons: a blood count alone is not a reliable carrier test (S9). Family history alone cannot confirm carrier status (PRD §4.3).

### 6.3 Conflicts and engine errors (after evidence handling)

| Code | Condition | Case | Condition status |
|---|---|---|---|
| `C1` | Haemoglobin group | A previous child has thalassaemia major or sickle cell disease (`yes`), but either parent is `tested_negative` | `conflict` |
| `C2` | Haemophilia | Father marked `carrier` or `unknown` (only possible through the API, not the form) | `conflict` |
| `F1` | Haemophilia | A previous son has haemophilia (`yes`) and the mother is `tested_negative` | `counselling_flag` (new mutations happen, S3) |
| `F2` | Marfan | A previous child has Marfan (`yes`) and both parents are `not_affected` | `counselling_flag` (new mutations happen, S4) |
| `E3` | Any | Rule file missing, or no rule row matches | `error` (saved, logged, doctor review) |
| `E4` | Any | Any unexpected engine failure | `error` (saved, logged, doctor review, safe fallback message) |

New conflict types are added to `conflicts.yaml` and to this table, never as special cases in code.

### 6.4 Priority (per condition)
If more than one applies to one condition, the highest wins:
`error` > `conflict` > `counselling_flag` > `needs_testing_or_counselling` > `calculated` > `not_assessed`

---

## 7. Rule tables (source of truth)

**Display format for chances:** "1 in 2 (50%)", "1 in 4 (25%)", "all children". Outcomes with no route are shown as `not expected`, never 0%.

### 7.1 Haemoglobin group (autosomal recessive, combined variants)
The order of parents does not matter. Codes are from section 5.1. Every unordered pair of codes appears exactly once below. Any pair not matched → `E3`.

| Rule ID | Pair(s) | Status | Outcomes per pregnancy | Source |
|---|---|---|---|---|
| HBB-01 | N + N | calculated | Affected: not expected. Carrier: not expected. | S1 |
| HBB-02 | N + B | calculated | Affected: not expected. β-thal carrier: 1 in 2. Neither: 1 in 2. | S1 |
| HBB-03 | N + S | calculated | Affected: not expected. Sickle carrier: 1 in 2. Neither: 1 in 2. | S1, S2 |
| HBB-04 | N + E | calculated | Affected: not expected. HbE carrier: 1 in 2. Neither: 1 in 2. `[CONFIRM AT RULE REVIEW]` (A2) | S2 |
| HBB-05 | N + D | calculated | Affected: not expected. HbD carrier: 1 in 2. Neither: 1 in 2. `[CONFIRM AT RULE REVIEW]` (A2) | S2 |
| HBB-06 | N + BB | calculated | Affected: not expected. β-thal carrier: all children. `[CONFIRM AT RULE REVIEW]` (A4) | S1 |
| HBB-07 | N + SS | calculated | Affected: not expected. Sickle carrier: all children. `[CONFIRM AT RULE REVIEW]` (A4) | S2 |
| HBB-08 | N + O | counselling_flag | — | — |
| HBB-09 | N + U | calculated | Affected: not expected. Carrier: cannot be calculated (depends on the other parent). Warning `warn_carrier_depends_on_partner`. | S1 |
| HBB-10 | B + B | calculated | β-thalassaemia major: 1 in 4. β-thal carrier: 1 in 2. Neither: 1 in 4. | S1 |
| HBB-11 | S + S | calculated | Sickle cell disease: 1 in 4. Sickle carrier: 1 in 2. Neither: 1 in 4. | S2 |
| HBB-12 | B + S | calculated | Sickle cell disease (sickle β-thalassaemia): 1 in 4. β-thal carrier: 1 in 4. Sickle carrier: 1 in 4. Neither: 1 in 4. | S1 |
| HBB-13 | B+E, B+D, S+E, S+D, E+E, E+D, D+D | counselling_flag | — (severity of these combinations varies, S2) | S2 |
| HBB-14 | BB or SS with any of B, S, E, D, BB, SS | counselling_flag | — | — |
| HBB-15 | O with any of B, S, E, D, BB, SS, O | counselling_flag | — | — |
| HBB-16 | U with any of B, S, E, D, BB, SS, U | needs_testing_or_counselling | — (testing nudge, section 9.3) | S6, S7 |
| HBB-17 | U + O | counselling_flag | — | — |

Coverage check: 9 codes give 45 unordered pairs. HBB-01…09 = 9, HBB-10…12 = 3, HBB-13 = 7, HBB-14 = 11, HBB-15 = 7, HBB-16 = 7, HBB-17 = 1. Total 45.

### 7.2 Haemophilia (X-linked recessive)
The order of parents matters. Results are given **conditionally** for a boy and for a girl. The baby's sex is never asked for or shown.

| Rule ID | Mother | Father | Status | If the baby is a boy | If the baby is a girl | Source |
|---|---|---|---|---|---|---|
| HEM-01 | tested_negative | not_affected | calculated | Haemophilia: not expected | Carrier: not expected | S3 |
| HEM-02 | carrier | not_affected | calculated | Haemophilia: 1 in 2. Unaffected: 1 in 2. | Carrier: 1 in 2. Neither: 1 in 2. Haemophilia: not expected. Note `note_carrier_girls_may_bleed`. | S3 |
| HEM-03 | tested_negative | affected | calculated | Haemophilia: not expected | Carrier: all daughters. Note `note_carrier_girls_may_bleed`. | S3 |
| HEM-04 | carrier | affected | counselling_flag | — | — | S3 |
| HEM-05 | affected | any | counselling_flag | — | — | — |
| HEM-06 | unknown | not_affected | needs_testing_or_counselling | — | — | S3 |
| HEM-07 | unknown | affected | needs_testing_or_counselling | — | — | S3 |

Always attach note `note_no_family_history_not_no_risk` to HEM-01 (about one third of haemophilia cases have no family history, S3).

### 7.3 Marfan syndrome (autosomal dominant)
The order of parents does not matter.

| Rule ID | Parents | Status | Outcomes per pregnancy | Source |
|---|---|---|---|---|
| MAR-01 | not_affected + not_affected | calculated | Inheriting from a parent: not expected. Note `note_new_cases_can_occur`. | S4 |
| MAR-02 | affected + not_affected | calculated | Inheriting the condition: 1 in 2. Note `note_severity_varies`. | S4 |
| MAR-03 | affected + affected | counselling_flag | — | — |
| MAR-04 | unknown + any | needs_testing_or_counselling | — | — |

---

## 8. Engine output

### 8.1 Condition status values

| Value | Number shown? | Meaning |
|---|---|---|
| `calculated` | Yes (subject to `show_result_before_review`) | A rule row produced outcomes |
| `needs_testing_or_counselling` | No | At least one needed status is unknown |
| `counselling_flag` | No | Outside what the rules support |
| `conflict` | No | Answers contradict each other |
| `error` | No | Rule or engine problem |
| `not_assessed` | No | The entry question was answered `no` |

### 8.2 Output structure (returned by the engine and stored in `results`)

```json
{
  "assessment_id": "uuid",
  "rules_version": "1.0.0",
  "created_at": "ISO-8601 timestamp",
  "review_status": "pending_review",
  "priority": "normal",
  "show_numbers_to_patient": true,
  "conditions": [
    {
      "condition": "haemoglobin_group",
      "rule_id": "HBB-12",
      "status": "calculated",
      "outcomes": [
        { "outcome": "sickle_cell_disease", "chance": "1_in_4", "percent": 25 },
        { "outcome": "beta_thal_carrier", "chance": "1_in_4", "percent": 25 },
        { "outcome": "sickle_carrier", "chance": "1_in_4", "percent": 25 },
        { "outcome": "neither", "chance": "1_in_4", "percent": 25 }
      ],
      "outcomes_if_boy": null,
      "outcomes_if_girl": null,
      "message_keys": ["result_hbb_calculated"],
      "warnings": [],
      "notes": []
    }
  ],
  "flags": {
    "consanguinity": false,
    "risk_indicated": true,
    "timing_prompt": true
  },
  "disclaimer_key": "disclaimer_main"
}
```

**Field rules:**
- `chance` allowed values: `1_in_2`, `1_in_4`, `all_children`, `not_expected`, `not_calculable`.
- `percent`: 50, 25 or 100 to match `chance`. `null` for `not_expected` and `not_calculable`. **Never 0.**
- `outcomes` is used for the haemoglobin group and Marfan. `outcomes_if_boy` / `outcomes_if_girl` are used for haemophilia only. Unused fields are `null`.
- For any status other than `calculated`, all outcome fields are `null`.
- `show_numbers_to_patient` = value of `show_result_before_review` when the assessment was created, or `true` after review.

---

## 9. Extra prompts and flags

### 9.1 Consanguinity
If the answer is `yes`: set `flags.consanguinity = true` and add message `msg_consanguinity_counselling`. If `not_sure`: add the same message. **No number changes.** Reason: about 18% of women in Telangana report marriage to a blood relative (S8), and related couples are more likely to share a recessive variant.

### 9.2 Timing prompt
If `flags.risk_indicated = true`: set `flags.timing_prompt = true`, add message `msg_speak_to_doctor_soon`, and set `priority = high`. Reason: prenatal testing for these conditions is only possible at certain stages of pregnancy (S10). The patient message must not name procedures or week numbers.

### 9.3 Testing nudge
- Haemoglobin group, mother `unknown`: add `msg_hplc_test_suggested` (ask the doctor about an HPLC test, ideally in the first trimester; S6, S7).
- Haemoglobin group, mother is a carrier or affected and father `unknown`: add `msg_partner_test_suggested` (S6).
- Haemophilia, mother `unknown`: add `msg_haemophilia_carrier_test_suggested`.
- Marfan, any parent `unknown`: add `msg_marfan_assessment_suggested`.

### 9.4 Definition of "risk indicated"
`flags.risk_indicated = true` if **any** condition has:
- status `calculated` with any outcome naming a condition (not just carrier) at `1_in_2`, `1_in_4` or `all_children`; or
- status `counselling_flag` or `conflict`; or
- status `needs_testing_or_counselling` where the **other** parent is a carrier or affected.

Otherwise `false`.

---

## 10. Doctor case review

### 10.1 Review queue
Shows assessments for the doctor's assigned patients with `review_status = pending_review`. Sorted by `priority` (`high` first), then oldest first.

### 10.2 Review states
`pending_review` → `reviewed`. Every new assessment starts as `pending_review`.

### 10.3 Doctor actions

| Action | Effect |
|---|---|
| Confirm | Adds `doctor_note` (required), sets `reviewed`, `reviewed_by`, `reviewed_at` |
| Correct inputs | Creates a **new** assessment with corrected inputs. The engine re-runs. The new row has `supersedes_id` = old row, `submitted_by` = the doctor, and goes straight to `reviewed` with the doctor's note. The old row is never edited. |

The doctor cannot type or override percentages.

### 10.4 What the patient sees after review
The latest reviewed assessment, its results (numbers now shown), and the doctor's note.

---

## 11. Wording rules

### 11.1 General
- Never say "will", "will not", "safe", "no risk" or "0%".
- Use "chance" and "not expected based on the information you gave".
- Haemophilia: "If the baby is a boy… / If the baby is a girl…".
- Marfan: "inheriting the condition". Never describe severity.
- "No family history" never means "no risk".
- Educational information and doctor-confirmed information are always visually distinct.

### 11.2 Fixed disclaimer (`disclaimer_main`)
"This is for knowledge only and is not medical advice. Counselling is recommended."
Shown on every result screen.

### 11.3 PCPNDT Act rule (legal)
The Indian PCPNDT Act prohibits communicating the sex of a foetus by any means (S11). Therefore the module:
- never asks for the baby's sex;
- never infers or stores it;
- always shows both "if boy" and "if girl" results together for haemophilia, never one alone.

### 11.4 Message keys (intent only; final text in `messages.yaml`, doctor-approved)

| Key | Intent |
|---|---|
| `review_with_doctor` | Shown with calculated results: review these results with your doctor; do not rely on them alone |
| `results_after_review` | Shown when `show_numbers_to_patient = false`: results will appear after your doctor reviews them |
| `msg_sent_for_review` | Conflict or error: some answers need your doctor's review; sent to your doctor; no result shown until then |
| `msg_counselling_flag` | Your combination needs a specialist's advice; please discuss with your doctor |
| `msg_needs_testing` | Some information is missing; testing or counselling can help |
| `msg_not_assessed` | No family history given for this condition; mention to your doctor if anything changes |
| `msg_hplc_test_suggested` | Ask your doctor about a haemoglobin (HPLC) test, ideally early in pregnancy |
| `msg_partner_test_suggested` | Because you are a carrier, your husband's test result is needed |
| `msg_haemophilia_carrier_test_suggested` | Carrier testing for women is available; discuss with your doctor |
| `msg_marfan_assessment_suggested` | A doctor can assess this; discuss with your doctor |
| `msg_consanguinity_counselling` | Related couples are advised to discuss genetic counselling with their doctor |
| `msg_speak_to_doctor_soon` | Some tests in pregnancy can only be done at certain stages; please speak to your doctor soon |
| `msg_safe_fallback` | Something went wrong; your doctor has been informed |
| `result_hbb_calculated`, `result_hem_calculated`, `result_mar_calculated` | Short plain-language explanation of the calculated outcomes |
| `warn_blood_count_not_enough` | A blood count alone cannot confirm carrier status |
| `warn_family_history_not_enough` | Family history alone cannot confirm status |
| `warn_card_checks_sickle_only` | The sickle cell card may not check for β-thalassaemia |
| `warn_carrier_depends_on_partner` | The carrier chance depends on the other parent's result |
| `note_carrier_girls_may_bleed` | Girls who are carriers sometimes have bleeding symptoms (S3) |
| `note_no_family_history_not_no_risk` | Haemophilia can appear in families with no history (S3) |
| `note_new_cases_can_occur` | Marfan can appear for the first time in a child (S4) |
| `note_severity_varies` | How the condition affects a person varies, even within a family (S4) |
| `disclaimer_main` | Section 11.2 |

---

## 12. Data and files

### 12.1 Repository layout

```
genetic_module/
├── rules/
│   ├── config.yaml              # rules_version, show_result_before_review
│   ├── haemoglobin_group.yaml   # section 7.1
│   ├── haemophilia.yaml         # section 7.2
│   ├── marfan.yaml              # section 7.3
│   ├── evidence.yaml            # sections 5.4 and 6.2
│   ├── conflicts.yaml           # section 6.3
│   └── messages.yaml            # section 11.4 (final text, doctor-approved)
├── engine/                      # Python: load, validate, apply, return section 8.2
├── tests/                       # section 14
└── docs/
    ├── genetic_risk_module_spec.md
    └── rule_review_signoff.md   # section 13
```

### 12.2 `config.yaml` settings

| Setting | Type | Default | Tag |
|---|---|---|---|
| `rules_version` | text | `1.0.0` | — |
| `show_result_before_review` | boolean | `true` | `[CONFIGURABLE]` |

### 12.3 Database table `genetic_assessments` (replaces the DRD v2 version)

| Column | Type | Notes |
|---|---|---|
| `id` | uuid, PK | |
| `patient_id` | uuid, FK → `patients.id` | |
| `submitted_by` | uuid, FK → `users.id` | Patient, or doctor for a correction |
| `inputs` | jsonb | All section 5 answers as submitted |
| `results` | jsonb | Section 8.2 structure |
| `rules_version` | text | From `config.yaml` at run time |
| `show_numbers_to_patient` | boolean | Setting value at creation |
| `risk_indicated` | boolean | Copy of the flag, for sorting |
| `priority` | text | `normal` / `high` |
| `review_status` | text | `pending_review` / `reviewed` |
| `reviewed_by` | uuid, nullable, FK → `doctors.id` | |
| `reviewed_at` | timestamptz, nullable | |
| `doctor_note` | text, nullable | |
| `supersedes_id` | uuid, nullable, FK → `genetic_assessments.id` | Set when a doctor corrects inputs |
| `created_at` | timestamptz | |

Append-only: rows are never deleted. Only the review columns are updated, once. Row-Level Security deny-by-default is added in Phase 8 (DEC-022). **Do not create a `genetic_conditions` table.**

### 12.4 API endpoints (proposed)
`[OPEN]` Names to be aligned with the project-wide route design.

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/genetic/assessments` | patient | Submit inputs, run engine, save |
| GET | `/genetic/assessments/{id}` | patient (own) / doctor (assigned) | One assessment |
| GET | `/patients/{patient_id}/genetic/assessments` | patient (own) / doctor (assigned) | History |
| GET | `/genetic/review-queue` | doctor | Section 10.1 |
| POST | `/genetic/assessments/{id}/review` | doctor | Confirm with a note |
| POST | `/genetic/assessments/{id}/correct` | doctor | Corrected inputs → new assessment |

---

## 13. Rule review (before release)

1. A doctor using the platform checks every rule row in section 7, every evidence rule in section 6.2, every conflict in section 6.3, and every final message text against the listed sources.
2. They record each item in `docs/rule_review_signoff.md`: rule ID, checked (yes/no), comment, reviewer name, date, rules version.
3. The module is not released until every row is checked "yes".
4. Any change to a rule file → raise `rules_version` → re-review the changed rows.

### 13.1 Assumptions to confirm at rule review

| ID | Assumption |
|---|---|
| A1 | A "normal" sickle cell status card does not rule out β-thalassaemia carrier status, so it is treated as `unknown` for the haemoglobin group. |
| A2 | HbE or HbD carrier × tested-negative partner: no affected child expected; 1 in 2 carrier. |
| A3 | Haemophilia A and B follow the same rules in this module. |
| A4 | β-thalassaemia major or sickle cell disease parent × tested-negative partner: all children are carriers, no affected child expected. |

---

## 14. Tests (all must pass before release)

1. One test per unordered pair in section 7.1 (45 tests), checking rule ID, status and outcomes.
2. One test per row in section 7.2 (including both "if boy" and "if girl" outputs) and section 7.3.
3. One test per evidence rule (section 6.2) and per conflict/error code (section 6.3).
4. Priority order (section 6.4), with at least one case per level.
5. Entry question `no` → `not_assessed`.
6. Consanguinity `yes` / `not_sure` → flag and message, numbers unchanged.
7. Timing prompt and `priority = high` exactly when `risk_indicated` (section 9.4).
8. `show_result_before_review` `true` and `false` both behave as specified.
9. No output ever contains `percent: 0` or a field for the baby's sex.
10. Doctor correction creates a new row with `supersedes_id` and leaves the old row unchanged.

---

## 15. Out of scope (version 1)
- Alpha-thalassaemia, HbC and any condition not listed in D2.
- Distinguishing β⁺ from β⁰ thalassaemia, or haemophilia A from B.
- Predicting severity.
- Residual risk after a negative test, population carrier frequencies, numeric consanguinity risk.
- Reading uploaded genetic reports (OCR).
- Any ML model.

## 16. Do not
- Do not hard-code `show_result_before_review`.
- Do not show 0%.
- Do not add conditions, statuses, input values or messages that are not in this document.
- Do not let doctors enter percentages.
- Do not edit or delete saved assessments (only the review columns are filled in, once).
- Do not create a `genetic_conditions` table.
- Do not show haemophilia results for only one sex.
- Do not release before the rule review sign-off (section 13).

## 17. Open items

| Item | Tag |
|---|---|
| Final text for every message key, approved by a doctor | `[OPEN]` |
| Rule review sign-off, including assumptions A1–A4 | `[OPEN]` |
| API route names aligned with the project-wide route design | `[OPEN]` |
| Screen designs (forms, result page, review queue) | `[OPEN]` |

## 18. Changes from `genetic_module_build_plan.md` v1

| Topic | Build plan v1 | This spec |
|---|---|---|
| β-thal and sickle cell | Two separate recessive conditions; mixed variants = counselling flag | One haemoglobin group table; β-thal × sickle calculated (HBB-12) |
| Dominant condition | Marfan, final choice open | Marfan, final |
| Evidence values | `test_report`, `doctor_told`, `family_history_only` | Adds `hplc_report`, `sickle_status_card`, `blood_count_only` (weak) |
| Conflict status name | `pending_review` | `conflict` (`pending_review` is now only a review status) |
| Sex input | Parent sex field | Removed; implied by mother/father forms |
| Haemophilia / Marfan | Always asked | Entry question first; `no` → `not_assessed` |
| Consanguinity | Later | Version 1, flag only |
| Patient sees result before review | Open | Yes, configurable |
| Rule storage | Files (DRD said database) | Files only, rules version stored per assessment |

---

## Sources

| ID | Source |
|---|---|
| S1 | St. Jude Children's Research Hospital, "What is beta thalassemia trait?" (reviewed Nov 2023). https://www.stjude.org/treatment/disease/sickle-cell-disease/diagnosing-sickle-cell/beta-thalassemia-trait.html |
| S2 | GeneReviews, "Sickle Cell Disease" (NCBI Bookshelf NBK1377). https://www.ncbi.nlm.nih.gov/books/NBK1377/ |
| S3 | Haemophilia Foundation Australia, "Haemophilia inheritance". https://www.haemophilia.org.au/bleeding-disorders/haemophilia/haemophilia-inheritance/ ; NHS Genomics Education Programme, "Haemophilia A". https://www.genomicseducation.hee.nhs.uk/documents/haemophilia-a/ |
| S4 | NHS Genomics Education Programme, "Marfan syndrome". https://www.genomicseducation.hee.nhs.uk/documents/marfan-syndrome |
| S5 | Ministry of Health, National Sickle Cell Anaemia Elimination Mission (genetic status cards: normal / carrier / affected). Reported in Rajya Sabha answer, March 2026 (ThePrint/PTI). https://theprint.in/india/over-6-97-cr-screenings-for-sickle-cell-anaemia-held-across-tribal-belts-nationwide-rajya-sabha-told/2887569 |
| S6 | MoHFW, Draft Policy for Prevention and Control of Hemoglobinopathies (2018). https://main.mohfw.gov.in/sites/default/files/drft%20policy.pdf |
| S7 | FOGSI, Good Clinical Practice Recommendations for Universal Antenatal Thalassemia Screening (2025). https://www.fogsi.org/wp-content/uploads/2025/08/FOGSI-GCPR_Thalassemia_2025.pdf |
| S8 | NFHS-5 (2019–21), consanguineous marriage by state, via Dataful. https://insights.dataful.in/maps/prevalence-of-consanguineous-marriages-in-india-nfhs-5-2019-21 |
| S9 | Asian Journal of Transfusion Science (2020), MCV/MCH not reliable predictors of β-thalassaemia carrier status. https://doaj.org/article/c6e61403394441f09ce6a08c3fd76057 |
| S10 | Li et al., Prenatal diagnosis of β-thalassemia in Southern China, Eur J Obstet Gynecol Reprod Biol (2006) (CVS 11–13 weeks; amniocentesis 15–17 weeks). |
| S11 | Pre-Conception and Pre-Natal Diagnostic Techniques (Prohibition of Sex Selection) Act, 1994 (India). Summary: https://ruralindiaonline.org/gu/library/resource/pre-conception-pre-natal-diagnostic-techniques-act-1994/ |

> **Disclaimer:** this module gives preliminary educational estimates only. It is not a diagnosis or a substitute for clinical genetic testing or counselling.

# Alovia: Genetic Risk Assessment Module — Build Plan

**Version:** 1 | **Date:** 2026-10-25 | **Module:** 3 (rule-based, no ML)
**Purpose:** a short guide that anyone can follow to build the module in order. It describes the structure and the decisions. The detailed rules live in separate data files (see section 4), not here.

---

## 1. What the module does

Takes what each parent has been told about their genetic status for a few well-known conditions, applies fixed inheritance rules, and shows the chance that a child is affected or a carrier. It is an educational estimate, not a diagnosis.

**Safety principle:** a rule only produces a number when the information is confirmed and consistent. If anything is unknown, conflicting or unsupported, the engine shows **no number** and routes the case to counselling or doctor review. A missing number is always safer than a wrongly high or low one.

---

## 2. Decisions already made

| Topic | Decision |
|---|---|
| Conditions | Well-known, pattern-based: β-thalassaemia, sickle cell disease (recessive); haemophilia (X-linked recessive); one dominant condition, e.g. Marfan syndrome (final choice open) |
| Who enters data | Patient enters, doctor reviews |
| Parent status values | `affected`, `carrier`, `tested_negative`, `unknown` |
| Unknown status | Result: "needs testing or counselling", no number |
| Conflicting answers | No number; case goes to doctor review; patient is told (see section 6) |
| Rule storage | Separate data files (JSON/YAML) read by a small engine |
| Consent | One application-wide consent covers mother, father and patient |
| Consanguinity | Later, not in version 1 |
| Result wording | "This is for knowledge only and is not medical advice. Counselling is recommended." |
| Builder | One person (Raheem) |

---

## 3. Project structure

```
genetic_module/
├── rules/                    # data files, one per pattern + shared files
│   ├── patterns/             # recessive, x_linked_recessive, dominant
│   ├── conditions/           # one file per condition (uses a pattern)
│   ├── conflicts.yaml        # conflict and error rules
│   └── messages.yaml         # all patient/doctor-facing wording
├── engine/                   # small Python code that reads the rules
├── tests/                    # test cases (one per rule row, one per conflict)
└── docs/                     # this plan, rule sources, reviewer notes
```

---

## 4. Build order

Work in this order. Each phase has a clear "done when" so progress is easy to check.

| # | Phase | What to produce | Done when |
|---|---|---|---|
| 1 | **Input vocabulary** | The fixed lists: conditions, status values, "how do you know" values (`test_report`, `doctor_told`, `family_history_only`), sex, extra flags (mixed variant, other haemoglobin type) | Every form answer maps to a defined value |
| 2 | **Pattern rule tables** | One table per pattern: parent status combination → outcome percentages (or a counselling flag) | Each table covers every combination, with no gaps |
| 3 | **Condition files** | One file per condition: name, pattern used, wording of status options, help text, special flags | Each condition points to a pattern and its extras |
| 4 | **Conflict and error rules** | `conflicts.yaml`: what counts as a conflict or error, and the outcome for each (section 6) | Every conflict type has a defined outcome and message |
| 5 | **Source check** | Each rule checked against a genetics reference; reviewer notes saved in `docs/` | A reviewer has confirmed every rule row |
| 6 | **Engine** | Python code that loads the rule files, checks inputs, applies rules, returns a structured result | Engine returns the right result for every test |
| 7 | **Tests** | One test per rule row and per conflict type | All tests pass |
| 8 | **API and database** | Endpoints to submit parental data, get a result and a review status; tables from the DRD | Result and review status are stored |
| 9 | **Frontend** | Parent forms, results page, "sent for review" screen, disclaimer | Patient can complete the flow end to end |
| 10 | **Doctor review screen** | List of cases awaiting review, ability to confirm, correct or add counselling notes | Doctor action updates the patient's view |

Phases 1 to 7 need no database or frontend. Finish them first and the rest is mostly wiring.

---

## 5. Rule table structure (overview only)

Each pattern table maps **mother status + father status → outcome**. Full tables go in `rules/patterns/`.

| Pattern | Conditions | What the table needs | Key notes |
|---|---|---|---|
| Recessive | β-thalassaemia, sickle cell | Both parents' status | Carrier plus carrier gives 25% affected, 50% carrier, 25% neither. Unknown for either parent means "needs testing or counselling". Mixed variants mean counselling flag. |
| X-linked recessive | Haemophilia | Each parent's status and sex | Output is split into sons and daughters. Fathers are only `affected` or `not_affected`. Affected father plus carrier mother means counselling flag. |
| Dominant | Marfan (or similar) | Whether each parent is affected | An affected parent gives 50% for each child. Two unaffected parents mean "no inherited risk expected", not 0%. Two affected parents mean counselling flag. |

Each rule row also stores the **source** it was checked against.

---

## 6. Conflict and error handling

### 6.1 Outcome levels (highest priority first)

When more than one applies, the highest one wins.

| Priority | Outcome | Number shown? | Goes to |
|---|---|---|---|
| 1 | **Error** (engine or data problem) | No | Doctor review, logged |
| 2 | **Conflict** (answers contradict) | No | Doctor review |
| 3 | **Counselling flag** (outside what the rules support) | No | Counselling message |
| 4 | **Needs testing or counselling** (status unknown) | No | Testing/counselling message |
| 5 | **Calculated** | Yes | Normal result |

### 6.2 Conflict and error types (starting list)

| Type | Example | Outcome |
|---|---|---|
| Contradictory answers | "Tested negative" but a child already has the recessive condition | Conflict |
| Weak evidence | Status given, but basis is "family history only" | Treated as `unknown` |
| Impossible entry | A man marked as a haemophilia carrier | Conflict |
| Unsupported combination | Mixed haemoglobin variants; two affected dominant parents; affected father with carrier mother (X-linked) | Counselling flag |
| Missing required field | Sex missing for haemophilia | Error, ask the patient to complete it |
| Unknown condition or rule not found | Rule file missing or incomplete | Error |
| Any unexpected failure | Engine problem | Error, with a safe fallback message |

This list will grow while building. Add new types to `conflicts.yaml`, never as special cases in code.

### 6.3 What the patient sees

For a conflict or error, show no risk number. Show a message such as (final wording lives in `messages.yaml`):

> "Some of your answers need a doctor's review. We have sent them to your doctor, who will look at them and counsel you. Until then, no result is shown."

After the doctor reviews, the patient sees the doctor's outcome and counselling note.

### 6.4 Doctor review states

`pending_review` → `reviewed` (with a doctor note). The patient sees the matching status at each stage.

---

## 7. Result output (what the engine returns)

- `status`: `calculated` / `needs_testing_or_counselling` / `counselling_flag` / `pending_review` / `error`
- `outcomes`: percentages (only if `calculated`), split by sons and daughters where the pattern requires it
- `explanation`: short plain-language text
- `warnings`: list of reasons (missing, unknown or conflicting items)
- `disclaimer`: fixed wording from section 2

---

## 8. Testing approach

- One test per rule-table row (expected percentages).
- One test per conflict and error type (expected outcome and message).
- Edge cases: every `unknown` combination, mixed-variant couples, both-affected dominant, affected father with carrier mother.
- Rule review by a reviewer (a doctor or genetics-aware person) before the module is considered ready.

---

## 9. Open items

- Final dominant condition (Marfan or another).
- Exact wording for all messages, reviewed by a doctor.
- Reviewer for the rules and the test names listed on forms.
- Consanguinity, later.
- Whether patients see the result before the doctor reviews it.
- Consent screen wording (application-wide).

## 10. Out of scope (version 1)

Automated reading of genetic reports, a trained ML model, conditions beyond the starter list, population carrier frequencies, residual risk after a negative test, and consanguinity.

> **Disclaimer:** this module is for preliminary educational estimates only. It is not a diagnosis or a substitute for clinical genetic testing or counselling.

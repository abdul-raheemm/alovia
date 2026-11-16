# Alovia — Modules 1 & 2: Fetal and Maternal Risk Prediction (ML) — Specification

**Version:** 1.0
**Date:** 2026-11-16
**Status:** Models trained, validated and served by a working FastAPI backend (old folder `ml-test`). In Phase 1 the prediction code and model files move into the new backend **without changing model behaviour**.
**Detail source:** `docs/archive/context_v2.md` §2–4 (full training record).

---

## 0. Rules for anyone building from this document
1. **Do not retrain, re-tune or modify the models.** The saved files are final for v1.
2. **Do not change prediction logic.** Move it; keep its behaviour identical, including both SHAP bug fixes (§4).
3. Field lists and order always come from the saved `*_feature_order.json` files, never hard-coded.
4. Any change in a prediction output after the move is a bug. Stop and report it.

---

## 1. Module 1 — Fetal Risk Prediction

| Item | Value |
|---|---|
| Dataset | UCI Cardiotocography (id 193); 2,126 records, 10 exact duplicates removed → 2,116 |
| Inputs | 21 CTG features: `LB, AC.1, FM.1, UC.1, DL.1, DS.1, DP.1, ASTV, MSTV, ALTV, MLTV, Width, Min, Max, Nmax, Nzeros, Mode, Mean, Median, Variance, Tendency` (order from `fetal_risk_feature_order.json`) |
| Output | `Normal` / `Suspect` / `Pathological` + confidence + class probabilities + top SHAP factors |
| Model | Tuned XGBoost (class weighting via `sample_weight`) |
| Results | CV macro F1 0.922; test macro F1 0.916; Pathological recall 97% (34/35); zero Pathological predicted as Normal |
| Known limitation | Inputs are computerised CTG values (SisPorto-style); not universally available. How to address this is on hold. |

## 2. Module 2 — Maternal Risk Prediction

| Item | Value |
|---|---|
| Dataset | Hossain et al. (2026), cleaned to the paper's criteria → 6,058 rows |
| Inputs | 8: age, systolic BP, diastolic BP, body temperature (°F), heart rate (bpm), BMI (kg/m²), HbA1c (**mmol/mol**), fasting glucose (**mmol/L**) (order from `maternal_risk_feature_order.json`) |
| Output | `Low` / `Mid` / `High` + confidence + class probabilities + top SHAP factors |
| Model | Tuned XGBoost |
| Results | CV macro F1 0.9924; test macro F1 0.9909; zero High predicted as Low. The dataset is highly separable; scores are not expected real-world accuracy. |

## 3. Files (8, moved into `backend/ml_models/`)

```
fetal_risk_xgboost_model.joblib      maternal_risk_xgboost_model.joblib
fetal_risk_feature_order.json        maternal_risk_feature_order.json
fetal_risk_label_mapping.json        maternal_risk_label_mapping.json
fetal_risk_model_metadata.json       maternal_risk_model_metadata.json
```

New in Phase 5 (Dashboard spec §9.4): `fetal_risk_feature_ranges.json`, `maternal_risk_feature_ranges.json`, computed by a script from the cleaned training data, never typed by hand. `[OPEN]` the cleaned training data files must be located (see §6).

## 4. Prediction logic to preserve (from the old `ml-test/app`)

- A `RiskModel` class builds each model's Pydantic input schema from its `feature_order.json`.
- Both models and both SHAP `TreeExplainer`s load once at startup.
- SHAP output shape for one row is `(n_samples, n_features, n_classes)`; slice by the predicted class (bug #1 fix).
- Direction labels are relative to the predicted class: "supports '<class>' prediction" / "pushes away from '<class>' prediction" (bug #2 fix).
- `payload.model_dump()` (Pydantic 2).

## 5. Endpoints

Old endpoints (`/health`, `/schema/fetal`, `/schema/maternal`, `/predict/fetal`, `/predict/maternal`) are replaced by the routes in `docs/API.md` (predictions section). Predictions are run and saved through the doctor routes; patients never call prediction routes.

## 6. Regression tests (required in Phase 1)

After the move, re-run the real test cases from the training notebooks and compare **every confidence value and top SHAP factor** with the old backend's output:
- fetal Normal, Suspect, Pathological;
- maternal Low, Mid, High, plus the known documented misclassification case.

**Decision (2026-11-16):** the notebook test values are not available. Before moving any code, the agent runs the old `ml-test` backend locally (read-only, from a copy) on a set of inputs agreed with the owner — at least one per class for each model, taken from rows of the public datasets or the owner's synthetic cases — saves inputs and full outputs to `backend/tests/fixtures/ml_reference_outputs.json`, and the new backend must reproduce them exactly. The owner approves the input set first.

## 7. What changes for the doctor (Phase 5, Dashboard spec §9–10)
Unit switches (HbA1c %, glucose mg/dL, temperature °C), training-range warnings, model limitations, result sharing. None of these change the model itself.

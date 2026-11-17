"""Fetal and maternal risk models (Modules 1 & 2), moved from the old ml-test backend.

Prediction logic is unchanged (ml_models_spec.md §0, §4), including both SHAP fixes:
bug #1 slice SHAP values by the predicted class; bug #2 directions are relative to the
predicted class. Any change in an output is a bug: tests/unit/test_ml_regression.py compares
every case with the old backend's recorded outputs.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from pydantic import BaseModel, create_model

MODELS_DIR = Path(__file__).resolve().parents[3] / "ml_models"


class RiskModel:
    """Loads one model + its feature order / label mapping / metadata,
    and builds predictions + SHAP top-contributing-factors from them."""

    def __init__(self, prefix: str):
        self.model = joblib.load(MODELS_DIR / f"{prefix}_xgboost_model.joblib")
        self.feature_order: list[str] = json.loads(
            (MODELS_DIR / f"{prefix}_feature_order.json").read_text()
        )
        self.label_mapping: dict = json.loads(
            (MODELS_DIR / f"{prefix}_label_mapping.json").read_text()
        )
        metadata_path = MODELS_DIR / f"{prefix}_model_metadata.json"
        self.metadata: dict = (
            json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        )
        self.explainer = shap.TreeExplainer(self.model)

        self.index_to_label: dict[int, str] = self._build_index_to_label(self.label_mapping)

    @staticmethod
    def _build_index_to_label(mapping_json: dict) -> dict[int, str]:
        """label_mapping.json holds two dicts: one mapping the model's
        contiguous output index ("0","1","2",...) to an intermediate code,
        and one mapping that intermediate code to the final label string.
        This composes them regardless of which order they appear in, or
        what the intermediate code's type/name is."""
        index_map: dict | None = None
        code_map: dict | None = None
        for value in mapping_json.values():
            keys = list(value.keys())
            if all(str(i) in keys for i in range(len(keys))):
                index_map = value
            else:
                code_map = value

        if index_map is None or code_map is None:
            raise ValueError(f"Unrecognized label_mapping structure: {mapping_json}")

        return {
            int(idx_str): code_map.get(str(code), code_map.get(code, str(code)))
            for idx_str, code in index_map.items()
        }

    def input_schema(self, name: str) -> type[BaseModel]:
        fields = {f: (float, ...) for f in self.feature_order}
        return create_model(name, **fields)

    def predict(self, payload: dict, top_n: int = 3) -> dict:
        row = pd.DataFrame([[payload[f] for f in self.feature_order]], columns=self.feature_order)
        proba = self.model.predict_proba(row)[0]
        pred_idx = int(np.argmax(proba))
        pred_label = self.index_to_label.get(pred_idx, str(pred_idx))

        shap_values = self.explainer.shap_values(row)
        contributions = self._top_contributors(shap_values, pred_idx, top_n)

        return {
            "predicted_class": pred_label,
            "confidence": round(float(proba[pred_idx]), 4),
            "class_probabilities": {
                self.index_to_label.get(i, str(i)): round(float(p), 4) for i, p in enumerate(proba)
            },
            "top_contributing_factors": contributions,
        }

    def _top_contributors(self, shap_values, pred_idx: int, top_n: int) -> list[dict]:
        pred_label = self.index_to_label.get(pred_idx, str(pred_idx))

        # SHAP's return format for multiclass tree models varies by version:
        # (a) a single ndarray of shape (n_samples, n_features, n_classes) —
        #     the shape directly verified against X_test in the training notebook
        # (b) a list of n_classes ndarrays, each shape (n_samples, n_features)
        if isinstance(shap_values, list):
            class_shap = shap_values[pred_idx][0]
        else:
            arr = np.asarray(shap_values)
            if arr.ndim == 3:
                # (n_samples, n_features, n_classes) — confirmed shape
                class_shap = arr[0, :, pred_idx]
            else:
                # Binary-classification fallback: (n_samples, n_features)
                class_shap = arr[0]

        pairs = sorted(
            zip(self.feature_order, class_shap),  # noqa: B905  (unchanged from ml-test)
            key=lambda p: abs(p[1]),
            reverse=True,
        )
        return [
            {
                "feature": f,
                "impact": round(float(v), 4),
                "direction": (
                    f"supports '{pred_label}' prediction"
                    if v > 0
                    else f"pushes away from '{pred_label}' prediction"
                ),
            }
            for f, v in pairs[:top_n]
        ]


@dataclass(frozen=True)
class Models:
    fetal: RiskModel
    maternal: RiskModel


@lru_cache
def load_models() -> Models:
    """Both models and SHAP explainers, loaded once per process. A missing or broken model
    file raises here, so the backend refuses to start (ARCHITECTURE.md §12)."""
    return Models(fetal=RiskModel("fetal_risk"), maternal=RiskModel("maternal_risk"))

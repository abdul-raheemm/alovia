"""Training-range files for the doctor's prediction forms (Dashboard spec §9.4, DEC-076).

Reads the cleaned CSVs written by the training notebooks (backend/ml_training/*.ipynb; run
them with backend/ml_training/data/ as the working folder, next to CTG.xls and
Maternal_Risk.csv; that folder is git-ignored), rebuilds each notebook's exact training split
(test_size 0.2, stratified, random_state 42) and writes the minimum and maximum of every
model input in that training split:

  backend/ml_models/fetal_risk_feature_ranges.json
  backend/ml_models/maternal_risk_feature_ranges.json

Before writing, it proves the split is the one the models were trained on: the saved model
must reproduce the test macro F1 recorded in its metadata file. No range is typed by hand.

  python scripts/compute_feature_ranges.py
"""

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / "ml_training" / "data"
MODELS = BACKEND / "ml_models"


@dataclass(frozen=True)
class Source:
    model: str  # file prefix: fetal / maternal
    csv: str
    rows: int  # cleaned rows the notebook reports
    target: str
    # target values -> model classes, exactly as the notebook encodes them
    encode: dict[object, int]


SOURCES = (
    Source("fetal", "fetal_clean.csv", 2116, "NSP", {1: 0, 2: 1, 3: 2}),
    Source(
        "maternal",
        "maternal_clean.csv",
        6058,
        "Status",
        {"low risk": 0, "mid risk": 1, "high risk": 2},
    ),
)


def split(src: Source) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    features = json.loads((MODELS / f"{src.model}_risk_feature_order.json").read_text("utf-8"))
    df = pd.read_csv(DATA / src.csv)
    if len(df) != src.rows:
        raise SystemExit(f"{src.csv}: {len(df)} rows, the notebook trained on {src.rows}")
    # the fetal notebook stratifies on NSP as read (1.0/2.0/3.0), the maternal one on 0/1/2
    y = df[src.target] if src.model == "fetal" else df[src.target].map(src.encode)
    x_train, x_test, y_train, y_test = train_test_split(
        df[features], y, test_size=0.2, stratify=y, random_state=42
    )
    return x_train, x_test, y_train, y_test


def check_split(src: Source, x_test: pd.DataFrame, y_test: pd.Series) -> float:
    """The saved model must give the test macro F1 recorded in its metadata on this split."""
    model = joblib.load(MODELS / f"{src.model}_risk_xgboost_model.joblib")
    meta = json.loads((MODELS / f"{src.model}_risk_model_metadata.json").read_text("utf-8"))
    truth = y_test.map(src.encode) if src.model == "fetal" else y_test
    score = round(float(f1_score(truth, model.predict(x_test), average="macro")), 4)
    if score != meta["test_macro_f1"]:
        raise SystemExit(f"{src.model}: test F1 {score} != metadata {meta['test_macro_f1']}")
    return score


def ranges(src: Source, x_train: pd.DataFrame, score: float) -> dict[str, object]:
    return {
        "model": src.model,
        "basis": "training split of the cleaned data (test_size 0.2, stratified, random_state 42)",
        "source": f"backend/ml_training/{src.model}_model.ipynb -> {src.csv}",
        "training_rows": len(x_train),
        "checked_test_macro_f1": score,
        "features": {
            name: {"min": float(x_train[name].min()), "max": float(x_train[name].max())}
            for name in x_train.columns
        },
    }


def main() -> None:
    for src in SOURCES:
        x_train, x_test, _, y_test = split(src)
        score = check_split(src, x_test, y_test)
        out = MODELS / f"{src.model}_risk_feature_ranges.json"
        out.write_text(json.dumps(ranges(src, x_train, score), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out.name}: {len(x_train)} training rows, test F1 {score} matches")


if __name__ == "__main__":
    main()

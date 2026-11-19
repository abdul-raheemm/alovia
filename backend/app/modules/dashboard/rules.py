"""Loads and checks backend/rules/dashboard/*.yaml (Dashboard spec §23, §9.4-9.6, §10).

Checked at startup; a wrong file stops the backend (ARCHITECTURE.md §12).
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.rule_texts import Message

RULES_DIR = Path(__file__).resolve().parents[3] / "rules" / "dashboard"
ML_DIR = Path(__file__).resolve().parents[3] / "ml_models"
# model labels, as in backend/ml_models/*_label_mapping.json (a test cross-checks them)
CLASSES = {"fetal": ("Normal", "Suspect", "Pathological"), "maternal": ("Low", "Mid", "High")}
TEMPLATE_KEYS = {f"result_template_{m}_{c.lower()}" for m, cs in CLASSES.items() for c in cs}
REQUIRED_MESSAGES = TEMPLATE_KEYS | {
    "lim_decision_support",
    "lim_public_data",
    "lim_fetal_ctg",
    "lim_maternal_separable",
    "warn_outside_training_range",
    "note_hba1c_haemoglobin_variant",
}


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DefaultUnits(_Strict):
    """§9.3 units offered on each switch: the model unit and one other."""

    hba1c: Literal["%", "mmol/mol"]
    glucose: Literal["mg/dL", "mmol/L"]
    temperature: Literal["°F", "°C"]


UnitName = Literal["hba1c", "glucose", "temperature"]


class Conversion(_Strict):
    """§9.3 one unit switch: model = entered * multiply / divide + add (U2)."""

    feature: str
    model_unit: str
    other_unit: str
    multiply: float
    divide: float = Field(gt=0)
    add: float
    source: str = Field(min_length=1)

    def to_model(self, value: float, unit: str) -> float:
        return value if unit == self.model_unit else value * self.multiply / self.divide + self.add


class FormField(_Strict):
    feature: str
    label: str = Field(min_length=1)


class FormGroup(_Strict):
    label: str = Field(min_length=1)
    fields: tuple[FormField, ...] = Field(min_length=1)


class FormGroups(_Strict):
    fetal: tuple[FormGroup, ...] = Field(min_length=1)
    maternal: tuple[FormGroup, ...] = Field(min_length=1)


class DashboardSettings(_Strict):
    """§23 settings (all [CONFIGURABLE]) plus the §9.1 form sections and §9.3 conversions."""

    default_units: DefaultUnits
    unit_conversions: dict[UnitName, Conversion]
    form_groups: FormGroups
    fetal_trend_features: tuple[str, ...] = Field(min_length=1)
    invite_code_length: int = Field(ge=6)
    invite_code_days: int = Field(ge=1)
    record_formats: tuple[Literal["pdf", "jpg", "png"], ...] = Field(min_length=1)
    record_max_mb: int = Field(gt=0)
    signed_url_minutes: int = Field(gt=0)
    require_signoff: bool
    ai_summary_enabled: bool
    ai_share_draft_enabled: bool
    ai_genetic_draft_enabled: bool
    ai_note_flag_enabled: bool
    ai_summary_days: int = Field(gt=0)
    ai_timeout_seconds: int = Field(gt=0)
    llm_provider: str | None  # TODO(OPEN): spec §27
    llm_model: str | None


class DashboardRules(_Strict):
    settings: DashboardSettings
    messages: dict[str, Message]

    @model_validator(mode="after")
    def complete(self) -> DashboardRules:
        if set(self.messages) != REQUIRED_MESSAGES:
            raise ValueError("messages.yaml must hold exactly the dashboard keys (§9.4-9.6, §10)")
        s = self.settings
        order = {m: feature_order(m) for m in ("fetal", "maternal")}
        if not set(s.fetal_trend_features) <= set(order["fetal"]):
            raise ValueError("fetal_trend_features must name fetal model features")
        for model, groups in (("fetal", s.form_groups.fetal), ("maternal", s.form_groups.maternal)):
            listed = [f.feature for g in groups for f in g.fields]
            if sorted(listed) != sorted(order[model]):
                raise ValueError(f"form_groups.{model} must list every model input exactly once")
        if set(s.unit_conversions) != {"hba1c", "glucose", "temperature"}:
            raise ValueError("unit_conversions needs hba1c, glucose and temperature (§9.3)")
        for name, c in s.unit_conversions.items():
            if c.feature not in order["maternal"]:
                raise ValueError(f"unit_conversions.{name} must name a maternal model input")
            if getattr(s.default_units, name) not in (c.model_unit, c.other_unit):
                raise ValueError(f"default_units.{name} must be one of its two units")
        return self


def feature_order(model: str) -> list[str]:
    """The model's inputs in order (backend/ml_models/<model>_risk_feature_order.json)."""
    names: list[str] = json.loads(
        (ML_DIR / f"{model}_risk_feature_order.json").read_text(encoding="utf-8")
    )
    return names


def _yaml(directory: Path, name: str) -> dict[str, object]:
    data: dict[str, object] = yaml.safe_load((directory / name).read_text(encoding="utf-8"))
    return data


def parse_dashboard_rules(directory: Path = RULES_DIR) -> DashboardRules:
    return DashboardRules.model_validate(
        {
            "settings": _yaml(directory, "config.yaml"),
            "messages": _yaml(directory, "messages.yaml")["messages"],
        }
    )


@lru_cache
def load_dashboard_rules() -> DashboardRules:
    return parse_dashboard_rules()


@lru_cache
def load_ranges() -> dict[str, dict[str, tuple[float, float]]]:
    """§9.4 training ranges per model: {feature: (min, max)}, from the files written by
    scripts/compute_feature_ranges.py. A missing or incomplete file stops the backend."""
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for model in ("fetal", "maternal"):
        data = json.loads((ML_DIR / f"{model}_risk_feature_ranges.json").read_text("utf-8"))
        ranges = {f: (float(r["min"]), float(r["max"])) for f, r in data["features"].items()}
        if list(ranges) != feature_order(model) or any(lo > hi for lo, hi in ranges.values()):
            raise ValueError(f"{model}_risk_feature_ranges.json does not match the model inputs")
        out[model] = ranges
    return out

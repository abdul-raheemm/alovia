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


class DashboardSettings(_Strict):
    """§23 settings (all [CONFIGURABLE])."""

    default_units: DefaultUnits
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
        fetal = json.loads((ML_DIR / "fetal_risk_feature_order.json").read_text(encoding="utf-8"))
        if not set(self.settings.fetal_trend_features) <= set(fetal):
            raise ValueError("fetal_trend_features must name fetal model features")
        return self


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

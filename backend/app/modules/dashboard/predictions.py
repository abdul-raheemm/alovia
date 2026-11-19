"""Doctor predictions: form schema, unit conversion, training-range warnings, predict and save,
history, sharing with the patient, trends; and the patient's shared results
(Dashboard spec §9-11, API.md §4.5-4.6). The models themselves are unchanged."""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.dashboard.rules import DashboardRules, feature_order
from app.modules.dashboard.schemas import (
    ConversionOut,
    FieldRange,
    ModelName,
    PatientResultOut,
    PredictionIn,
    PredictionSchema,
    ResultOut,
    SchemaField,
    SchemaGroup,
    ShareIn,
    ShareOut,
    TrendPoint,
    TrendsOut,
    UnitSwitch,
)
from app.modules.genetic import service as genetic
from app.modules.journey.engine import gestational_age_days
from app.modules.predictions import service as predictions
from app.modules.predictions.risk_model import Models
from app.modules.users.models import Doctor, Patient
from app.modules.users.service import DoctorAccount, add_audit, assigned_patient

Ranges = dict[str, dict[str, tuple[float, float]]]
LIMITATIONS: dict[str, list[str]] = {  # §9.6
    "fetal": ["lim_decision_support", "lim_public_data", "lim_fetal_ctg"],
    "maternal": ["lim_decision_support", "lim_public_data", "lim_maternal_separable"],
}
# §9.5: the note shows unless the mother's haemoglobin-group status is one of these
HB_NOTE_EXEMPT = {"tested_negative", "unknown"}


def schema(model: ModelName, rules: DashboardRules, ranges: Ranges) -> PredictionSchema:
    s = rules.settings
    switch = {c.feature: (name, c) for name, c in s.unit_conversions.items()}
    groups = s.form_groups.fetal if model == "fetal" else s.form_groups.maternal

    def unit(feature: str) -> UnitSwitch | None:
        if feature not in switch:
            return None
        name, c = switch[feature]
        default = getattr(s.default_units, name)
        return UnitSwitch(
            name=name, model_unit=c.model_unit, other_unit=c.other_unit, default=default
        )

    return PredictionSchema(
        model=model,
        groups=[
            SchemaGroup(
                label=g.label,
                fields=[
                    SchemaField(
                        feature=f.feature,
                        label=f.label,
                        range=FieldRange(
                            min=ranges[model][f.feature][0], max=ranges[model][f.feature][1]
                        ),
                        unit=unit(f.feature),
                    )
                    for f in g.fields
                ],
            )
            for g in groups
        ],
        limitation_keys=LIMITATIONS[model],
        messages={k: m.text for k, m in rules.messages.items()},
        conversions={
            name: ConversionOut(multiply=c.multiply, divide=c.divide, add=c.add)
            for name, c in s.unit_conversions.items()
        },
    )


def hba1c_note(db: Session, patient_id: uuid.UUID) -> bool:
    status = genetic.mother_haemoglobin_status(db, patient_id)
    return status is not None and status not in HB_NOTE_EXEMPT


def _convert(
    model: ModelName, body: PredictionIn, rules: DashboardRules
) -> tuple[dict[str, float], dict[str, Any]]:
    """§9.2 steps 1-2: every input present, units valid, values converted to model units."""
    order = feature_order(model)
    errors = {f"values.{f}": "required" for f in order if f not in body.values}
    errors |= {f"values.{f}": "not a model input" for f in body.values if f not in order}
    switches = {
        name: c for name, c in rules.settings.unit_conversions.items() if c.feature in order
    }
    for name, c in switches.items():
        if body.units.get(name) not in (c.model_unit, c.other_unit):
            errors[f"units.{name}"] = f"use {c.model_unit} or {c.other_unit}"
    errors |= {f"units.{n}": "no unit switch here" for n in body.units if n not in switches}
    if errors:
        raise AppError("VALIDATION_ERROR", "Please check the values.", fields=errors)
    by_feature = {c.feature: (name, c) for name, c in switches.items()}
    model_values: dict[str, float] = {}
    entered: dict[str, Any] = {}
    for f in order:
        value = body.values[f]
        if f in by_feature:
            name, c = by_feature[f]
            unit = body.units[name]
            model_values[f] = c.to_model(value, unit)
            entered[f] = {"value": value, "unit": unit}
        else:
            model_values[f] = value
            entered[f] = {"value": value, "unit": None}
    return model_values, entered


def _names(db: Session, doctor_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not doctor_ids:
        return {}
    rows = db.execute(select(Doctor.id, Doctor.name).where(Doctor.id.in_(doctor_ids)))
    return {doctor_id: name for doctor_id, name in rows}


def _outs(
    db: Session, model: ModelName, rows: list[predictions.Result], note: bool
) -> list[ResultOut]:
    shares = predictions.shares_for(db, model, [r.id for r in rows])
    ids = {r.entered_by for r in rows if r.entered_by} | {s.shared_by for s in shares.values()}
    names = _names(db, ids)
    out = []
    for r in rows:
        share = shares.get(r.id)
        out.append(
            ResultOut(
                id=r.id,
                model=model,
                created_at=r.created_at,
                predicted_class=r.predicted_class,
                confidence=r.confidence,
                class_probabilities=r.class_probabilities,
                top_contributing_factors=r.top_contributing_factors,
                input_values=r.input_values,
                entered_values=r.entered_values,
                range_warnings=r.range_warnings or [],
                model_version=r.model_version,
                entered_by_name=names.get(r.entered_by) if r.entered_by else None,
                hba1c_note=model == "maternal" and note,
                share=ShareOut(
                    shared_at=share.created_at,
                    shared_by_name=names.get(share.shared_by),
                    template_key=share.template_key,
                    doctor_message=share.doctor_message,
                )
                if share
                else None,
            )
        )
    return out


def run(
    db: Session,
    account: DoctorAccount,
    patient: Patient,
    model: ModelName,
    body: PredictionIn,
    rules: DashboardRules,
    ranges: Ranges,
    models: Models,
) -> ResultOut:
    """§9.2: validate, convert, check ranges (the prediction still runs), predict, save."""
    model_values, entered = _convert(model, body, rules)
    warnings = [
        f for f, v in model_values.items() if not ranges[model][f][0] <= v <= ranges[model][f][1]
    ]
    row = predictions.predict_and_save(
        db, models, model, patient.id, account.doctor.id, model_values, entered, warnings
    )
    add_audit(db, account.user, "prediction run", f"{model}_result", row.id, patient.id)
    db.commit()
    db.refresh(row)
    return _outs(db, model, [row], hba1c_note(db, patient.id))[0]


def history(db: Session, patient: Patient, model: ModelName) -> list[ResultOut]:
    rows = predictions.results(db, patient.id, model)
    return _outs(db, model, rows, hba1c_note(db, patient.id))


def share(
    db: Session, account: DoctorAccount, model: ModelName, result_id: uuid.UUID, body: ShareIn
) -> ResultOut:
    """§10: one share per result, with the class template and an optional message."""
    row = predictions.get_result(db, model, result_id)
    if row is None:
        raise AppError("NOT_FOUND", "Result not found.", status=404)
    patient = assigned_patient(db, account.doctor.id, row.patient_id)  # 404 if not assigned
    message = (body.doctor_message or "").strip() or None
    template = f"result_template_{model}_{row.predicted_class.lower()}"
    predictions.add_share(db, model, row.id, account.doctor.id, template, message)
    add_audit(db, account.user, "result shared", f"{model}_result", row.id, patient.id)
    db.commit()
    return _outs(db, model, [row], hba1c_note(db, patient.id))[0]


def trends(db: Session, patient: Patient, fetal_features: tuple[str, ...]) -> TrendsOut:
    """§11: every maternal input and the configured fetal inputs, oldest first."""

    def week(day: date) -> int | None:
        if patient.due_date is None:
            return None
        days = gestational_age_days(patient.due_date, day)
        return days // 7 if 0 <= days <= 42 * 7 else None

    def points(model: ModelName, features: list[str]) -> list[TrendPoint]:
        return [
            TrendPoint(
                result_id=r.id,
                created_at=r.created_at,
                ga_week=week(r.created_at.date()),
                predicted_class=r.predicted_class,
                values={f: r.input_values[f] for f in features},
            )
            for r in reversed(predictions.results(db, patient.id, model))
        ]

    maternal_features = feature_order("maternal")
    return TrendsOut(
        maternal_features=maternal_features,
        fetal_features=list(fetal_features),
        maternal=points("maternal", maternal_features),
        fetal=points("fetal", list(fetal_features)),
    )


def patient_results(db: Session, patient: Patient, rules: DashboardRules) -> list[PatientResultOut]:
    """§10 step 4: shared results only; template text and doctor message, nothing else."""
    shared = predictions.shared_results(db, patient.id)
    names = _names(db, {s.shared_by for s in shared})
    return [
        PatientResultOut(
            id=s.share_id,
            result_type=s.result_type,
            result_date=s.result_date,
            shared_at=s.shared_at,
            template_key=s.template_key,
            template_text=rules.messages[s.template_key].text,
            doctor_message=s.doctor_message,
            doctor_name=names.get(s.shared_by),
        )
        for s in shared
    ]

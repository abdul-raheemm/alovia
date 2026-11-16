# Module Specifications

One specification per module. Each spec is the source of truth for **its own module's rules, flows and wording**.

| # | Module | Spec | Build phase |
|---|---|---|---|
| 1 | Fetal Risk Prediction (ML) | `ml_models_spec.md` | Built; moved into the new backend in Phase 1 |
| 2 | Maternal Risk Prediction (ML) | `ml_models_spec.md` | Built; moved into the new backend in Phase 1 |
| 3 | Genetic Risk Assessment | `genetic_risk_module_spec.md` | Phase 4 |
| 4 | Pregnancy Journey (patient home) | `pregnancy_journey_module_spec.md` | Phase 2 |
| 5 | Pregnancy Knowledge Assistant (RAG) | `rag_assistant_module_spec.md` | Phase 7 (last module) |
| 6 | Doctor Dashboard + minimal Admin | `doctor_dashboard_module_spec.md` | Phase 5 |
| 7 | Symptom Tracking | `symptom_tracking_module_spec.md` | Phase 3 |

## How these specs relate to the project-wide documents

The specs were written before the project-wide documents were consolidated, so they still mention older documents. Read them with this mapping:

| Spec says | Now means |
|---|---|
| PRD v2 | `docs/PRD.md` |
| TRD v2 | `docs/ARCHITECTURE.md` (and `docs/SECURITY.md` for TRD §5) |
| DRD v2 | `docs/DATABASE.md` |
| `context_v2.md` | `docs/tracking/CONTEXT.md` and `docs/modules/ml_models_spec.md` |
| "API endpoints (proposed)" sections | `docs/API.md` holds the agreed routes |
| "Repository layout" sections (`genetic_module/`, `symptom_module/`, `journey_module/`) | Logical groupings only. Real paths follow `docs/ARCHITECTURE.md` §7: code in `backend/app/modules/<module>/`, YAML in `backend/rules/<module>/`, content in `backend/content/`, tests in `backend/tests/`, sign-off and review docs in `docs/modules/reviews/` |
| `genetic_conditions` table / DRD v2 `symptom_logs` / `journey_content` definitions | Replaced by `docs/DATABASE.md` §3 |

## Which document wins

| Topic | Source of truth |
|---|---|
| A module's rules, flows, wording, thresholds | That module's spec |
| Table and column definitions | `docs/DATABASE.md` |
| Route names and request/response shapes | `docs/API.md` |
| Look and feel | `docs/DESIGN_SYSTEM.md` |
| Security | `docs/SECURITY.md` |

If two documents disagree, **do not pick one**. Stop, describe the conflict, and ask the owner. Record the answer in `docs/DECISIONS.md` and fix the losing document.

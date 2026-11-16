# Roadmap — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
Each phase ends with: all checks pass, owner review, `CHANGELOG.md` entry, `PROGRESS.md` updated. Detailed task checkboxes live in `tracking/PROGRESS.md`.

## NOW

### Phase 0 — Documentation ✅ (this document set)

### Phase 1 — Foundation
- Fresh repo, folder structure, `.gitignore`, `.env.example` files, `scripts/check_all`.
- Copy the knowledge-base collection from the old `rag/` into `knowledge-base/` (collection only; the RAG module stays Phase 7).
- Backend skeleton: config, logging, error envelope, auth dependency, `/health`, `/me`.
- **Owner action:** create fresh Supabase project and provide values.
- Alembic + Phase 1 migration (identity tables, result tables). No RLS until Phase 8 (DEC-022).
- Move ML prediction code + 8 model files; record reference outputs from the old backend first; regression tests identical.
- Frontend workspace: two apps + `packages/ui` (tokens, themes, fonts, shadcn base) + `packages/shared` (API client); sign-in/sign-up with consent and 18+ checkbox; legal pages; app shells with nav; theme switch; PWA manifest for the patient app.
- Seed script with synthetic data.
- Optional: GitHub Actions running all checks (`[OPEN]`, after the GitHub repo exists).

### Phase 2 — Pregnancy Journey (Module 4)
Dates/onboarding, GA, months, home screen, month cards, size comparison (prototype YAML), calendar, appointments (patient side), notifications, doctor notes (read side), pregnancy-end flow, prototype content with banner, openly licensed illustrations or placeholders.

## NEXT

### Phase 3 — Symptom Tracking (Module 7)
Vocabulary, logging, urgent button, red-flag engine, PUQE, pattern rules, inbox items, charts, calendar dots, weekly summary.

### Phase 4 — Genetic Risk (Module 3)
YAML rules, engine, all tests (45 pairs + haemophilia + Marfan + conflicts), patient forms and results, assessment storage.

### Phase 5 — Doctor Dashboard + Admin (Module 6; Modules 1–2 doctor side)
Patient list, inbox, patient tabs, CTG/vitals forms with units and range warnings, sharing, trends, genetic review, symptom view, records, notes, appointments (doctor side), dates/status, rule review screen, audit log, admin screens, invite codes.

## LATER

### Phase 6 — AI draft features
Choose LLM `[OPEN]`; AI-1…AI-4 behind flags.

### Phase 7 — Knowledge Assistant (Module 5)
When the knowledge base is complete: chunk + embed, retrieval, safety pipeline, evaluation set; switch Journey content provider to the knowledge base.

### Phase 8 — Security hardening and compliance
`SECURITY.md` §11 checklist, Row-Level Security on every table, deletion requests, rate limits, CORS, headers, policy review, legal pages final, compliance checklist with supervisor.

### Phase 9 — Deployment
`DEPLOYMENT.md`: Render + 2 Vercel projects, smoke tests, demo data.

## DEFERRED
Postpartum features; regional languages; push notifications; CTG input-availability approach (on hold); more genetic conditions and patterns; OCR for reports; patient access to medical records.

## NOT PLANNED (v1)
Combined risk score; diagnosis/treatment advice; baby-sex prediction; payments; analytics/ads; multi-clinic tenancy; native mobile apps.

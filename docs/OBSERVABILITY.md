# Observability — Alovia

**Version:** 1.0 · **Date:** 2026-11-16 · Prototype scale: keep it simple and free.

## 1. Logging
- Backend JSON logs to stdout (Render collects them). Each request gets a `request_id`, returned in the `X-Request-ID` header.
- **Log:** request method/path/status/duration (no bodies on patient routes), sign-ins, permission denials, rule-engine failures, external API failures and latency, admin actions, startup checks (models, rules loaded).
- **Never log:** passwords, tokens, keys, symptom notes, chat text, genetic inputs, clinical values, file contents (`SECURITY.md` §9).

## 2. Health
`GET /api/v1/health` → `{status, models_loaded, rules_loaded: {genetic, symptoms, journey}, db: ok|error, version}`.

## 3. Metrics (from logs, no extra service in v1)
Error rate, request latency (p50/p90), prediction latency, RAG latency (Phase 7), count of L1/L2 check-ins (counts only), AI fallback count.

## 4. Monitoring and alerts
- Render dashboard + Supabase dashboard (database size vs 500 MB limit; project pause warnings).
- Optional free uptime ping on `/health` `[OPEN]` (note: pinging keeps the free service awake, which may conflict with free-tier fair use; decide at deployment).

## 5. Business events (audit, not analytics)
Stored in `audit_log` (Dashboard spec §20). No third-party analytics in v1 (see `legal/COMPLIANCE_CHECKLIST.md`).

# Error Handling (how the app behaves when things fail) — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
This document is about **the app's behaviour**. The agent's own log of build errors is `tracking/ERROR_LOG.md`.

## 1. API errors → what the user sees

| HTTP / code | Patient sees | Doctor sees |
|---|---|---|
| 400 `VALIDATION_ERROR` | Message next to each field | Same |
| 401 `AUTH_REQUIRED` | "Please sign in again." → sign-in page | Same |
| 403 `FORBIDDEN` | "You don't have access to this." | Same |
| 404 `NOT_FOUND` | "We couldn't find this." + back button | Same |
| 409 `CONFLICT` | Specific message (e.g. "This code has already been used.") | e.g. "Already reviewed by Dr X." |
| 413 / 415 | — | "File too large (max 10 MB)" / "Only PDF, JPG, PNG" |
| 429 `RATE_LIMITED` | "Too many attempts. Please wait a few minutes." | Same |
| 503 `SERVICE_UNAVAILABLE` | "We can't connect right now. Please try again." + Retry | Same |
| 500 `INTERNAL_ERROR` | "Something went wrong. Please try again." + Retry | Same + request ID |

## 2. Network, timeouts, cold starts
- Request timeout 20 s. First request after inactivity may take up to 60 s (Render free tier): show "Connecting…".
- Retries: GETs retry automatically twice with back-off; POST/PUT/DELETE never retry automatically (the user presses Retry; idempotency key prevents duplicates).
- Form input is kept in memory when a submit fails.

## 3. Safety-critical behaviour (never fails silently)
- **Urgent button and L1/L2 advice text are bundled in the patient app**, so the advice shows even if the backend is down. The check-in is queued in memory and sent when possible; the patient is told it was not saved yet.
- Symptom engine failure → check-in saved as L2 with `ERR` and `msg_safe_fallback` (Symptom spec §6 V3).
- Genetic engine failure → `error` status, no number, doctor review (Genetic spec §6.3 E3/E4).
- RAG / AI failure → fallback messages (RAG §8, Dashboard §18).
- Missing/invalid rule files or model files → backend refuses to start; `/health` reports which.

## 4. Empty and loading states
Defined in `UX_FLOWS.md` §0. Every data screen implements loading, empty, error and success.

## 5. Third-party failures

| Service | Behaviour |
|---|---|
| Supabase Auth down | Sign-in shows "Sign-in is temporarily unavailable." |
| Supabase Storage down | Upload/download error; no database row without a stored file |
| LLM/embedding API | Fallback; never blocks the workflow |

## 6. Backend rules
- One exception handler maps `AppError` and unexpected exceptions to the envelope.
- Unexpected exceptions: log with `request_id` and stack trace (server side only), return `INTERNAL_ERROR`.
- Database transactions: a request either fully succeeds or makes no change.

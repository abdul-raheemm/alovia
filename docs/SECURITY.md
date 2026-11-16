# Security — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
**Owner decision:** modules are built and tested first; **security hardening is the last build phase (Phase 8)**. Only the items in §0 are needed earlier, because the app cannot work or would leak data without them.

---

## 0. What applies from Phase 1 (minimum, not hardening)

| Item | Why it cannot wait |
|---|---|
| Sign-in with Supabase Auth; backend verifies the JWT on every request | The app must know who is a patient, doctor or admin |
| Role and assignment checks in the backend | Otherwise any user could see any patient's data |
| Secrets only in `.env` files that are git-ignored; `.env.example` with empty values | A leaked database password cannot be undone |
| Private Storage bucket | Medical files must never be public |
| Synthetic/test data only | No real patient data until Phase 8 is complete and a compliant setup exists |

Everything else below is **Phase 8** unless marked otherwise, **including Row-Level Security** (DEC-022).

> **Known risk accepted by the owner (DEC-022):** until Phase 8, tables have no Row-Level Security, so the public Supabase key used by the frontends could read tables through Supabase's automatic Data API. This is accepted because only synthetic/test data is used. **No real personal data may be entered before Phase 8.** If anything in development needs protection earlier, the agent asks the owner first.

---

## 1. Authentication
- **Provider:** Supabase Auth.
- **Methods:** email + password (patients and doctors). Doctors are invited by the admin (Supabase invite). Admin accounts are created by the owner in the Supabase console.
- **Backend verification:** one dependency (`app/core/auth.py`) verifies the token signature and expiry using the project's JWT verification key, then loads `users.role`. A future move to a backend-issued JWT should only change this file.
- **Phase 8:** password rules (min length 8, Supabase settings), email confirmation required, session expiry review, sign-out everywhere on password change.

## 2. Authorization

| Role | Can |
|---|---|
| Patient | Own records only (journey, symptoms, genetic, appointments, shared results and notes, chat, deletion request) |
| Doctor | Assigned patients only (Dashboard spec §4) |
| Admin | Doctor accounts, assignments, activity log, deletion requests; **no clinical data** |

Enforced server-side in every route. The frontend only hides buttons; it is never the security boundary.

## 3. Secrets
- Never hard-code credentials; never commit `.env`; never put the service key or database URL in frontend code.
- The frontends only hold the Supabase **URL** and **public (anon/publishable) key**, which are designed to be public.
- Rotate any credential that was exposed (and record it in `tracking/ERROR_LOG.md`).
- Production secrets live in the Render and Vercel dashboards.

## 4. Environment Variables
See `ENVIRONMENT.md` for the full list. Public: Supabase URL, public key, API base URL. Private: database URL, service key, JWT verification settings, LLM/embedding keys.

## 5. API Security (Phase 8)
- **Input validation:** Pydantic on every route (from Phase 1); text length limits; upload checks (§8).
- **Rate limiting:** per user and per IP on sign-in-adjacent routes, invite-code use (max 5 attempts per 15 minutes), predictions, AI and assistant routes. `[CONFIGURABLE]`
- **CORS:** only the two frontend origins (dev: localhost ports; prod: the Vercel domains). No `*`.
- **Headers:** HTTPS only (Render/Vercel), HSTS, `X-Content-Type-Options`, frame denial, a Content Security Policy on the frontends.
- **Docs endpoint** `/docs` disabled in production.
- **Invite codes:** hashed, single use, expiring, same error for wrong/used/expired.

## 6. Data Protection
- **Sensitive data:** everything in patient tables (`DATABASE.md` §10), including the father's genetic findings and chat messages.
- **Data minimisation:** no phone numbers, addresses, government IDs or payment data. Age is optional. Names can be first names.
- **Encryption:** in transit (HTTPS) everywhere; at rest by Supabase (provider default).
- **LLM/embedding calls:** no names or IDs sent; real patient data only after a provider with acceptable privacy terms is chosen (`[OPEN]`).
- **Retention:** keep data while the account exists; deleted on request (§7). `[OPEN]` retention period for inactive accounts.

## 7. Data Deletion (Phase 8)
1. Patient: Settings → "Request deletion of my data" → confirmation screen listing what will be deleted.
2. A `deletion_requests` row is created; admins see it.
3. Admin executes: deletes the patient's rows in every patient table, her Storage files and her Auth user; `audit_log` keeps the action without clinical values.
4. Target: completed within `deletion_days` (default 30) `[CONFIGURABLE]` `[CONFIRM]` against DPDP Rules timelines.
5. The patient gets a confirmation (in-app before deletion; email by Supabase is optional `[OPEN]`).

## 8. File Uploads
- **Allowed:** PDF, JPG, PNG (`record_formats`). **Max:** 10 MB (`record_max_mb`).
- **Validation:** check extension **and** file signature (magic bytes); reject others with 415.
- **Storage:** private Supabase bucket, path `patients/{patient_id}/{uuid}.{ext}`; original filename stored separately.
- **Download:** signed URLs valid 5 minutes.

## 9. Logging
- **Never log:** passwords, tokens, API keys, full request bodies of patient routes, symptom notes, chat messages, genetic inputs, clinical values.
- **Log:** sign-in events, permission denials, errors (with request ID), admin actions, rule engine failures, external API failures.
See `OBSERVABILITY.md`.

## 10. Legal and Regulatory Flags (not legal advice; review with the supervisor)

| Area | Flag |
|---|---|
| India DPDP Act 2023 + DPDP Rules 2025 | Rules notified 14 Nov 2025 with a phased rollout to 14 May 2027; consent notices, children's data (verifiable parental consent) and breach duties come in the later phases. Alovia must have a clear consent notice, a contact for privacy questions, and a deletion route before real users. |
| Children's data | Under DPDP, a child is under 18. v1 accepts **18+ only** (DEC-023); minors would need verifiable parental consent. |
| CDSCO medical device software | CDSCO issued final guidance on medical device software (July 2026). Clinical decision-support software can count as a medical device. Alovia stays a **research prototype, not for clinical use**, with synthetic data only; any real deployment needs a regulatory check first. |
| PCPNDT Act | No feature may reveal or predict the baby's sex (genetic and RAG specs). |
| Content licences | NHS OGL conditions, Tier A/B rules (`docs/knowledge-base/knowledgebase.md`); illustrations, fonts and icons per `docs/legal/CREDITS.md`. |
| Hosting terms | Vercel Hobby is for non-commercial use: fine for the academic project; re-check before any commercial use. |

Checklist of the owner's 20 legal items: `docs/legal/COMPLIANCE_CHECKLIST.md`.

## 11. Security Checklist (Phase 8 sign-off)
- [ ] Authentication flows tested (sign-in, expiry, sign-out)
- [ ] Every route has role + assignment checks (automated test per route)
- [ ] Server-side validation on every input
- [ ] Secrets only in environment settings; repository scanned for secrets
- [ ] RLS enabled on every table; no permissive policies; Storage bucket private
- [ ] CORS restricted; security headers set; `/docs` off in production
- [ ] Rate limits on sensitive routes
- [ ] Upload validation (type, signature, size)
- [ ] Errors never expose internals
- [ ] Logs contain no sensitive data (sample review)
- [ ] Dependencies scanned (`pip-audit`, `npm audit`) and reviewed
- [ ] Deletion request flow works end to end
- [ ] Legal pages published and linked; consent recorded
- [ ] Compliance checklist reviewed with the supervisor

# Deployment — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
**Rule:** the agent never deploys, creates cloud projects, or changes cloud settings by itself. It prepares everything and gives the owner exact steps ("Action needed").

## 1. Environments

| Environment | Backend | Patient app | Doctor app | Database |
|---|---|---|---|---|
| Development | `localhost:8000` | `localhost:5173` | `localhost:5174` | Fresh Supabase project (dev) |
| Test | Local / CI | — | — | Local Postgres or separate test project `[CONFIRM]` |
| Production (demo) | Render free web service | Vercel Hobby project 1 | Vercel Hobby project 2 | Same Supabase project, or a second one before real users `[OPEN]` |

URLs are recorded here once created `[OPEN]`.

## 2. One-time setup (owner, guided by the agent)
1. Create the **fresh Supabase project** → give the agent the URL, keys and database URL through the `.env` files (never in chat history if avoidable).
2. Create the **GitHub repository** (new, empty) → agent adds the remote after approval.
3. Render: new Web Service from the repo, root `backend/`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Python 3.12, environment variables from `ENVIRONMENT.md`.
4. Vercel: two projects from the same repo, roots `frontend/apps/patient-web` and `frontend/apps/doctor-web`, framework Vite.
5. Supabase Auth: set site URLs/redirects to the two Vercel domains.

## 3. Deployment Process (each release)
1. All checks pass (`TESTING.md` §7).
2. Database migrations applied (owner approves; backup first via Supabase dashboard).
3. Push to `main` → Render and Vercel deploy automatically.
4. Smoke tests: `/health`, sign-in on both apps, one patient flow, one doctor flow.
5. Update `CHANGELOG.md` and `tracking/HISTORY.md`.

## 4. Rollback
- Frontends: Vercel "promote previous deployment".
- Backend: Render "rollback to previous deploy".
- Database: Alembic `downgrade` to the previous revision (tested before release); restore from backup for data problems.

## 5. Production Checklist
- [ ] Build succeeds for backend and both frontends
- [ ] Environment variables set in Render and Vercel
- [ ] Migrations applied; `/health` all green
- [ ] CORS set to the two production domains
- [ ] Supabase Auth redirect URLs set
- [ ] Legal pages reachable; prototype/medical disclaimer visible
- [ ] Smoke tests pass
- [ ] Phase 8 security checklist complete before any real user

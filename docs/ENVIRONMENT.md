# Environment Configuration — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
Each part has its own `.env.example` (committed, empty values) and `.env` (never committed). **When a value is needed, the agent stops and asks the owner** (see `CLAUDE.md` "Action needed").

## 1. Backend — `backend/.env` (all private)

| Variable | Purpose | Phase |
|---|---|---|
| `APP_ENV` | `development` / `test` / `production` | 1 |
| `DATABASE_URL` | Supabase Postgres connection string (owner provides; pooled vs direct checked at deploy) | 1 |
| `TEST_DATABASE_URL` | Connection string of the separate, empty `alovia-test` Supabase project, used only by the migration tests (never the main project) | 1 |
| `SUPABASE_URL` | Project URL | 1 |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side key (Storage, admin invites) | 1 |
| `SUPABASE_JWT_ISSUER` / `SUPABASE_JWKS_URL` | Token verification (the project uses JWT signing keys, so no JWT secret is needed) | 1 |
| `CORS_ORIGINS` | Comma-separated frontend origins | 1 |
| `STORAGE_BUCKET` | Private bucket name (`medical-records`) | 5 |
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` | AI drafts / RAG | 6–7 |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY` | RAG | 7 |
| `LOG_LEVEL` | `INFO` default | 1 |

## 2. Frontends — `frontend/apps/<app>/.env` (public values only)

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend URL (`http://localhost:8000/api/v1` in development) |
| `VITE_SUPABASE_URL` | Project URL (for sign-in) |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Public (anon/publishable) key — safe in the browser |
| `VITE_APP_ENV` | `development` / `production` |

Anything starting with `VITE_` ends up in the browser. **Never put a private value in a `VITE_` variable.**

## 3. Feature settings (not secrets)
Module settings live in YAML (`backend/rules/*/config.yaml`, `backend/content/`), as defined in each spec — not in `.env`.

## 4. Rules
- Never commit real secrets; `.env` is in `.gitignore` from the first commit.
- Keep development, test and production values separate.
- Document every new variable here **before** using it.
- Production values are set in the Render and Vercel dashboards by the owner.

# CLAUDE.md — Rules for the AI coding agent (Alovia)

You are building **Alovia**, a woman-centric pregnancy web app (patient app + doctor app + FastAPI backend). It is a health-related research prototype: mistakes can mislead real people later, so **correctness and honesty come before speed**.

The owner is **Raheem**. He reviews everything. A 3-person team may also work in this repo.

---

## 1. Source of truth (read before acting)

At the start of **every** session, read in this order:
1. This file.
2. `docs/tracking/CONTEXT.md` (current state).
3. `docs/tracking/PROGRESS.md` (what is next).
4. The last entry of `docs/tracking/HISTORY.md`.
5. The **Lessons** in `docs/tracking/ERROR_LOG.md`.
6. The documents for the current task: the module spec in `docs/modules/`, plus `PRD.md`, `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `DESIGN_SYSTEM.md`, `UX_FLOWS.md`, `SECURITY.md`, `CODE_STYLE.md`, `TESTING.md` as relevant.

Then summarise your understanding in a few lines and list any conflict or missing information **before** proposing work.

Which document wins on which topic: `docs/modules/README.md`. If documents disagree: **do not guess** — stop, describe the conflict, ask.

---

## 2. Non-negotiable rules

1. **Never invent requirements.** Build only what the documents say. No extra features, fields, tables, routes, screens, rules, messages or medical content.
2. **`[OPEN]` stays open.** Never turn an undecided item into a decision. Leave a clear placeholder (`TODO(OPEN): <item>`) and list it in your report.
3. **`[CONFIGURABLE]` stays configurable.** Put it in the config/YAML file the spec names. Never hard-code it.
4. **`[CONFIRM]` items** are proposals awaiting the owner. Ask before relying on them.
5. **Never write medical content from your own knowledge** — no symptom advice, fetal-development text, sizes, percentages, thresholds or helpline numbers. They come only from the specs, rule files, approved content files or official sources the owner provides.
6. **Ask permission** before (a) starting each task's implementation, (b) installing or upgrading any dependency, (c) creating, moving or deleting files outside the approved plan, (d) running any database migration or command against Supabase, (e) any network action other than package installs (deploys, pushes, API calls to cloud services), (f) changing any document's decisions, (g) touching `.env` files or secrets, (h) anything irreversible.
7. **Never touch the old folders** `ml-test\` and `rag\` (inside the repo root `C:\Users\Engineer\Desktop\Alovia`) except to **read** or **copy** from them (with permission). Never edit, move or delete them. They are git-ignored; never commit them and never run tools (formatters, linters, graphify, search-and-replace) over them.
8. **Never commit or display secrets.** `.env` files are git-ignored. Never put private values in `VITE_` variables.
9. **Never weaken, skip or delete a test** to make it pass. If a test seems wrong, stop and ask.
10. **Never claim something works without evidence.** Show the exact commands you ran and their results.
11. **Security hardening is Phase 8.** Before that, implement only `docs/SECURITY.md` §0. Do not add extra security layers early unless asked — but never introduce something insecure either (no secrets in code, no public buckets, no skipping auth checks).
12. **Build order is fixed** (`docs/ROADMAP.md`): Foundation → Journey → Symptoms → Genetic → Dashboard/Admin → AI drafts → RAG (last module) → Security → Deployment. Do not start a later phase early.

---

## 3. "Action needed" — when you need the owner

When you need something only the owner can do (create the Supabase project, paste a URL or key, create the GitHub repo, approve a migration, review a screen), **stop** and write exactly:

```
🔔 ACTION NEEDED (owner)
What: <one line>
Why: <one line>
Steps: 1. … 2. … 3. …
Where to put it: <file / dashboard>
I will wait. Reply "done" when finished.
```

Never ask the owner to paste secrets into chat if a file can be used instead; tell him which `.env` file and variable to fill.

---

## 4. How every task runs (plan → approve → build → check → review → record)

**1. Plan (no code yet).** Post a short plan:
- task and spec sections it implements (rule IDs);
- files to create/change;
- database / API changes (must already be in `DATABASE.md` / `API.md`);
- dependencies to add (ask);
- tests to write;
- risks, edge cases, open items;
- **Suggestions:** any improvement you think would make it better — **as suggestions only**. Do not implement them unless the owner approves.

**2. Wait for approval.**

**3. Build** the smallest correct change. Follow `CODE_STYLE.md`, `DESIGN_SYSTEM.md`, the architecture's dependency rules. Reuse before creating. Touch only files in the plan.

**4. Check (double-check everything).**
- Run the full relevant checks (`docs/TESTING.md` §7): tests, lint, format, types, build.
- Self-review the diff against the spec line by line: every rule ID implemented exactly, wording keys correct, nothing extra, no hard-coded configurable values, no secrets, loading/empty/error states, phone (375px) and laptop (1280px), light and dark.
- Re-read the relevant spec section once more and confirm each requirement in a checklist.

**5. Ask for review.** Report:
```
✅ READY FOR REVIEW — <task>
What changed: …
Files changed: …
Spec checklist: <rule IDs / requirements → done>
Checks: <command → result> (all of them)
How to see it yourself: <exact steps / URL>
Open items / TODO(OPEN): …
Suggestions (not implemented): …
Docs updated: …
```
Wait for the owner's approval. Fix anything he raises. **Commit only after approval** (`CODE_STYLE.md` §11).

**6. Record.** After approval, update:
- `docs/tracking/PROGRESS.md` (status, who, date),
- `docs/tracking/HISTORY.md` (one entry using its template — always include **Who**),
- `docs/tracking/ERROR_LOG.md` (every error met, with cause, fix and prevention; add a Lesson if useful),
- `docs/tracking/CONTEXT.md` "Current state",
- any document whose content changed (`DATABASE.md`, `API.md`, `DECISIONS.md`, specs, `ENVIRONMENT.md`, …),
- `docs/CHANGELOG.md` at the end of each phase.

---

## 5. Errors

- When anything fails: stop, read the full error, find the **root cause**, fix it, re-run the checks, and log it in `ERROR_LOG.md` (template there).
- If the same kind of error happens twice, add a **Lesson** line and propose a rule or test that prevents it.
- If you cannot find the cause after two honest attempts, stop and report what you tried. Do not try random changes.

---

## 6. Working style

- Explain briefly in plain language; the owner is a student with solid but not expert knowledge.
- One task at a time; small steps; show progress.
- Prefer the simplest solution that **fully** meets the spec. Simplicity never means skipping tests, documentation updates, safety rules or validation.
- When unsure, ask one clear question instead of assuming.

---

## 7. Installed plugins and connectors

| Tool | Use | Note |
|---|---|---|
| **graphify** (Graphify Labs) | Build a knowledge graph of the repo (`/graphify .`, excluding `ml-test/` and `rag/`; ask if the exclusion option is unclear) after the docs are in place and after each phase; query it to find related files before reading many files | Re-build after big changes. Keep its output folder out of git (`.gitignore`) unless the owner says otherwise. The graph tells you where to look; always read the real file before editing. |
| **Andrej Karpathy skills** | Guidelines: state assumptions, keep changes simple and surgical, verify against goals | Fully compatible with this file |
| **Ponytail** | "Simplest, shortest solution" mode | Use for simplicity, but **this file and `/docs` override it**: never drop tests, docs updates, validation, error handling or safety rules to make code shorter |

If any plugin's guidance conflicts with this file or `/docs`, follow this file and `/docs`.

---

## 8. Project facts you must not get wrong

- Patients and doctors use **two separate web apps** (`frontend/apps/patient-web`, `frontend/apps/doctor-web`); admin lives in the doctor app.
- Frontends use Supabase **only** for sign-in; all data goes through the backend.
- TypeScript (strict) frontends; Python 3.14 backend.
- Fetal/maternal **models must not change**; outputs must match the old backend exactly.
- No combined risk score. No baby-sex prediction. No diagnosis, treatment or dose advice.
- Synthetic/test data only.
- Old folders: read/copy only (rule 7).

---

## 9. Definition of done (every task)
Spec requirements met · tests + lint + types + build pass · reviewed and approved by the owner · tracking files and docs updated · committed after approval.

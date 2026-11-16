# Code Style & Conventions — Alovia

**Version:** 1.0 · **Date:** 2026-11-16

## 1. General Principles
- Readable over clever. Small, focused functions. The simplest code that fully meets the spec.
- Reuse existing components, utilities and patterns before writing new ones.
- No unused code, commented-out code or speculative features.
- Rules, thresholds, wording and lists live in YAML/config files, never inline in code.
- Every function that applies a medical rule names the rule ID it implements (e.g. `# L1-03`).

## 2. Naming

| Item | Backend (Python) | Frontend (TypeScript) |
|---|---|---|
| Files | `snake_case.py` | Components `PascalCase.tsx`; others `camelCase.ts` |
| Classes / components | `PascalCase` | `PascalCase` |
| Functions | `snake_case` | `camelCase`; hooks `useSomething` |
| Variables | `snake_case` | `camelCase` |
| Constants | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| Database fields | `snake_case` (DATABASE.md) | API types keep `snake_case` as returned |
| API routes | lowercase, hyphens, plural nouns (`/patient/doctor-notes`) | — |
| Rule / message IDs | as in the specs (`L1-03`, `HBB-12`, `msg_level1_go_now`) | same |

## 3. Folder Structure
As in `ARCHITECTURE.md` §7. One folder per module. Tests mirror the source layout. Do not create new top-level folders without asking.

## 4. Imports
- Backend: absolute imports from `app.` ; standard library → third-party → local (Ruff sorts them).
- Frontend: path aliases `@/` (app) and `@alovia/ui`, `@alovia/shared` (packages); no deep imports into another package's internals.
- No circular imports. A module imports another module's service only.

## 5. Components (frontend)
- One responsibility per component; feature components in `src/features/<module>/`.
- Base UI only from `packages/ui` (shadcn/ui + tokens). No inline colours or pixel values; use tokens/Tailwind classes.
- Every component handles loading, empty and error states where it shows data.
- All text the patient sees for medical rules comes from the backend message keys or the approved text files, never typed in components.

## 6. Functions
- One logical job; clear name; type hints (Python) / explicit types (TypeScript, `strict: true`).
- Rule engines are **pure functions** (input → output), no database or network access.
- No function longer than about 60 lines without a reason noted in a comment.

## 7. Error Handling
- **Backend:** raise typed application errors (`AppError(code, message, status, fields)`) from services; one exception handler turns them into the API envelope (`API.md`). Catch only errors you can handle; never `except Exception: pass`.
- **Frontend:** TanStack Query error states + an error boundary per page. Show the user-facing messages from `ERROR_HANDLING.md`.
- Do not swallow errors; do not show stack traces to users.

## 8. Comments
Explain **why**, trade-offs, rule IDs and non-obvious behaviour. Do not repeat the code. Docstrings on public service functions and every rule engine.

## 9. Logging
- Backend: Python `logging` with a JSON formatter configured in `app/core/logging.py`; include `request_id`.
- Frontend: no `console.log` in committed code (ESLint rule); errors go through one `reportError` helper.
- Never log sensitive data (`SECURITY.md` §9).

## 10. Formatting, Linting, Types

| | Backend | Frontend |
|---|---|---|
| Formatter | Ruff format | Prettier |
| Linter | Ruff | ESLint (typescript-eslint, react-hooks, jsx-a11y) |
| Types | mypy (strict on `app/modules/*/engine.py` and services) | `tsc --noEmit`, `strict: true` |

## 11. Git
- Fresh repository; default branch `main`; work on `phase-N/<short-name>` branches; merge after the owner's review.
- Commit messages: `type(module): summary` (types: feat, fix, docs, test, refactor, chore). Example: `feat(symptoms): add L1 red-flag rules`.
- Commit only after the owner approves; never commit secrets or `.env`.

## 12. Do
- Follow the specs exactly; cite rule IDs.
- Keep changes focused on the current task.
- Update docs and tracking files with each change.
- Add tests with every feature.

## 13. Don't
- Create duplicate utilities or components.
- Add dependencies without approval.
- Change unrelated files or reformat untouched code.
- Turn `[OPEN]` items into decisions, or hard-code `[CONFIGURABLE]` values.
- Weaken or skip tests to make them pass.

# Testing — Alovia

**Version:** 1.0 · **Date:** 2026-11-16
"The code looks correct" is never enough. A task is finished only when its tests run and pass, and the result is shown to the owner.

## 1. Testing Goals (critical functionality)
- Red-flag rules (Symptom spec §7) and urgent handling — safety critical.
- Genetic rule engine (Genetic spec §7, all 45 haemoglobin pairs) — correctness critical.
- ML predictions identical to the old backend (ML spec §6).
- Access control: patients see only their data; doctors only assigned patients; admins no clinical data.
- Gestational age, month mapping and pregnancy-end behaviour (Journey spec §15).
- RAG safety checks (Phase 7).

## 2. Test Types

### Unit (backend: pytest)
Rule engines, PUQE, GA calculations, unit conversions, validation, message selection. **One test per rule row** where the spec says so.

### Integration (backend: pytest + httpx against a test database)
Every route: happy path, validation errors, role and assignment checks (403/404), database writes, inbox item creation. Test database: the separate Supabase test project `alovia-test` (`TEST_DATABASE_URL`, DEC-034); never the main project.

### Frontend unit/component (Vitest + React Testing Library)
Forms, state handling (loading/empty/error), components with logic (calendar markers, size card, red-flag result screen).

### End-to-end (Playwright, phone 375px and laptop 1280px, light and dark)
Critical flows in §5, with **axe accessibility checks** on each page.

**Frontend redesign additions (FRONTEND_REDESIGN.md §13, redesign step 9):**
- Projects: `phone-light` (375×812) and `laptop-dark` (1280×800) run everything. Five more projects (360 dark, 390 light, 768 dark and light, 1440 light) run only `e2e/responsive.spec.ts` (bottom bar vs side bar, two columns on Home, doctor cards vs table, no sideways scroll, axe).
- `e2e/quality.spec.ts`: every listed patient, doctor and public screen has no sideways scroll at 360 px and no interactive element under 44×44 px at 375 px (a checkbox counts with its label; links inside running text are exempt, WCAG 2.5.8). Layout shift (CLS) under 0.1 on Home, Log and Calendar.
- `e2e/home-ring.spec.ts`: ring above the fold at 375×667, drag preview (weeks 30 and 2) never changes the image or data and shows no log/action buttons, month image at every month boundary, haptics (stubbed `navigator.vibrate`, none with reduced motion), laptop columns.
- `e2e/motion.spec.ts`, `e2e/worst-case.spec.ts`, `e2e/log-sheet.spec.ts`, `e2e/calendar-redesign.spec.ts`, `e2e/doctor-shell.spec.ts`, `e2e/doctor-detail.spec.ts`, `e2e/shell.spec.ts`.
- `packages/ui/src/contrast.test.ts` (Vitest): reads `tokens.css` and checks every text pair at 4.5:1 and the ring arcs at 3:1, both apps, both themes.
- **Visual snapshots** (`e2e/snapshots.spec.ts`): patient Home, Log, Calendar and doctor Home, Patients, patient page at 375 and 1280 px, light and dark (24 images in `e2e/snapshots.spec.ts-snapshots/`). They are made on Windows (`-win32` in the name); another OS such as Linux CI needs its own set first: `npx playwright test snapshots --update-snapshots`. After an intended visual change, update them the same way and review the new images before committing.

## 3. Tools

| Purpose | Backend | Frontend |
|---|---|---|
| Unit | pytest | Vitest + React Testing Library |
| Integration | pytest + httpx | — |
| E2E | — | Playwright (+ @axe-core/playwright) |
| Coverage | pytest-cov | Vitest coverage |

## 4. Test File Structure

```
backend/tests/
├── unit/          (test_symptom_rules.py, test_genetic_engine.py, test_gestational_age.py, …)
├── integration/   (test_patient_journey_api.py, test_access_control.py, …)
└── fixtures/      (synthetic patients, ML reference cases)
frontend/apps/*/src/**/*.test.tsx
frontend/e2e/      (patient/*.spec.ts, doctor/*.spec.ts)
```

## 5. Critical User Flows (E2E)

| Flow | Steps | Expected |
|---|---|---|
| Patient onboarding | Sign up → consent → dates (LMP) → home | Home shows correct weeks + days and "estimate" label |
| L1 symptom | Log → bleeding → Submit | L1 screen, no animation; doctor inbox gets `symptom_l1` |
| Urgent button | Any page → urgent → fits → Submit | L1 advice in ≤ 2 taps |
| Genetic B × S | Enter β-thal carrier + sickle carrier | HBB-12 outcomes, "Review with your doctor", review item for doctor |
| Pregnancy ended | End → loss → no inform | Baby content gone, support screen, no doctor notice |
| Doctor prediction | Create patient → maternal vitals in % and mg/dL → predict | Conversion shown; result saved; limitations visible |
| Share result | Share with message | Patient sees template + message, no probabilities |
| Access control | Doctor A opens Doctor B's patient URL | 404 page |

## 6. Coverage
Practical target: **≥ 90% line coverage for rule engines and calculations**, ≥ 70% for backend overall; frontend: critical components and flows above. Coverage never replaces the rule-by-rule tests.

## 7. Commands (defined in Phase 1, keep in sync with README)

| Task | Command |
|---|---|
| Backend tests | `cd backend && pytest -W error::DeprecationWarning -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning` (database tests need `TEST_DATABASE_URL`) |
| Backend lint/format | `ruff check . && ruff format --check .` |
| Backend types | `mypy app tests migrations scripts` |
| Frontend tests | `cd frontend && npm test` |
| Frontend format | `npm run format:check` |
| Frontend lint | `npm run lint` |
| Frontend types | `npm run typecheck` |
| Frontend build | `npm run build` |
| E2E | `npm run test:e2e` |
| Everything | `scripts/check_all` (`.ps1` for Windows, `.sh` for others) |

## 8. Definition of Done (per task)
- [ ] New/changed behaviour has tests; all tests pass.
- [ ] Lint, format, type checks and builds pass.
- [ ] Critical flow for the change verified (E2E or manual steps written in HISTORY.md).
- [ ] Phone and laptop layouts checked; light and dark checked (UI changes).
- [ ] No warnings left unexplained.
- [ ] Results pasted in `tracking/HISTORY.md`.

## 9. Rules for the agent
- Never delete, skip or weaken a test to make it pass. If a test seems wrong, stop and ask.
- Run the **full** relevant suite, not only the new tests.
- Report exact commands and results, not "tests pass".

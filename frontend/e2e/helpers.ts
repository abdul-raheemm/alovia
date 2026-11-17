import AxeBuilder from '@axe-core/playwright'
import { expect, type Page } from '@playwright/test'

export const PATIENT = 'http://localhost:5173'
export const DOCTOR = 'http://localhost:5174'

/** WCAG 2.1 AA checks with axe (DESIGN_SYSTEM §16, TESTING.md §2). */
export async function expectNoA11yViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  const summary = results.violations.map(
    (v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`,
  )
  expect(summary).toEqual([])
}

/** Answer GET /invites/{code}/check without a backend. */
export async function mockInviteCheck(page: Page, valid: boolean): Promise<void> {
  await page.route('**/api/v1/invites/*/check', (route) =>
    route.fulfill({ json: { data: { valid }, error: null } }),
  )
}

export const TEST_PATIENT_ME = {
  user: {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'test.patient@example.test',
    role: 'patient',
  },
  patient: { id: '22222222-2222-2222-2222-222222222222', name: 'Test Patient 1' },
  doctor: null,
  consent: { current_version: '2026-11-v1', accepted: true },
}

const NAV_ITEMS = [
  { key: 'home', label: 'Home' },
  { key: 'calendar', label: 'Calendar' },
  { key: 'log_symptoms', label: 'Log symptoms' },
  { key: 'appointments', label: 'Appointments' },
  { key: 'doctor_notes', label: 'Doctor notes' },
  { key: 'more', label: 'More' },
]

/** A GET /patient/journey/home reply. Message texts are null, as before doctor approval. */
export function journeyHome(overrides: Record<string, unknown> = {}) {
  return {
    state: 'no_date',
    dates: { due_date: null, lmp_date: null, due_date_source: null },
    pregnancy: null,
    nav_items: NAV_ITEMS,
    show_prototype_banner: true,
    messages: {
      msg_onboarding: null,
      msg_estimate_label: null,
      msg_dates_updated_by_clinician: null,
      msg_confirm_override_clinician_date: null,
      msg_past_due_date: null,
      msg_beyond_42_weeks: null,
    },
    notices: [],
    ...overrides,
  }
}

/** Sign in as a test patient without Supabase: a stored session plus a mocked GET /me.
 * The session is fake and only read locally; no request goes to Supabase. */
export async function signInAsPatient(page: Page, me: unknown = TEST_PATIENT_ME): Promise<void> {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString('base64url')
  const expires = Math.floor(Date.now() / 1000) + 3600
  const claims = { sub: TEST_PATIENT_ME.user.id, exp: expires }
  const session = {
    access_token: `${b64({ alg: 'ES256', typ: 'JWT' })}.${b64(claims)}.sig`,
    token_type: 'bearer',
    expires_in: 3600,
    expires_at: expires,
    refresh_token: 'e2e-refresh',
    user: { id: TEST_PATIENT_ME.user.id, aud: 'authenticated', email: TEST_PATIENT_ME.user.email },
  }
  // key = sb-<first label of VITE_SUPABASE_URL's host>-auth-token (see playwright.config.ts)
  await page.addInitScript((value) => {
    localStorage.setItem('sb-e2e-test-auth-token', value)
  }, JSON.stringify(session))
  await page.route('**/api/v1/me', (route) => route.fulfill({ json: { data: me, error: null } }))
}

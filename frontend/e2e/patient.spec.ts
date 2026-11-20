import { expect, test } from '@playwright/test'

import { expectNoA11yViolations, mockInviteCheck, PATIENT, signInAsPatient } from './helpers'

const INVALID = "This invite link isn't valid. Please ask your doctor for a new one."

test('landing page: disclaimer, sign in, and no open sign-up (UX_FLOWS P1, DEC-024)', async ({
  page,
}) => {
  await page.goto(PATIENT)
  await expect(page.getByRole('heading', { level: 1, name: 'Alovia' })).toBeVisible()
  await expect(page.getByText(/^Alovia is a research prototype/)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible()
  await expect(page.getByText('New here? Ask your doctor for an invite link.')).toBeVisible()
  await expect(page.getByRole('link', { name: /sign up|create account/i })).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('invite link without a code, or with a bad code, shows no sign-up form', async ({ page }) => {
  await page.goto(`${PATIENT}/join`)
  await expect(page.getByText(INVALID)).toBeVisible()

  await mockInviteCheck(page, false)
  await page.goto(`${PATIENT}/join?code=WRONGCOD`)
  await expect(page.getByText(INVALID)).toBeVisible()
  await expect(page.getByLabel('Email')).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('valid invite: sign-up form with unticked consent boxes; Continue needs both', async ({
  page,
}) => {
  await mockInviteCheck(page, true)
  await page.goto(`${PATIENT}/join?code=ABCD2345`)
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  const age = page.getByRole('checkbox', { name: 'I am 18 years or older.' })
  const agree = page.getByRole('checkbox', { name: /I have read the Privacy Policy/ })
  const cont = page.getByRole('button', { name: 'Continue' })
  await expect(age).not.toBeChecked()
  await expect(agree).not.toBeChecked()
  await expect(cont).toBeDisabled()
  await age.check()
  await expect(cont).toBeDisabled()
  await agree.check()
  await expect(cont).toBeEnabled()
  await expectNoA11yViolations(page)
})

test('a signed-in patient opening an invite link is told, not taken into her app', async ({
  page,
}) => {
  await signInAsPatient(page) // an existing, linked patient in this browser
  await mockInviteCheck(page, true)
  await page.route('**/auth/v1/logout*', (route) => route.fulfill({ status: 204, body: '' }))
  await page.goto(`${PATIENT}/join?code=ABCD2345`)
  await expect(page.getByText(/You are signed in as test\.patient@example\.test/)).toBeVisible()
  await expect(page).toHaveURL(`${PATIENT}/join?code=ABCD2345`)
  // her app must not try to link someone else's invite
  expect(await page.evaluate(() => localStorage.getItem('alovia-invite-code'))).toBeNull()
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  expect(await page.evaluate(() => localStorage.getItem('alovia-invite-code'))).toBe('ABCD2345')
})

test('signed-out visitors are sent from the app to sign-in', async ({ page }) => {
  await page.goto(`${PATIENT}/home`)
  await expect(page).toHaveURL(`${PATIENT}/signin`)
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await expectNoA11yViolations(page)
})

for (const [path, heading] of [
  ['/privacy', 'Privacy Policy — Alovia (DRAFT)'],
  ['/terms', /Terms of Use/],
  ['/disclaimer', 'Medical Disclaimer — Alovia (DRAFT)'],
  ['/cookies', /Cookie/],
  ['/consent', /Consent/],
  ['/about', 'About Alovia'],
] as const) {
  test(`legal page ${path} renders from docs/legal`, async ({ page }) => {
    await page.goto(`${PATIENT}${path}`)
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible()
    await expectNoA11yViolations(page)
  })
}

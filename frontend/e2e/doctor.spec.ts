import { expect, test } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsPatient } from './helpers'

test('doctor app: signed-out visitors land on sign-in; no sign-up', async ({ page }) => {
  await page.goto(DOCTOR)
  await expect(page).toHaveURL(`${DOCTOR}/signin`)
  await expect(page.getByRole('heading', { name: 'Doctor sign-in' })).toBeVisible()
  await expect(page.getByText('Doctor accounts are invited by the administrator.')).toBeVisible()
  await expect(page.getByRole('link', { name: /sign up|create account/i })).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('doctor app: sign-in form asks for both fields', async ({ page }) => {
  await page.goto(`${DOCTOR}/signin`)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByText('Enter your email.')).toBeVisible()
  await expect(page.getByText('Enter your password.')).toBeVisible()
  await expectNoA11yViolations(page)
})

test('doctor app: legal page renders', async ({ page }) => {
  await page.goto(`${DOCTOR}/privacy`)
  await expect(
    page.getByRole('heading', { level: 1, name: 'Privacy Policy — Alovia (DRAFT)' }),
  ).toBeVisible()
  await expectNoA11yViolations(page)
})

test('doctor app: doctors accept the consent once at first sign-in', async ({ page }) => {
  // owner decision 2026-11-17: doctors and admins accept the app-wide consent once
  let accepted = false
  const doctorMe = () => ({
    user: {
      id: '66666666-6666-6666-6666-666666666666',
      email: 'test.doctor@example.test',
      role: 'doctor',
    },
    patient: null,
    doctor: { id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', specialty: null },
    consent: { current_version: '2026-11-v1', accepted },
  })
  let posted: unknown = null
  await signInAsPatient(page) // the fake stored session works for both apps
  await page.route('**/api/v1/me', (route) =>
    route.fulfill({ json: { data: doctorMe(), error: null } }),
  )
  await page.route('**/api/v1/me/consent', (route) => {
    posted = route.request().postDataJSON()
    accepted = true
    return route.fulfill({
      json: { data: { current_version: '2026-11-v1', accepted: true }, error: null },
    })
  })
  await page.goto(`${DOCTOR}/home`)

  await expect(page.getByRole('heading', { name: 'Before you start' })).toBeVisible()
  const next = page.getByRole('button', { name: 'Continue' })
  await expect(next).toBeDisabled() // both boxes start unticked
  const boxes = page.getByRole('checkbox')
  await expect(boxes).toHaveCount(2)
  await boxes.nth(0).check()
  await expect(next).toBeDisabled()
  await boxes.nth(1).check()
  await expectNoA11yViolations(page)
  await next.click()
  expect(posted).toMatchObject({ age_confirmed_18_plus: true })
  await expect(page.getByRole('heading', { level: 1, name: 'Home' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Before you start' })).toHaveCount(0)
})

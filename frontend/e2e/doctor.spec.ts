import { expect, test } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations } from './helpers'

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

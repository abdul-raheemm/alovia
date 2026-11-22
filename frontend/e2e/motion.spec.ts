import { expect, test, type Page } from '@playwright/test'

import { journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// FRONTEND_REDESIGN §5.4 and §11 rule 4 (step 7): motion only when the user allows it.
const HOME = journeyHome({
  state: 'active',
  dates: { due_date: '2027-03-01', lmp_date: '2026-05-25', due_date_source: 'lmp_estimate' },
  pregnancy: {
    completed_weeks: 24,
    days: 3,
    days_to_go: 104,
    content_week: 24,
    trimester: 2,
    month: 6,
    is_estimate: true,
  },
  months: MONTHS,
})

async function openHome(page: Page) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.route('**/api/v1/patient/symptoms/vocabulary', () => undefined) // sheet stays loading
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('Month 6 · now')).toBeVisible()
}

const style = (page: Page, selector: string, prop: string) =>
  page
    .locator(selector)
    .first()
    .evaluate((e, p) => getComputedStyle(e).getPropertyValue(p), prop)

test('motion allowed: Home cards rise in once; the Log sheet slides in', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await openHome(page)
  expect(await style(page, '.home-rise > *', 'animation-name')).toBe('alovia-rise')
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Log' }).click()
  await expect(page.getByRole('dialog', { name: 'Log symptoms' })).toBeVisible()
  expect(await style(page, 'dialog[data-sheet]', 'transition-duration')).toBe('0.3s')
  // back to Home in the same visit: no second entrance
  await page.getByRole('button', { name: 'Close' }).click()
  await expect(page.locator('.home-rise')).toHaveCount(0)
})

test('reduced motion: no entrance, no sheet movement, no float', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await openHome(page)
  expect(await style(page, '.home-rise > *', 'animation-name')).toBe('none')
  expect(await style(page, '.ring-float', 'animation-name')).toBe('none')
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Log' }).click()
  await expect(page.getByRole('dialog', { name: 'Log symptoms' })).toBeVisible()
  // the design system's reduced-motion rule makes every transition 0.01 ms: effectively instant
  expect(parseFloat(await style(page, 'dialog[data-sheet]', 'transition-duration'))).toBeLessThan(
    0.001,
  )
})

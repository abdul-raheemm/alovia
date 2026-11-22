import { expect, test } from '@playwright/test'

import {
  DOCTOR,
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
} from './helpers'

// FRONTEND_REDESIGN §6 and §13 "Responsive layout": runs at 360, 375, 390, 768, 1280 and 1440 px,
// light and dark (see playwright.config.ts projects).
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

test('patient Home: bottom bar below 1024 px, side bar and two columns from 1024 px', async ({
  page,
}) => {
  const width = page.viewportSize()?.width ?? 0
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('Month 6 · now')).toBeVisible()
  const nav = page.getByRole('navigation', { name: 'Main' })
  const navBox = await nav.boundingBox()
  const ring = await page.getByRole('img', { name: /^Pregnancy ring/ }).boundingBox()
  const quickLog = await page.getByRole('link', { name: 'Log a symptom' }).boundingBox()
  if (width < 1024) {
    expect(Math.round((navBox?.y ?? 0) + (navBox?.height ?? 0))).toBe(page.viewportSize()?.height)
    expect(quickLog?.y ?? 0).toBeGreaterThan(ring?.y ?? 0) // one column
  } else {
    expect(navBox?.x).toBe(0) // side bar on the left
    expect((ring?.x ?? 0) + (ring?.width ?? 0)).toBeLessThan(quickLog?.x ?? 0) // two columns
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width)
  await expectNoA11yViolations(page)
})

test('doctor patients: cards below 768 px, a table from 768 px', async ({ page }) => {
  const width = page.viewportSize()?.width ?? 0
  await signInAsDoctor(page)
  await page.route('**/api/v1/doctor/patients', (r) =>
    r.fulfill({
      json: {
        data: [
          {
            id: '00000000-0000-0000-0000-000000000001',
            name: 'Test Patient A',
            linked: true,
            ga_weeks: 24,
            ga_days: 1,
            due_date: '2027-03-01',
            fetal: null,
            maternal: null,
            genetic: null,
            symptom: { level: 'L2', created_at: '2026-11-19T05:00:00Z' },
            unseen_count: 1,
            pregnancy_status: 'active',
            group: 2,
          },
        ],
        error: null,
      },
    }),
  )
  await page.goto(`${DOCTOR}/patients`)
  if (width < 768) {
    await expect(page.getByRole('list', { name: 'Patient list' })).toBeVisible()
    await expect(page.getByRole('table')).toBeHidden()
  } else {
    await expect(
      page.getByRole('region', { name: 'Patient list' }).getByRole('table'),
    ).toBeVisible()
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width)
  await expectNoA11yViolations(page)
})

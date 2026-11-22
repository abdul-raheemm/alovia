import { expect, test, type Page } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsDoctor } from './helpers'

// FRONTEND_REDESIGN §8.4, §8.5 (step 6b). Mocked API, synthetic data only.
const PID = 'aaaaaaaa-0000-0000-0000-000000000009'
const AT = '2026-11-19T05:00:00Z'
const PATIENT = {
  id: PID,
  name: 'Test Patient E',
  linked: true,
  ga_weeks: 24,
  ga_days: 2,
  due_date: '2027-03-01',
  fetal: { predicted_class: 'Suspect', created_at: AT },
  maternal: null,
  genetic: null,
  symptom: { level: 'L2', created_at: AT },
  unseen_count: 3,
  pregnancy_status: 'active',
  group: 2,
  age: 30,
  notes: null,
  due_date_source: 'lmp_estimate',
  doctors: [{ id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', is_primary: true }],
  hba1c_note: false,
}

async function setUp(page: Page) {
  await signInAsDoctor(page)
  await page.route(`**/api/v1/doctor/patients/${PID}`, (r) =>
    r.fulfill({ json: { data: PATIENT, error: null } }),
  )
  await page.route(`**/api/v1/doctor/patients/${PID}/symptoms`, (r) =>
    r.fulfill({
      json: {
        data: {
          checkins: [
            {
              checkin_id: 'c1',
              created_at: AT,
              pregnancy_week: 24,
              red_flag_level: 'L0',
              matched_rules: [],
              message_keys: [],
              source: 'form',
              local_date: '2026-11-19',
              entries: [
                {
                  symptom: 'headache',
                  severity: 'mild',
                  duration: null,
                  body_area: null,
                  details: null,
                  occurred_at: null,
                  notes: null,
                },
              ],
              pattern_changes: [],
            },
          ],
          charts: {
            symptoms: [
              {
                symptom: 'headache',
                label: 'Headache',
                points: [
                  {
                    local_date: '2026-11-12',
                    pregnancy_week: 23,
                    severity: 'mild',
                    duration: null,
                  },
                  {
                    local_date: '2026-11-19',
                    pregnancy_week: 24,
                    severity: 'mild',
                    duration: null,
                  },
                ],
              },
            ],
            puqe: [],
          },
          labels: { headache: 'Headache' },
          puqe_bands: [{ band: 'mild', min: 3, max: 6 }],
        },
        error: null,
      },
    }),
  )
}
const phone = (page: Page) => (page.viewportSize()?.width ?? 0) < 768

test('header card: name, age, week, due date and source, unseen, one badge per module', async ({
  page,
}) => {
  await setUp(page)
  await page.goto(`${DOCTOR}/patients/${PID}`)
  await expect(page.getByRole('heading', { level: 1, name: 'Test Patient E' })).toBeVisible()
  await expect(
    page.getByText('Age 30 · Week 24w 2d · Due 1 Mar 2027 (LMP estimate) · 3 unseen'),
  ).toBeVisible()
  const header = page
    .locator('main')
    .locator('div', { has: page.getByRole('heading', { level: 1 }) })
    .first()
  await expect(header.getByText('Fetal Suspect')).toBeVisible()
  await expect(header.getByText('Symptoms L2')).toBeVisible()
  await expect(header.getByText(/maternal/i)).toHaveCount(0) // no result -> no badge
  await expectNoA11yViolations(page)
})

test('the open tab is scrolled into view on a phone', async ({ page }) => {
  test.skip(!phone(page), 'phone layout only')
  await setUp(page)
  await page.goto(`${DOCTOR}/patients/${PID}/pregnancy`)
  const tab = page.getByRole('navigation', { name: 'Patient sections' }).getByRole('link', {
    name: 'Pregnancy',
  })
  await expect(tab).toHaveAttribute('aria-current', 'page')
  await expect(tab).toBeInViewport()
  const wide = await page.evaluate(() => document.documentElement.scrollWidth)
  expect(wide).toBeLessThanOrEqual(375)
})

test('"View as table" shows the numbers and hides the chart', async ({ page }) => {
  await setUp(page)
  await page.goto(`${DOCTOR}/patients/${PID}/symptoms`)
  const card = page.locator('div', { has: page.getByRole('heading', { name: 'Headache' }) }).last()
  const toggle = page.getByRole('button', { name: 'View as table' }).first()
  await expect(page.getByRole('table', { name: /Headache/ })).not.toBeVisible() // screen readers only
  await toggle.click()
  await expect(page.getByRole('button', { name: 'View as chart' }).first()).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  const table = page.getByRole('table', { name: /Headache/ })
  await expect(table).toBeVisible()
  await expect(table.getByRole('row', { name: /wk 24/ })).toBeVisible()
  await expect(card.locator('.recharts-responsive-container')).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('phone: a form keeps its main button in a bar at the bottom of the screen', async ({
  page,
}) => {
  test.skip(!phone(page), 'phone layout only')
  await setUp(page)
  await page.route(`**/api/v1/doctor/patients/${PID}/notes`, (r) =>
    r.fulfill({ json: { data: [], error: null } }),
  )
  await page.goto(`${DOCTOR}/patients/${PID}/notes`)
  const bar = page.locator('[data-sticky-actions]').first()
  await expect(bar).toBeVisible()
  expect(await bar.evaluate((e) => getComputedStyle(e).position)).toBe('sticky')
  const button = await bar.getByRole('button').boundingBox()
  expect(button?.height).toBeGreaterThanOrEqual(44)
  expect(Math.round(button?.width ?? 0)).toBeGreaterThan(300) // full width on a phone
})

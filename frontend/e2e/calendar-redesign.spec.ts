import { expect, test, type Page } from '@playwright/test'

import {
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  mockCalendar,
  PATIENT,
  signInAsPatient,
} from './helpers'

// FRONTEND_REDESIGN §7.6 (DEC-115: rows are pregnancy weeks). Fixed clock; test strings only.
const NOW = new Date('2026-11-17T10:00:00')
const CALENDAR = {
  start: '2026-05-04', // a Monday: rows run Monday to Sunday
  end: '2027-02-22',
  milestones: [{ date: '2026-11-23', kind: 'new_week', value: 29 }],
  symptom_days: [
    { date: '2026-11-10', levels: ['L0', 'L2'] },
    { date: '2026-11-12', levels: ['L0'] },
  ],
}
const HOME = journeyHome({
  state: 'active',
  dates: { due_date: '2027-02-08', lmp_date: '2026-05-04', due_date_source: 'lmp_estimate' },
  pregnancy: {
    completed_weeks: 28,
    days: 1,
    days_to_go: 83,
    content_week: 28,
    trimester: 3,
    month: 7,
    is_estimate: true,
  },
  months: MONTHS,
})

async function setUp(page: Page) {
  await page.clock.setFixedTime(NOW)
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await mockCalendar(page, CALENDAR)
}

const isLaptop = (page: Page) => (page.viewportSize()?.width ?? 0) >= 1024

test('phone: rows are pregnancy weeks with a W gutter; 44 px cells; today outlined', async ({
  page,
}) => {
  test.skip(isLaptop(page), 'phone layout only')
  await setUp(page)
  await page.goto(`${PATIENT}/calendar`)
  const nov23 = page.getByRole('button', { name: /^23 November 2026/ })
  await expect(nov23).toBeVisible()
  // the row that starts on 23 November (a Monday) is pregnancy week 29
  const row = page.getByRole('row').filter({ has: nov23 })
  await expect(row.getByRole('rowheader')).toHaveText('W29')
  await expect(page.getByText('Mo', { exact: true }).first()).toBeVisible()

  const box = await nov23.boundingBox()
  expect(box?.width).toBeGreaterThanOrEqual(44)
  expect(box?.height).toBeGreaterThanOrEqual(44)
  const today = page.getByRole('button', { name: /^17 November 2026.*today/ })
  expect(await today.evaluate((e) => getComputedStyle(e).outlineStyle)).toBe('solid')
  // month names stay at the top while their month scrolls
  const caption = page.getByText('November 2026', { exact: true })
  expect(
    await caption.evaluate((e) =>
      e.parentElement ? getComputedStyle(e.parentElement).position : '',
    ),
  ).toBe('sticky')
  await expectNoA11yViolations(page)
})

test('phone: no sideways scroll at 360 px', async ({ page }) => {
  test.skip(isLaptop(page), 'phone layout only')
  await page.setViewportSize({ width: 360, height: 740 })
  await setUp(page)
  await page.goto(`${PATIENT}/calendar`)
  await expect(page.getByRole('button', { name: /^23 November 2026/ })).toBeVisible()
  const wide = await page.evaluate(() => document.documentElement.scrollWidth)
  expect(wide).toBeLessThanOrEqual(360)
})

test('phone: "Jump to today" shows only when today is far away, and brings it back', async ({
  page,
}) => {
  test.skip(isLaptop(page), 'phone layout only')
  await setUp(page)
  await page.goto(`${PATIENT}/calendar`)
  const today = page.getByRole('button', { name: /^17 November 2026.*today/ })
  await expect(today).toBeInViewport() // opens on today
  const jump = page.getByRole('button', { name: 'Jump to today' })
  await expect(jump).toHaveCount(0)
  await page.evaluate(() => window.scrollTo(0, 0)) // back to May
  await expect(jump).toBeVisible()
  await jump.click()
  await expect(today).toBeInViewport()
  await expect(jump).toHaveCount(0)
})

test('a Level 2 day has its own icon and words; the day lists each symptom', async ({ page }) => {
  await setUp(page)
  await page.route('**/api/v1/patient/symptoms/vocabulary', (r) =>
    r.fulfill({
      json: {
        data: {
          logging_open: true,
          pregnancy_week: 28,
          severities: { mild: 'Mild' },
          durations: { under_1_hour: 'Under 1 hour' },
          labour_durations: {},
          body_areas: {},
          common: [
            {
              id: 'headache',
              label: 'Headache',
              puqe: false,
              flags: {},
              severity: true,
              duration: true,
            },
          ],
          warning: [{ id: 'high_fever', label: 'High fever', labour_duration: false }],
          puqe_questions: [],
          puqe_source: {
            publisher: 'P',
            title: 'T',
            url: 'https://example.test',
            date_accessed: '2026-11-18',
          },
          puqe_bands: [],
          draft_ttl_minutes: 30,
        },
        error: null,
      },
    }),
  )
  await page.route('**/api/v1/patient/symptoms/checkins', (r) =>
    r.fulfill({
      json: {
        data: [
          {
            checkin_id: '1',
            created_at: '2026-11-10T05:00:00Z',
            pregnancy_week: 27,
            red_flag_level: 'L2',
            matched_rules: [],
            message_keys: [],
            source: 'form',
            local_date: '2026-11-10',
            entries: [
              {
                symptom: 'headache',
                severity: 'mild',
                duration: 'under_1_hour',
                body_area: null,
                details: null,
                occurred_at: null,
                notes: null,
              },
              {
                symptom: 'high_fever',
                severity: null,
                duration: null,
                body_area: null,
                details: null,
                occurred_at: null,
                notes: null,
              },
            ],
          },
        ],
        error: null,
      },
    }),
  )
  await page.goto(`${PATIENT}/calendar`)
  const l2Day = page.getByRole('button', {
    name: /^10 November 2026.*symptoms logged, Level 2 warning logged/,
  })
  await expect(l2Day).toBeVisible()
  await expect(l2Day.locator('svg.text-caution')).toHaveCount(1) // not the L1 triangle
  await expect(l2Day.locator('svg.text-urgent')).toHaveCount(0)
  await l2Day.click()
  const details = page.getByRole('region', { name: '10 November 2026' })
  await expect(details.getByText('Week 27', { exact: true })).toBeVisible()
  await expect(details.getByText('Check-in: Contact your doctor today')).toBeVisible()
  await expect(details.getByText('Headache · Mild · Under 1 hour')).toBeVisible()
  await expect(details.getByText('High fever', { exact: true })).toBeVisible()
  await expectNoA11yViolations(page)
})

test('laptop: one month with Previous, Next and Today; the day panel on the right', async ({
  page,
}) => {
  test.skip(!isLaptop(page), 'laptop layout only')
  await setUp(page)
  await page.goto(`${PATIENT}/calendar`)
  await expect(page.getByText('November 2026', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /previous month/i }).click()
  await page.getByRole('button', { name: /previous month/i }).click()
  await expect(page.getByText('September 2026', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: /^12 September 2026/ }).click()
  await expect(page.getByRole('heading', { name: '12 September 2026' })).toBeVisible()
  await page.getByRole('button', { name: 'Today', exact: true }).click()
  await expect(page.getByText('November 2026', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: '17 November 2026' })).toBeVisible()
  // the panel sits to the right of the month grid
  const grid = await page.getByRole('grid').boundingBox()
  const panel = await page.getByRole('region', { name: '17 November 2026' }).boundingBox()
  expect((panel?.x ?? 0) > (grid?.x ?? 0) + (grid?.width ?? 0) - 1).toBe(true)
  await expectNoA11yViolations(page)
})

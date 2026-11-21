import { expect, test } from '@playwright/test'

import {
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  PATIENT,
  signInAsPatient,
  testAppointment,
  testContentItem,
} from './helpers'

const PENDING = '[Text pending doctor approval]'
const HOME_URL = '**/api/v1/patient/journey/home'

const PREGNANCY = {
  completed_weeks: 24,
  days: 3,
  days_to_go: 104,
  content_week: 24,
  trimester: 2,
  month: 6,
  is_estimate: true,
}

const FULL_HOME = journeyHome({
  state: 'active',
  dates: { due_date: '2027-03-01', lmp_date: '2026-05-25', due_date_source: 'lmp_estimate' },
  pregnancy: PREGNANCY,
  months: MONTHS,
  stage_items: [testContentItem()],
  size: {
    week: 24,
    length_cm: null,
    weight_g: 600,
    object_icon_id: 'test_icon',
    object_name: 'test object',
    source: {
      publisher: 'Test Publisher',
      title: 'Test size table',
      url: 'https://example.test/sizes',
      licence: 'CC BY 4.0',
      date_accessed: '2026-11-17',
      kb_doc_id: null,
    },
    review_status: 'unreviewed',
  },
  next_appointment: testAppointment({ title: 'Check-up' }),
})

test('home shows the §4.3 blocks: baby card, stage content with source, banner, appointment, months', async ({
  page,
}) => {
  await signInAsPatient(page)
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: FULL_HOME, error: null } }))
  await page.goto(`${PATIENT}/home`)

  // ring centre (FRONTEND_REDESIGN §7.1-7.3): today's month image and caption; size worded as
  // typical, never "your baby"
  await expect(page.getByText('Month 6 · now')).toBeVisible()
  // the current month's drawing appears twice: ring centre and months strip
  const drawing = page.getByRole('img', {
    name: 'Illustration of a typical baby in month 6 of pregnancy',
  })
  await expect(drawing).toHaveCount(2)
  await expect(drawing.first()).toHaveAttribute('src', '/illustrations/month_6.webp')
  await expect(page.getByText('About the size of a test object (about 600 g)')).toBeVisible()
  await expect(page.getByText('Test size table')).toBeVisible()
  expect(await page.content()).not.toContain('your baby')

  // this stage: prototype banner (pending text) + the item with its source line
  await expect(page.getByRole('status').filter({ hasText: PENDING })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Example stage content' })).toBeVisible()
  await expect(page.getByRole('link', { name: /Test Publisher/ })).toBeVisible()

  // quick log, next appointment, months strip with the current month marked
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toBeVisible()
  // date and time come from the API as local values, shown as they are
  await expect(page.getByText('Check-up — 20 November 2026, 10:30 am')).toBeVisible()
  const strip = page.getByRole('list').filter({ hasText: 'You are here' })
  await expect(strip.getByRole('link')).toHaveCount(9)
  await expect(strip.getByRole('link', { name: /Month 6/ })).toHaveAttribute('aria-current', 'true')
  await expectNoA11yViolations(page)
})

test('month card opens the detail view with content, sources and the warning-signs link', async ({
  page,
}) => {
  await signInAsPatient(page)
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: FULL_HOME, error: null } }))
  await page.route('**/api/v1/patient/journey/months/6', (route) =>
    route.fulfill({
      json: {
        data: {
          month: 6,
          week_start: 23,
          week_end: 27,
          is_current: true,
          items: [
            testContentItem({
              id: 'test_month_6',
              granularity: 'month',
              month: 6,
              week_start: null,
              week_end: null,
              title: 'Example month content',
            }),
          ],
        },
        error: null,
      },
    }),
  )
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('link', { name: /Month 6.*You are here/ }).click()
  await expect(page).toHaveURL(`${PATIENT}/months/6`)
  await expect(page.getByRole('heading', { level: 1, name: 'Month 6' })).toBeVisible()
  await expect(page.getByText('Weeks 23–27')).toBeVisible()
  await expect(page.getByText('You are here')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Example month content' })).toBeVisible()
  await expect(page.getByRole('status').filter({ hasText: PENDING })).toBeVisible()
  await expect(page.getByRole('link', { name: 'warning signs' })).toBeVisible()
  await expectNoA11yViolations(page)
})

test('without content or size, home shows the empty stage state and no size line', async ({
  page,
}) => {
  await signInAsPatient(page)
  const bare = journeyHome({
    state: 'active',
    dates: { due_date: '2027-03-01', lmp_date: null, due_date_source: 'clinician_confirmed' },
    pregnancy: { ...PREGNANCY, is_estimate: false },
    months: MONTHS,
  })
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: bare, error: null } }))
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('Content for this stage is being prepared.')).toBeVisible()
  await expect(page.getByText('About the size of')).toHaveCount(0) // §7.2: no source, no size
  await expect(page.getByText('Next appointment')).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test("home: logged today and this week's summary, her data apart from the content (§9.4)", async ({
  page,
}) => {
  await signInAsPatient(page)
  const summaryHome = {
    ...FULL_HOME,
    logged_today: true,
    weekly_summary: {
      week_start: '2026-11-15',
      week_end: '2026-11-21',
      days_logged: 2,
      top_symptoms: [{ symptom: 'fatigue', label: 'Tiredness', count: 3 }],
      red_flag_days: ['2026-11-17'],
      common_at_stage: [
        testContentItem({
          id: 'test_common',
          content_type: 'common_symptoms',
          title: 'Example common content',
        }),
      ],
    },
  }
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: summaryHome, error: null } }))
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('Logged today')).toBeVisible()
  const summary = page.getByRole('region', { name: "This week's summary" })
  await expect(summary.getByRole('heading', { name: 'You logged' })).toBeVisible()
  await expect(summary.getByText('Days with check-ins: 2')).toBeVisible()
  await expect(summary.getByText('Tiredness: 3')).toBeVisible()
  await expect(summary.getByText('Red-flag days: 17 November 2026')).toBeVisible()
  // the content part is a separate Learn card (D15), and nothing compares the two
  await expect(
    summary.getByRole('article').filter({ hasText: 'Example common content' }),
  ).toBeVisible()
  expect(await summary.textContent()).not.toMatch(/normal|typical for|nothing to worry/i)
  await expectNoA11yViolations(page)
})

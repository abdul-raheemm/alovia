import { expect, test } from '@playwright/test'

import {
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  PATIENT,
  signInAsPatient,
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
  next_appointment: { appointment_at: '2026-11-20T04:30:00Z', has_time: true, title: 'Check-up' },
})

test('home shows the §4.3 blocks: baby card, stage content with source, banner, appointment, months', async ({
  page,
}) => {
  await signInAsPatient(page)
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: FULL_HOME, error: null } }))
  await page.goto(`${PATIENT}/home`)

  // baby card: placeholder illustration, size worded as typical, never "your baby"
  await expect(page.getByRole('heading', { name: 'Month 6', exact: true })).toBeVisible()
  // the current month's drawing appears twice: baby card and months strip
  await expect(page.getByRole('img', { name: 'Placeholder drawing for month 6' })).toHaveCount(2)
  await expect(page.getByText('About the size of a test object (about 600 g)')).toBeVisible()
  await expect(page.getByText('Test size table')).toBeVisible()
  expect(await page.content()).not.toContain('your baby')

  // this stage: prototype banner (pending text) + the item with its source line
  await expect(page.getByRole('status').filter({ hasText: PENDING })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Example stage content' })).toBeVisible()
  await expect(page.getByRole('link', { name: /Test Publisher/ })).toBeVisible()

  // quick log, next appointment, months strip with the current month marked
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toBeVisible()
  await expect(page.getByText('Check-up —')).toBeVisible()
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

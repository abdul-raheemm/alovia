import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// Journey spec §4.2 notification bar and §10.3 doctor notes. Fake test wording only.

const ACTIVE_HOME = journeyHome({
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

const note = (id: string, type: string, target_ref: string) => ({
  id,
  type,
  target_ref,
  created_at: '2026-11-17T04:30:00Z',
})

async function home(page: Page) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) =>
    route.fulfill({ json: { data: ACTIVE_HOME, error: null } }),
  )
}

test('notification bar: tap opens the target and marks it read; dismiss removes it', async ({
  page,
}) => {
  await home(page)
  let items = [
    note('n-week', 'new_week', '28'),
    note('n-month', 'new_month', '7'),
    note('n-note', 'doctor_note', 'x'),
  ]
  const posted: string[] = []
  await page.route('**/api/v1/patient/notifications', (route) =>
    route.fulfill({ json: { data: items, error: null } }),
  )
  await page.route('**/api/v1/patient/notifications/*/*', (route) => {
    const [, id, action] =
      new URL(route.request().url()).pathname.match(/notifications\/(.+)\/(.+)$/) ?? []
    posted.push(`${id}/${action}`)
    items = items.filter((n) => n.id !== id)
    return route.fulfill({ json: { data: null, error: null } })
  })
  await page.route('**/api/v1/patient/journey/months/7', (route) =>
    route.fulfill({
      json: {
        data: { month: 7, week_start: 28, week_end: 31, is_current: true, items: [] },
        error: null,
      },
    }),
  )
  await page.goto(`${PATIENT}/home`)

  const bar = page.getByRole('region', { name: 'Notifications' })
  await expect(bar.getByRole('link')).toHaveCount(2)
  await expect(bar.getByRole('link', { name: 'Week 28 has started' })).toBeVisible()
  // a new doctor note is a Home status card, not a bar item (DEC-112, step 4 plan)
  const noteCard = page.getByRole('link', { name: 'Your doctor shared a note with you' })
  await expect(noteCard).toHaveCount(1)
  await expect(bar.getByRole('link', { name: 'Your doctor shared a note with you' })).toHaveCount(0)
  await expectNoA11yViolations(page)

  await bar.getByRole('button', { name: 'Dismiss: Week 28 has started' }).click()
  await expect(bar.getByRole('link')).toHaveCount(1)
  expect(posted).toContain('n-week/dismiss')

  await bar.getByRole('link', { name: 'Month 7 has started' }).click()
  await expect(page).toHaveURL(`${PATIENT}/months/7`)
  await expect.poll(() => posted).toContain('n-month/read')
})

test('no notifications: the bar is not shown', async ({ page }) => {
  await home(page)
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByRole('heading', { name: '28 weeks, 1 day pregnant' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Notifications' })).toHaveCount(0)
})

test('doctor notes: shared notes newest first, read-only; empty state', async ({ page }) => {
  await home(page)
  await page.route('**/api/v1/patient/doctor-notes', (route) =>
    route.fulfill({
      json: {
        data: [
          {
            id: 'a',
            body: 'Test note newer',
            doctor_name: 'Test Doctor',
            created_on: '2026-11-17',
            related_ref: null,
          },
          {
            id: 'b',
            body: 'Test note older',
            doctor_name: 'Test Doctor',
            created_on: '2026-11-10',
            related_ref: null,
          },
        ],
        error: null,
      },
    }),
  )
  await page.goto(`${PATIENT}/doctor-notes`)
  await expect(page.getByRole('heading', { level: 1, name: 'Doctor notes' })).toBeVisible()
  const notes = page.getByRole('main').getByRole('listitem')
  await expect(notes).toHaveCount(2)
  await expect(notes.first()).toContainText('Test note newer')
  await expect(notes.first()).toContainText('Test Doctor — 17 November 2026')
  await expect(page.getByRole('button', { name: /edit|delete/i })).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('doctor notes: empty state', async ({ page }) => {
  await home(page)
  await page.route('**/api/v1/patient/doctor-notes', (route) =>
    route.fulfill({ json: { data: [], error: null } }),
  )
  await page.goto(`${PATIENT}/doctor-notes`)
  await expect(page.getByText('No notes from your doctor yet.')).toBeVisible()
  await expectNoA11yViolations(page)
})

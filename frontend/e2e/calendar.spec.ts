import { expect, test, type Page } from '@playwright/test'

import {
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  mockCalendar,
  PATIENT,
  signInAsPatient,
  testAppointment,
} from './helpers'

// Journey spec §9 (calendar, week strip, appointments) with obviously fake test titles.
// The browser clock is fixed so every day below is known.
const NOW = new Date('2026-11-17T10:00:00')

const DOCTOR_VISIT = testAppointment({
  id: '44444444-4444-4444-4444-444444444444',
  date: '2026-11-23',
  time: null,
  has_time: false,
  appointment_at: '2026-11-23T00:00:00+05:30',
  title: 'Test doctor visit',
  source: 'doctor',
  can_edit: false,
})

const CALENDAR = {
  start: '2026-05-04',
  end: '2027-02-22',
  milestones: [
    { date: '2026-11-23', kind: 'new_week', value: 29 },
    { date: '2026-11-23', kind: 'new_trimester', value: 3 },
  ],
  appointments: [testAppointment({ title: 'Test scan' }), DOCTOR_VISIT],
}

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

async function setUp(page: Page) {
  await page.clock.setFixedTime(NOW)
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) =>
    route.fulfill({ json: { data: ACTIVE_HOME, error: null } }),
  )
}

test('calendar month view shows markers and the tapped day details (§9.1-9.2)', async ({
  page,
}) => {
  await setUp(page)
  const asked: string[] = []
  await mockCalendar(page, CALENDAR)
  page.on('request', (r) => {
    if (r.url().includes('/journey/calendar?')) asked.push(new URL(r.url()).search)
  })
  await page.goto(`${PATIENT}/calendar`)

  await expect(page.getByRole('heading', { level: 1, name: 'Calendar' })).toBeVisible()
  expect(asked).toContain('?from=2026-11-01&to=2026-11-30') // the month on screen
  // markers are also in the day's accessible name, not only in the icons
  await expect(page.getByRole('button', { name: /^20 November 2026.*appointment/ })).toBeVisible()
  await expect(
    page.getByRole('button', { name: /^23 November 2026.*milestone, appointment/ }),
  ).toBeVisible()
  // today is selected at first and has nothing on it
  await expect(page.getByRole('heading', { name: '17 November 2026' })).toBeVisible()
  await expect(page.getByText('Nothing on this day.')).toBeVisible()
  await expectNoA11yViolations(page)

  await page.getByRole('button', { name: /^23 November 2026/ }).click()
  const details = page.getByRole('region', { name: '23 November 2026' })
  await expect(details.getByText('Week 29 begins')).toBeVisible()
  await expect(details.getByText('Trimester 3 begins')).toBeVisible()
  await expect(details.getByText('Test doctor visit')).toBeVisible()
  await expect(details.getByText('Added by your doctor')).toBeVisible()

  await page.getByRole('button', { name: /^20 November 2026/ }).click()
  await expect(page.getByText('10:30 am — Test scan')).toBeVisible()
  await expectNoA11yViolations(page)
})

test('calendar stops at the navigation range (§9.1: start .. due date + 2 weeks)', async ({
  page,
}) => {
  await setUp(page)
  await mockCalendar(page, { ...CALENDAR, end: '2026-11-30' })
  await page.goto(`${PATIENT}/calendar`)
  await expect(page.getByRole('button', { name: /next month/i })).toBeDisabled()
  await page.getByRole('button', { name: /previous month/i }).click()
  await expect(page.getByText('October 2026')).toBeVisible()
  await expect(page.getByText('Choose a day to see its details.')).toBeVisible()
})

test('home week strip marks today and opens the calendar on a day', async ({ page }) => {
  await setUp(page)
  await mockCalendar(page, CALENDAR)
  await page.goto(`${PATIENT}/home`)
  const week = page.getByRole('region', { name: 'This week' })
  await expect(week.getByRole('list').getByRole('link')).toHaveCount(7)
  await expect(week.getByRole('link', { name: 'Tue 17 November 2026' })).toHaveAttribute(
    'aria-current',
    'date',
  )
  await expect(week.getByRole('link', { name: 'Fri 20 November 2026, appointment' })).toBeVisible()
  await expectNoA11yViolations(page)
  await week.getByRole('link', { name: /21 November 2026/ }).click()
  await expect(page).toHaveURL(`${PATIENT}/calendar?day=2026-11-21`)
  await expect(page.getByRole('heading', { name: '21 November 2026' })).toBeVisible()
})

test('appointments: add, edit and delete her own; doctor-added ones are read-only (§9.3)', async ({
  page,
}) => {
  await setUp(page)
  // a small in-memory backend for the appointment routes
  let items = [DOCTOR_VISIT]
  const sent: unknown[] = []
  await page.route('**/api/v1/patient/appointments**', async (route) => {
    const req = route.request()
    const id = req.url().split('/appointments/')[1]
    if (req.method() === 'GET') {
      return route.fulfill({ json: { data: { upcoming: items, past: [] }, error: null } })
    }
    if (req.method() === 'DELETE') {
      items = items.filter((a) => a.id !== id)
      return route.fulfill({ json: { data: null, error: null } })
    }
    const body = req.postDataJSON() as Record<string, string | null>
    sent.push(body)
    const saved = testAppointment({
      id: id ?? '55555555-5555-5555-5555-555555555555',
      date: body.date,
      time: body.time ? `${body.time}:00` : null,
      has_time: Boolean(body.time),
      title: body.title,
      note: body.note,
    })
    items = id ? items.map((a) => (a.id === id ? saved : a)) : [...items, saved]
    return route.fulfill({ status: id ? 200 : 201, json: { data: saved, error: null } })
  })
  await page.goto(`${PATIENT}/appointments`)

  // doctor-added: labelled, no edit or delete
  await expect(page.getByText('Test doctor visit')).toBeVisible()
  await expect(page.getByText('Added by your doctor')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Edit Test doctor visit' })).toHaveCount(0)
  await expect(page.getByText('No past appointments.')).toBeVisible()
  await expectNoA11yViolations(page)

  // add: required fields first
  await page.getByRole('button', { name: 'Add an appointment' }).click()
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Please fill this in.')).toHaveCount(2)
  await expectNoA11yViolations(page)
  await page.getByLabel('Date').fill('2026-11-25')
  await page.getByLabel('Time (optional)').fill('09:15')
  await page.getByLabel('Title').fill('Test blood test')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Appointments' })).toBeVisible()
  await expect(page.getByText('25 November 2026, 9:15 am')).toBeVisible()
  expect(sent[0]).toEqual({
    date: '2026-11-25',
    time: '09:15',
    title: 'Test blood test',
    note: null,
  })

  // edit: the form starts with her values; clearing the time makes it date-only
  await page.getByRole('button', { name: 'Edit Test blood test' }).click()
  await expect(page.getByLabel('Title')).toHaveValue('Test blood test')
  await expect(page.getByLabel('Time (optional)')).toHaveValue('09:15')
  await page.getByLabel('Title').fill('Test blood test 2')
  await page.getByLabel('Time (optional)').fill('')
  await page.getByLabel('Note (optional)').fill('Test note')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByRole('heading', { name: 'Test blood test 2' })).toBeVisible()
  await expect(page.getByText('Test note')).toBeVisible()

  // delete asks first, and "Keep it" keeps it
  await page.getByRole('button', { name: 'Delete Test blood test 2' }).click()
  await expect(page.getByRole('alertdialog', { name: 'Delete this appointment?' })).toBeVisible()
  await page.getByRole('button', { name: 'Keep it' }).click()
  await page.getByRole('button', { name: 'Delete Test blood test 2' }).click()
  await page.getByRole('button', { name: 'Delete', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Test blood test 2' })).toHaveCount(0)
  await expect(page.getByText('Test doctor visit')).toBeVisible()
})

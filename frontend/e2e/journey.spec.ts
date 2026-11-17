import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, PATIENT, signInAsPatient } from './helpers'

const PENDING = '[Text pending doctor approval]'
const HOME_URL = '**/api/v1/patient/journey/home'
const DATES_URL = '**/api/v1/patient/journey/dates'

const PREGNANCY = {
  completed_weeks: 24,
  days: 3,
  days_to_go: 104,
  content_week: 24,
  trimester: 2,
  month: 6,
  is_estimate: true,
}
const ACTIVE = journeyHome({
  state: 'active',
  dates: { due_date: '2027-03-01', lmp_date: '2026-05-25', due_date_source: 'lmp_estimate' },
  pregnancy: PREGNANCY,
})

async function mockHome(page: Page, home: unknown) {
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: home, error: null } }))
}

test('onboarding: no dates, enter last period, home shows weeks and the estimate label', async ({
  page,
}) => {
  await signInAsPatient(page)
  // like the real backend: /home answers "no dates" until the dates are saved
  let current: unknown = journeyHome()
  await page.route(HOME_URL, (route) => route.fulfill({ json: { data: current, error: null } }))
  const sent: unknown[] = []
  await page.route(DATES_URL, async (route) => {
    sent.push(route.request().postDataJSON())
    current = ACTIVE
    await route.fulfill({ json: { data: ACTIVE, error: null } })
  })

  await page.goto(`${PATIENT}/home`)
  await expect(page.getByRole('heading', { name: 'Your pregnancy dates' })).toBeVisible()
  await expect(page.getByText(PENDING)).toBeVisible() // msg_onboarding is not approved yet
  await expectNoA11yViolations(page)

  await page.getByRole('link', { name: 'Enter your dates' }).click()
  await expect(page.getByRole('heading', { name: 'Pregnancy dates' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Skip for now' })).toBeVisible()
  await expect(page.getByRole('radio', { name: 'First day of my last period' })).toBeChecked()
  await expectNoA11yViolations(page)

  await page.getByRole('button', { name: 'Save dates' }).click()
  await expect(page.getByText('Please fill this in.')).toBeVisible()
  expect(sent).toEqual([]) // nothing is sent while a field is empty

  await page.getByLabel('First day of your last period').fill('2026-05-25')
  await page.getByRole('button', { name: 'Save dates' }).click()
  await expect(page).toHaveURL(`${PATIENT}/home`)
  expect(sent).toEqual([{ option: 'lmp', lmp_date: '2026-05-25', confirm_override: false }])
  await expect(page.getByRole('heading', { name: '24 weeks, 3 days pregnant' })).toBeVisible()
  await expect(page.getByText('104 days to go')).toBeVisible()
  await expect(page.getByText('Due date: 1 March 2027')).toBeVisible()
  await expect(page.getByText('estimate', { exact: true })).toBeVisible()
  await expectNoA11yViolations(page)
})

test('a date rule error is shown at its field (D1)', async ({ page }) => {
  await signInAsPatient(page)
  await mockHome(page, journeyHome())
  await page.route(DATES_URL, (route) =>
    route.fulfill({
      status: 400,
      json: {
        data: null,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Please check the dates.',
          fields: { scan_date: 'D1' },
        },
      },
    }),
  )
  await page.goto(`${PATIENT}/dates`)
  await page.getByRole('radio', { name: 'Ultrasound scan result' }).check()
  await page.getByLabel('Date of the scan').fill('2030-01-01')
  await page.getByLabel('Weeks at the scan').fill('12')
  await page.getByRole('button', { name: 'Save dates' }).click()
  await expect(page.getByLabel('Date of the scan')).toHaveAttribute('aria-invalid', 'true')
  await expect(page.getByText("This date can't be in the future.")).toBeVisible()
  await expect(page).toHaveURL(`${PATIENT}/dates`)
  await expectNoA11yViolations(page)
})

test('a doctor-set date is replaced by an estimate only after she confirms (spec 5.3)', async ({
  page,
}) => {
  await signInAsPatient(page)
  await mockHome(
    page,
    journeyHome({
      state: 'active',
      dates: { due_date: '2027-03-01', lmp_date: null, due_date_source: 'clinician_confirmed' },
      pregnancy: { ...PREGNANCY, is_estimate: false },
    }),
  )
  const sent: boolean[] = []
  await page.route(DATES_URL, async (route) => {
    const body = route.request().postDataJSON() as { confirm_override: boolean }
    sent.push(body.confirm_override)
    if (body.confirm_override) {
      await route.fulfill({ json: { data: ACTIVE, error: null } })
      return
    }
    await route.fulfill({
      status: 409,
      json: {
        data: null,
        error: {
          code: 'CONFLICT',
          message: 'Confirmation is needed to replace a date set by a doctor or a scan.',
          fields: { confirm_override: 'msg_confirm_override_clinician_date' },
        },
      },
    })
  })

  await page.goto(`${PATIENT}/dates`)
  await expect(page.getByText('Given by your doctor')).toBeVisible()
  await page.getByLabel('First day of your last period').fill('2026-05-25')
  await page.getByRole('button', { name: 'Save dates' }).click()

  await expect(page.getByRole('heading', { name: 'Change your pregnancy dates?' })).toBeVisible()
  await expect(page.getByRole('alertdialog')).toContainText(PENDING)
  await expectNoA11yViolations(page)
  expect(sent).toEqual([false])

  await page.getByRole('button', { name: 'Keep my current date' }).click()
  await expect(page.getByRole('heading', { name: 'Pregnancy dates' })).toBeVisible()
  expect(sent).toEqual([false]) // keeping the date sends nothing

  await page.getByRole('button', { name: 'Save dates' }).click()
  await page.getByRole('button', { name: 'Change my dates' }).click()
  await expect(page).toHaveURL(`${PATIENT}/home`)
  expect(sent).toEqual([false, false, true])
})

test('navigation shows the six items from the backend config (DEC-040)', async ({ page }) => {
  await signInAsPatient(page)
  await mockHome(page, ACTIVE)
  await page.goto(`${PATIENT}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  await expect(nav.getByRole('link')).toHaveText([
    'Home',
    'Calendar',
    'Log symptoms',
    'Appointments',
    'Doctor notes',
    'More',
  ])
  await nav.getByRole('link', { name: 'Doctor notes' }).click()
  await expect(page.getByRole('heading', { name: 'Doctor notes' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Urgent' })).toBeVisible() // on every screen
  await expectNoA11yViolations(page)
})

test('past 42 weeks the counter stops and the pending message is shown', async ({ page }) => {
  await signInAsPatient(page)
  await mockHome(
    page,
    journeyHome({
      state: 'beyond_42',
      dates: { due_date: '2026-10-20', lmp_date: null, due_date_source: 'clinician_confirmed' },
      pregnancy: { ...PREGNANCY, completed_weeks: 44, days: 0, days_to_go: null, content_week: 42 },
    }),
  )
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByRole('heading', { name: '42 weeks pregnant' })).toBeVisible()
  await expect(page.getByText('to go')).toHaveCount(0)
  // msg_beyond_42_weeks notice (the prototype banner also carries the pending text)
  await expect(page.getByRole('status').filter({ hasText: PENDING }).first()).toBeVisible()
})

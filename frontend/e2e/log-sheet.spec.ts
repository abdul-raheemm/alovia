import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// FRONTEND_REDESIGN §7.5 and §11 rules 8, 11, 12 (DEC-109). Mocked API, test strings only.
const PENDING = '[Text pending doctor approval]'
const VOCABULARY = {
  logging_open: true,
  pregnancy_week: 24,
  severities: { mild: 'Mild', moderate: 'Moderate', severe: 'Severe' },
  durations: { under_1_hour: 'Under 1 hour' },
  labour_durations: { under_12_hours: 'Under 12 hours', more_than_12_hours: 'More than 12 hours' },
  body_areas: {},
  common: [
    { id: 'headache', label: 'Headache', puqe: false, flags: {}, severity: true, duration: true },
  ],
  warning: [
    { id: 'fits', label: 'Fits / convulsions', labour_duration: false },
    { id: 'labour_pains', label: 'Labour pains / regular tightenings', labour_duration: true },
  ],
  puqe_questions: [],
  puqe_source: {
    publisher: 'P',
    title: 'T',
    url: 'https://example.test',
    date_accessed: '2026-11-18',
  },
  puqe_bands: [],
  draft_ttl_minutes: 30,
}
const HOME = journeyHome({
  state: 'active',
  dates: { due_date: '2027-02-08', lmp_date: '2026-05-04', due_date_source: 'lmp_estimate' },
  pregnancy: {
    completed_weeks: 24,
    days: 1,
    days_to_go: 110,
    content_week: 24,
    trimester: 2,
    month: 6,
    is_estimate: true,
  },
  months: MONTHS,
})

async function setUp(page: Page) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.route('**/api/v1/patient/symptoms/vocabulary', (r) =>
    r.fulfill({ json: { data: VOCABULARY, error: null } }),
  )
}

const sheet = (page: Page) => page.getByRole('dialog', { name: 'Log symptoms' })
const save = (page: Page) => sheet(page).getByRole('button', { name: 'Save check-in' })

test('sheet layout: full screen on the phone, right panel on the laptop; Save disabled until a choice', async ({
  page,
}) => {
  await setUp(page)
  let sent = 0
  await page.route('**/api/v1/patient/symptoms/checkins', (r) => {
    sent += 1
    return r.abort()
  })
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Log' }).click()
  await expect(sheet(page)).toBeVisible()
  await expect(sheet(page).getByText('Week 24')).toBeVisible()

  const view = page.viewportSize() ?? { width: 0, height: 0 }
  const box = await sheet(page).boundingBox()
  if (view.width >= 1024) {
    expect(Math.round(box?.width ?? 0)).toBe(480)
    expect(Math.round((box?.x ?? 0) + (box?.width ?? 0))).toBe(view.width)
  } else {
    // covers the whole screen, bottom bar included
    expect(box).toEqual({ x: 0, y: 0, width: view.width, height: view.height })
  }

  await expect(save(page)).toHaveAttribute('aria-disabled', 'true')
  // a tap on the disabled button still fires; force it, as Playwright waits on aria-disabled
  await save(page).click({ force: true })
  expect(sent).toBe(0) // V1: nothing chosen, nothing sent
  await expectNoA11yViolations(page)

  await page.keyboard.press('Escape')
  await expect(sheet(page)).toBeHidden()
  await expect(page).toHaveURL(`${PATIENT}/home`)
})

test('closing keeps the choices as a draft; reopening restores them; Clear drops them', async ({
  page,
}) => {
  await setUp(page)
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Log' }).click()
  await sheet(page).getByRole('checkbox', { name: 'Headache' }).check()
  await sheet(page).getByRole('radio', { name: 'Mild' }).check()
  await sheet(page).getByRole('button', { name: 'Close' }).click()
  await expect(page).toHaveURL(`${PATIENT}/home`)

  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Log' }).click()
  await expect(sheet(page).getByRole('status').filter({ hasText: 'Draft restored' })).toBeVisible()
  await expect(sheet(page).getByRole('checkbox', { name: 'Headache' })).toBeChecked()
  await expect(sheet(page).getByRole('radio', { name: 'Mild' })).toBeChecked()
  await expect(save(page)).not.toHaveAttribute('aria-disabled', 'true')
  await expectNoA11yViolations(page)

  await sheet(page).getByRole('button', { name: 'Clear' }).click()
  await expect(sheet(page).getByRole('checkbox', { name: 'Headache' })).not.toBeChecked()
  await page.reload()
  await expect(sheet(page).getByRole('checkbox', { name: 'Fits / convulsions' })).toBeVisible()
  await expect(sheet(page).getByText('Draft restored')).toHaveCount(0)
})

test('a failed save says it is not saved yet and keeps the draft (DEC-109)', async ({ page }) => {
  await setUp(page)
  await page.route('**/api/v1/patient/symptoms/checkins', (r) => r.abort())
  await page.goto(`${PATIENT}/log`)
  await sheet(page).getByRole('checkbox', { name: 'Headache' }).check()
  await sheet(page).getByRole('radio', { name: 'Mild' }).check()
  await sheet(page).getByRole('radio', { name: 'Under 1 hour' }).check()
  await save(page).click()
  // msg_not_saved has no approved text yet, so the pending placeholder is shown
  await expect(sheet(page).getByRole('alert')).toHaveText(PENDING, { timeout: 15_000 })
  await expect(sheet(page).getByRole('checkbox', { name: 'Headache' })).toBeChecked()
  await page.reload()
  await expect(sheet(page).getByText('Draft restored')).toBeVisible()
  await expect(sheet(page).getByRole('radio', { name: 'Under 1 hour' })).toBeChecked()
})

test('labour pains still asks for its duration (Symptom spec §5.2)', async ({ page }) => {
  await setUp(page)
  await page.goto(`${PATIENT}/log`)
  await sheet(page).getByRole('checkbox', { name: 'Labour pains / regular tightenings' }).check()
  await save(page).click()
  const duration = sheet(page).getByRole('group', { name: 'Duration' })
  await expect(duration.getByText('Please fill this in.')).toBeVisible()
  await expectNoA11yViolations(page)
})

import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// Journey spec §11 (UX_FLOWS P11). Message texts below are fake test strings, so each
// screen's message key can be told apart; real texts await doctor approval (DEC-041).
const PENDING = '[Text pending doctor approval]'
const MESSAGES = {
  msg_loss_support: 'TEST support message',
  msg_after_pregnancy_danger_signs: 'TEST safety message',
  msg_birth_congratulations: 'TEST birth message',
}

const ACTIVE = journeyHome({
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

function endedHome(status: string, undo_until: string | null, messages = {}) {
  const base = journeyHome({
    state: 'ended',
    dates: ACTIVE.dates,
    ended: { status, ended_at: '2026-11-17T05:00:00Z', undo_until },
  })
  return { ...base, messages: { ...base.messages, ...messages } }
}

async function withHome(page: Page, first: unknown) {
  let current = first
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) =>
    route.fulfill({ json: { data: current, error: null } }),
  )
  return (next: unknown) => {
    current = next
  }
}

test('end flow: choice, inform-doctor question with no default, confirmation (§11.2)', async ({
  page,
}) => {
  const setHome = await withHome(page, ACTIVE)
  let sent: unknown = null
  await page.route('**/api/v1/patient/pregnancy-end', (route) => {
    sent = route.request().postDataJSON()
    const after = endedHome('ended_loss', '2026-11-24T05:00:00Z')
    setHome(after)
    return route.fulfill({ json: { data: after, error: null } })
  })
  await page.goto(`${PATIENT}/more`)
  await page.getByRole('link', { name: 'My pregnancy has ended' }).click()
  await expect(page).toHaveURL(`${PATIENT}/pregnancy-end`)

  // step 1: the spec's three choices; nothing chosen yet
  for (const label of ['My baby was born', 'I have lost my pregnancy', 'I prefer not to say']) {
    await expect(page.getByRole('radio', { name: label })).not.toBeChecked()
  }
  await page.getByRole('button', { name: 'Continue' }).click()
  await expect(page.getByText('Please choose one.')).toBeVisible()
  await expectNoA11yViolations(page)
  await page.getByRole('radio', { name: 'I have lost my pregnancy' }).check()
  await page.getByRole('button', { name: 'Continue' }).click()

  // step 2: no default answer
  const question = page.getByRole('group', { name: 'Would you like your doctor to be informed?' })
  await expect(question.getByRole('radio', { name: 'Yes' })).not.toBeChecked()
  await expect(question.getByRole('radio', { name: 'No' })).not.toBeChecked()
  await page.getByRole('button', { name: 'Continue' }).click()
  await expect(page.getByText('Please choose one.')).toBeVisible()
  await question.getByRole('radio', { name: 'No' }).check()
  await page.getByRole('button', { name: 'Continue' }).click()

  // step 3: confirmation
  await expect(page.getByText('I have lost my pregnancy')).toBeVisible()
  await expect(page.getByText('Inform my doctor: No')).toBeVisible()
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Confirm' }).click()
  expect(sent).toEqual({ status: 'ended_loss', inform_doctor: false })

  // the quiet home (§11.4): support + safety messages, records, undo; no baby imagery
  await expect(page).toHaveURL(`${PATIENT}/home`)
  await expect(page.getByText(PENDING)).toHaveCount(2)
  await expect(page.getByRole('heading', { name: 'My records' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'I marked this by mistake' })).toBeVisible()
  await expect(page.getByRole('main').getByRole('img')).toHaveCount(0)
  await expect(page.getByText(/weeks pregnant|Month \d/)).toHaveCount(0)
  await expectNoA11yViolations(page)
})

test('after a loss: support and safety messages; after a birth: its own message (§11.4-11.5)', async ({
  page,
}) => {
  const setHome = await withHome(page, endedHome('ended_loss', null, MESSAGES))
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('TEST support message')).toBeVisible()
  await expect(page.getByText('TEST safety message')).toBeVisible()
  await expect(page.getByText('TEST birth message')).toHaveCount(0)
  // the undo window has passed: no undo button
  await expect(page.getByRole('button', { name: 'I marked this by mistake' })).toHaveCount(0)

  setHome(endedHome('ended_birth', null, MESSAGES))
  await page.reload()
  await expect(page.getByText('TEST birth message')).toBeVisible()
  await expect(page.getByText('TEST safety message')).toBeVisible()
  await expect(page.getByText('TEST support message')).toHaveCount(0)
  await expectNoA11yViolations(page)

  // the entry in More is gone once the pregnancy has ended
  await page.goto(`${PATIENT}/more`)
  await expect(page.getByRole('link', { name: 'Pregnancy dates' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'My pregnancy has ended' })).toHaveCount(0)
})

test('undo within the window asks first, then restores the normal home (§11.6)', async ({
  page,
}) => {
  const setHome = await withHome(page, endedHome('ended_not_specified', '2026-11-24T05:00:00Z'))
  let undone = false
  await page.route('**/api/v1/patient/pregnancy-end/undo', (route) => {
    undone = true
    setHome(ACTIVE)
    return route.fulfill({ json: { data: ACTIVE, error: null } })
  })
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('button', { name: 'I marked this by mistake' }).click()
  await expect(page.getByRole('alertdialog', { name: 'Undo this change?' })).toBeVisible()
  await page.getByRole('button', { name: 'Keep it' }).click()
  expect(undone).toBe(false)
  await page.getByRole('button', { name: 'I marked this by mistake' }).click()
  await page.getByRole('button', { name: 'Yes, undo' }).click()
  await expect(page.getByRole('heading', { name: '28 weeks, 1 day pregnant' })).toBeVisible()
  expect(undone).toBe(true)
})

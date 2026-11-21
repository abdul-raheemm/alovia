import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// Symptom spec §4 (UX_FLOWS P5, P6). Mocked API; option and question texts are test strings.
const PENDING = '[Text pending doctor approval]'
const VOCAB = '**/api/v1/patient/symptoms/vocabulary'
const CHECKINS = '**/api/v1/patient/symptoms/checkins'

const VOCABULARY = {
  logging_open: true,
  pregnancy_week: 24,
  severities: { mild: 'Mild', moderate: 'Moderate', severe: 'Severe' },
  durations: { under_1_hour: 'Under 1 hour', '1_to_6_hours': '1 to 6 hours' },
  labour_durations: { under_12_hours: 'Under 12 hours', more_than_12_hours: 'More than 12 hours' },
  body_areas: { upper_abdomen: 'Upper abdomen', lower_abdomen: 'Lower abdomen' },
  common: [
    { id: 'fatigue', label: 'Tiredness', puqe: false, flags: {}, severity: true, duration: true },
    {
      id: 'headache',
      label: 'Headache',
      puqe: false,
      flags: { with_swelling: 'With swelling' },
      severity: true,
      duration: true,
    },
    {
      id: 'nausea_vomiting',
      label: 'Nausea / vomiting',
      puqe: true,
      flags: { unable_to_keep_fluids: 'Unable to keep fluids' },
      severity: false,
      duration: false,
    },
    {
      id: 'mood_change',
      label: 'Mood change',
      puqe: false,
      flags: {},
      severity: true,
      duration: false,
    },
  ],
  warning: [
    {
      id: 'vaginal_bleeding',
      label: 'Bleeding from the vagina (any amount)',
      labour_duration: false,
    },
    { id: 'fits', label: 'Fits / convulsions', labour_duration: false },
    { id: 'labour_pains', label: 'Labour pains / regular tightenings', labour_duration: true },
  ],
  puqe_questions: ['Test question one', 'Test question two', 'Test question three'].map(
    (text, i) => ({
      id: `q${i}`,
      text,
      answers: {
        '1': `Test answer 1`,
        '2': 'Test answer 2',
        '3': 'Test answer 3',
        '4': 'Test answer 4',
        '5': 'Test answer 5',
      },
    }),
  ),
  puqe_source: {
    publisher: 'Test Publisher',
    title: 'Test PUQE sheet',
    url: 'https://example.test/puqe',
    date_accessed: '2026-11-18',
  },
  puqe_bands: [
    { band: 'mild', min: 3, max: 6 },
    { band: 'moderate', min: 7, max: 12 },
    { band: 'severe', min: 13, max: 15 },
  ],
  draft_ttl_minutes: 30,
}

const ACTIVE = journeyHome({
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

function result(level: string, keys: string[], rules: string[] = []) {
  return {
    checkin_id: '88888888-8888-8888-8888-888888888888',
    created_at: '2026-11-18T05:00:00Z',
    pregnancy_week: 24,
    red_flag_level: level,
    matched_rules: rules,
    message_keys: keys,
  }
}

async function setUp(page: Page, vocabulary: unknown = VOCABULARY) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) =>
    route.fulfill({ json: { data: ACTIVE, error: null } }),
  )
  await page.route(VOCAB, (route) => route.fulfill({ json: { data: vocabulary, error: null } }))
}

async function answerCheckin(page: Page, reply: unknown): Promise<() => unknown> {
  let sent: unknown = null
  await page.route(CHECKINS, (route) => {
    sent = route.request().postDataJSON()
    return route.fulfill({ status: 201, json: { data: reply, error: null } })
  })
  return () => sent
}

test('log an everyday symptom: details asked, saved (L0)', async ({ page }) => {
  await setUp(page)
  const sent = await answerCheckin(page, result('L0', ['msg_level0_logged']))
  await page.goto(`${PATIENT}/log`)
  await expect(page.getByRole('heading', { level: 1, name: 'Log symptoms' })).toBeVisible()
  // warning signs come first (§4.1), and the not-monitored notice is shown (§11.2)
  const headings = await page.getByRole('heading', { level: 2 }).allTextContents()
  expect(headings.slice(0, 2)).toEqual(['Warning signs', 'Everyday symptoms'])
  await expect(page.getByRole('note')).toHaveText(PENDING)

  await page.getByRole('checkbox', { name: 'Headache' }).check()
  await page.getByRole('button', { name: 'Save check-in' }).click()
  await expect(page.getByText('Please fill this in.')).toHaveCount(2) // severity, duration
  await expectNoA11yViolations(page)

  await page.getByRole('radio', { name: 'Mild' }).check()
  await page.getByRole('radio', { name: 'Under 1 hour' }).check()
  await page.getByLabel('Notes (optional)').fill('Test note')
  await page.getByRole('button', { name: 'Save check-in' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Saved' })).toBeVisible()
  expect(sent()).toEqual({
    source: 'form',
    entries: [
      { symptom: 'headache', severity: 'mild', duration: 'under_1_hour', notes: 'Test note' },
    ],
  })
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Done' }).click()
  await expect(page).toHaveURL(`${PATIENT}/home`)
})

test('a warning sign shows the L1 screen with the emergency number (UX P5)', async ({ page }) => {
  await setUp(page)
  await answerCheckin(page, result('L1', ['msg_level1_go_now'], ['L1-01']))
  await page.goto(`${PATIENT}/log`)
  await page.getByRole('checkbox', { name: 'Bleeding from the vagina (any amount)' }).check()
  await page.getByRole('button', { name: 'Save check-in' }).click()
  const advice = page.getByRole('alert')
  await expect(advice.getByRole('heading', { name: 'Go to hospital now' })).toBeVisible()
  await expect(advice.getByText(PENDING)).toBeVisible()
  await expect(advice.getByRole('link', { name: '108' })).toHaveAttribute('href', 'tel:108')
  await expect(advice.getByRole('link', { name: '102' })).toHaveAttribute('href', 'tel:102')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'I understand' }).click()
  await expect(page).toHaveURL(`${PATIENT}/home`)
})

test('PUQE questions and mood support with the national helpline', async ({ page }) => {
  await setUp(page)
  const sent = await answerCheckin(page, result('L0', ['msg_level0_logged', 'msg_mood_support']))
  await page.goto(`${PATIENT}/log`)
  await page.getByRole('checkbox', { name: 'Nausea / vomiting' }).check()
  // the PUQE questions open in their own sheet, with a live score band (FRONTEND_REDESIGN §7.5)
  const puqe = page.getByRole('dialog', { name: 'Nausea / vomiting' })
  await expect(puqe.getByRole('status')).toHaveText('0 of 3 questions answered')
  for (const [i, q] of [
    'Test question one',
    'Test question two',
    'Test question three',
  ].entries()) {
    await page
      .getByRole('group', { name: q })
      .getByRole('radio', { name: `Test answer ${i + 2}` })
      .check()
  }
  await expect(page.getByText('Questions: Test PUQE sheet (Test Publisher)')).toBeVisible()
  await expect(puqe.getByRole('status')).toHaveText('Score 9 of 15 (Moderate)')
  await expectNoA11yViolations(page)
  await puqe.getByRole('button', { name: 'Done' }).click()
  await expect(puqe).toBeHidden()
  await expect(page.getByText('Score 9 of 15 (Moderate)')).toBeVisible()
  await page.getByRole('checkbox', { name: 'Mood change' }).check()
  await page.getByRole('group', { name: 'Severity' }).getByRole('radio', { name: 'Mild' }).check()
  await page.getByRole('button', { name: 'Save check-in' }).click()
  expect(sent()).toEqual({
    source: 'form',
    entries: [
      { symptom: 'nausea_vomiting', puqe_answers: [2, 3, 4] },
      { symptom: 'mood_change', severity: 'mild' },
    ],
  })
  await expect(page.getByRole('link', { name: '14416', exact: true })).toHaveAttribute(
    'href',
    'tel:14416',
  )
  await expectNoA11yViolations(page)
})

test('urgent button: warning signs only, one tap + submit (UX P6)', async ({ page }) => {
  await setUp(page)
  const sent = await answerCheckin(page, result('L1', ['msg_level1_go_now'], ['L1-02']))
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('link', { name: 'Urgent' }).click()
  await expect(
    page.getByRole('heading', { level: 1, name: 'I have an urgent symptom' }),
  ).toBeVisible()
  await expect(page.getByRole('checkbox', { name: 'Headache' })).toHaveCount(0)
  await expectNoA11yViolations(page)
  await page.getByRole('checkbox', { name: 'Fits / convulsions' }).check()
  await page.getByRole('button', { name: 'Submit' }).click()
  await expect(page.getByRole('heading', { name: 'Go to hospital now' })).toBeVisible()
  expect(sent()).toEqual({ source: 'urgent_button', entries: [{ symptom: 'fits' }] })
})

test('urgent button works with the backend down: bundled list, L1 advice, sent later', async ({
  page,
}) => {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) => route.abort())
  await page.route(VOCAB, (route) => route.abort())
  let attempts = 0
  await page.route(CHECKINS, (route) => {
    attempts += 1
    return route.abort()
  })
  await page.goto(`${PATIENT}/urgent`)
  // the bundled list shows at once (all 15 warning signs when the week is unknown, §1.3)
  await page.getByRole('checkbox', { name: 'Severe itching' }).check()
  await page.getByRole('button', { name: 'Submit' }).click()
  // DEC-060: the stronger advice wins when the backend cannot answer
  await expect(page.getByRole('heading', { name: 'Go to hospital now' })).toBeVisible()
  await expect(
    page.getByText('Your answer will be sent when the connection is back.'),
  ).toBeVisible()
  await expect(page.getByRole('link', { name: '108' })).toBeVisible()
  expect(attempts).toBeGreaterThan(0)
})

test('after the pregnancy has ended, log and urgent show the after-pregnancy notice', async ({
  page,
}) => {
  await setUp(page, { ...VOCABULARY, logging_open: false })
  await page.goto(`${PATIENT}/log`)
  await expect(page.getByRole('heading', { level: 1, name: 'Log symptoms' })).toBeVisible()
  await expect(page.getByRole('checkbox')).toHaveCount(0)
  await expect(page.getByText(PENDING)).toBeVisible()
  await expectNoA11yViolations(page)
  await page.goto(`${PATIENT}/urgent`)
  await expect(
    page.getByRole('heading', { level: 1, name: 'I have an urgent symptom' }),
  ).toBeVisible()
  await expect(page.getByRole('checkbox')).toHaveCount(0)
})

test('symptom history: charts by pregnancy week with a table view; PUQE over time (§4.3)', async ({
  page,
}) => {
  await setUp(page)
  await page.route('**/api/v1/patient/symptoms/charts', (route) =>
    route.fulfill({
      json: {
        data: {
          symptoms: [
            {
              symptom: 'headache',
              label: 'Headache',
              points: [
                {
                  local_date: '2026-11-10',
                  pregnancy_week: 23,
                  severity: 'mild',
                  duration: 'under_1_hour',
                },
                {
                  local_date: '2026-11-17',
                  pregnancy_week: 24,
                  severity: 'severe',
                  duration: 'under_1_hour',
                },
              ],
            },
          ],
          puqe: [{ local_date: '2026-11-17', pregnancy_week: 24, score: 13, band: 'severe' }],
        },
        error: null,
      },
    }),
  )
  await page.goto(`${PATIENT}/log`)
  await page.getByRole('link', { name: 'Your symptom history' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Symptom history' })).toBeVisible()
  await expect(page.locator('.recharts-bar-rectangle').first()).toBeVisible()
  await expect(page.locator('.recharts-line')).toHaveCount(1)
  const headache = page.getByRole('heading', { name: 'Headache' }).locator('..')
  await headache.getByText('Show as a table').click()
  await expect(
    headache.getByRole('row', { name: /Week 24 1 Severe: 1 under 1 hour: 1/ }),
  ).toBeVisible()
  await expectNoA11yViolations(page)
})

test('symptom history: empty state', async ({ page }) => {
  await setUp(page)
  await page.route('**/api/v1/patient/symptoms/charts', (route) =>
    route.fulfill({ json: { data: { symptoms: [], puqe: [] }, error: null } }),
  )
  await page.goto(`${PATIENT}/log/history`)
  await expect(page.getByText('Nothing logged yet.')).toBeVisible()
  await expectNoA11yViolations(page)
})

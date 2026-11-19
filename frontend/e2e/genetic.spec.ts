import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, PATIENT, signInAsPatient } from './helpers'

// Genetic spec §4.1 (UX_FLOWS P9). Mocked API; notes are test strings.
const PENDING = '[Text pending doctor approval]'
const DISCLAIMER =
  'This is for knowledge only and is not medical advice. Counselling is recommended.'
const URL = '**/api/v1/patient/genetic/assessments'

function assessment(over: Record<string, unknown> = {}) {
  return {
    assessment_id: '99999999-9999-9999-9999-999999999999',
    created_at: '2026-11-19T05:00:00Z',
    rules_version: '1.0.0',
    review_status: 'pending_review',
    show_numbers_to_patient: true,
    conditions: [
      {
        condition: 'haemoglobin_group',
        rule_id: 'HBB-16',
        status: 'needs_testing_or_counselling',
        outcomes: null,
        outcomes_if_boy: null,
        outcomes_if_girl: null,
        message_keys: ['msg_needs_testing', 'msg_partner_test_suggested'],
        warnings: [],
        notes: [],
      },
      {
        condition: 'haemophilia',
        rule_id: 'HEM-02',
        status: 'calculated',
        outcomes: null,
        outcomes_if_boy: [
          { outcome: 'haemophilia', chance: '1_in_2', percent: 50 },
          { outcome: 'unaffected', chance: '1_in_2', percent: 50 },
        ],
        outcomes_if_girl: [
          { outcome: 'carrier', chance: '1_in_2', percent: 50 },
          { outcome: 'neither', chance: '1_in_2', percent: 50 },
          { outcome: 'haemophilia', chance: 'not_expected', percent: null },
        ],
        message_keys: ['result_hem_calculated'],
        warnings: [],
        notes: ['note_carrier_girls_may_bleed'],
      },
      {
        condition: 'marfan',
        rule_id: null,
        status: 'not_assessed',
        outcomes: null,
        outcomes_if_boy: null,
        outcomes_if_girl: null,
        message_keys: ['msg_not_assessed'],
        warnings: [],
        notes: [],
      },
    ],
    flags: { consanguinity: false, risk_indicated: true, timing_prompt: true },
    message_keys: ['msg_speak_to_doctor_soon', 'review_with_doctor'],
    disclaimer_key: 'disclaimer_main',
    doctor_note: null,
    reviewed_at: null,
    inputs: {},
    ...over,
  }
}

async function setUp(page: Page, list: unknown[], home = journeyHome()) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (route) =>
    route.fulfill({ json: { data: home, error: null } }),
  )
  let sent: unknown = null
  await page.route(URL, (route) => {
    if (route.request().method() === 'POST') {
      sent = route.request().postDataJSON()
      return route.fulfill({ status: 201, json: { data: assessment(), error: null } })
    }
    return route.fulfill({ json: { data: list, error: null } })
  })
  return () => sent
}

test('genetic form: consent reminder, entry questions, evidence by status, exact request', async ({
  page,
}) => {
  const sent = await setUp(page, [])
  await page.goto(`${PATIENT}/more`)
  await page.getByRole('link', { name: 'Genetic risk' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Genetic risk' })).toBeVisible()
  await expect(page.getByText('This form also asks about your husband.')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Read the consent text' })).toBeVisible()

  await page.getByRole('button', { name: 'Submit' }).click()
  await expect(page.getByText('Please answer this.')).toHaveCount(5)
  await expectNoA11yViolations(page)

  const hbb = page.getByRole('region', { name: /Haemoglobin conditions/ })
  const mother = hbb.getByRole('group', { name: 'You (the mother)' })
  await mother.getByLabel('Status').selectOption('beta_thal_carrier')
  // §5.4: the sickle card is not offered with a β-thalassaemia status
  const how = mother.getByLabel('How do you know?')
  await expect(
    how.locator('option', { hasText: 'National sickle cell genetic status card' }),
  ).toHaveCount(0)
  await how.selectOption('hplc_report')
  // D14: the father starts as unknown, so no evidence is asked
  const father = hbb.getByRole('group', { name: 'Your husband (the father)' })
  await expect(father.getByLabel('Status')).toHaveValue('unknown')
  await expect(father.getByLabel('How do you know?')).toHaveCount(0)
  await hbb.getByRole('radio', { name: 'No', exact: true }).check()

  const hem = page.getByRole('region', { name: 'Haemophilia' })
  await hem.getByRole('radio', { name: 'Yes', exact: true }).first().check()
  // DEC-069: no pre-selected answer for the father's haemophilia status
  await expect(
    hem.getByRole('group', { name: 'Your husband (the father)' }).getByLabel('Status'),
  ).toHaveValue('')
  await hem.getByRole('radio', { name: 'No', exact: true }).first().check()
  await expect(hem.getByRole('group', { name: 'You (the mother)' })).toHaveCount(0)

  await page
    .getByRole('region', { name: 'Marfan syndrome' })
    .getByRole('radio', { name: 'No', exact: true })
    .check()
  await page
    .getByRole('group', { name: /related by blood/ })
    .getByRole('radio', { name: 'Not sure' })
    .check()
  await page.getByRole('button', { name: 'Submit' }).click()

  await expect(page.getByRole('heading', { name: /Your result/ })).toBeVisible()
  expect(sent()).toEqual({
    haemoglobin_group: {
      mother: { status: 'beta_thal_carrier', evidence: 'hplc_report' },
      father: { status: 'unknown' },
      previous_child: 'no',
    },
    haemophilia: { entry: 'no' },
    marfan: { entry: 'no' },
    consanguinity: 'not_sure',
  })
})

test('result: boy and girl shown together, never 0%, disclaimer, next steps (§11)', async ({
  page,
}) => {
  await setUp(page, [assessment()])
  await page.goto(`${PATIENT}/genetic`)
  await expect(page.getByRole('note')).toHaveText(DISCLAIMER)
  const hem = page.getByRole('heading', { name: 'Haemophilia', level: 3 }).locator('..')
  await expect(hem.getByRole('heading', { name: 'If the baby is a boy' })).toBeVisible()
  await expect(hem.getByRole('heading', { name: 'If the baby is a girl' })).toBeVisible()
  await expect(hem.getByText('Haemophilia: 1 in 2 (50%)')).toBeVisible()
  await expect(hem.getByText('Haemophilia: not expected')).toBeVisible()
  expect(await page.getByRole('main').innerText()).not.toMatch(/(^|[^0-9])0%/) // visible text only
  await expect(page.getByText(PENDING).first()).toBeVisible()
  await expectNoA11yViolations(page)
})

test('numbers are hidden until review when the setting is off; the doctor note stands apart', async ({
  page,
}) => {
  const hidden = assessment({
    show_numbers_to_patient: false,
    message_keys: ['results_after_review'],
  })
  const conditions = (hidden.conditions as Record<string, unknown>[]).map((c) => ({
    ...c,
    outcomes_if_boy: null,
    outcomes_if_girl: null,
  }))
  await setUp(page, [{ ...hidden, conditions }])
  await page.goto(`${PATIENT}/genetic`)
  await expect(page.getByText('If the baby is a boy')).toHaveCount(0)
  await expect(page.getByText(/in 2 \(50%\)/)).toHaveCount(0)

  await page.unrouteAll({ behavior: 'ignoreErrors' })
  await setUp(page, [
    assessment({
      review_status: 'reviewed',
      reviewed_at: '2026-11-20T05:00:00Z',
      doctor_note: 'Test doctor note',
    }),
  ])
  await page.reload()
  await expect(page.getByText('From your doctor')).toBeVisible()
  await expect(page.getByText('Test doctor note')).toBeVisible()
  await expectNoA11yViolations(page)
})

test('home shows the Genetic check card linking to the page (Journey §10.4)', async ({ page }) => {
  await setUp(page, [assessment()], journeyHome({ genetic_check: 'needs_testing' }))
  await page.goto(`${PATIENT}/home`)
  await page.getByRole('link', { name: 'Genetic check: Needs testing' }).click()
  await expect(page).toHaveURL(`${PATIENT}/genetic`)
})

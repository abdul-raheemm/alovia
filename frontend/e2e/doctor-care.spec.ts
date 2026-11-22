import { expect, test, type Page } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsDoctor } from './helpers'

const PID = 'aaaaaaaa-0000-0000-0000-000000000004'
const AID = 'eeeeeeee-0000-0000-0000-000000000001'
const AT = '2026-11-19T05:00:00Z'

function patient(over: Record<string, unknown> = {}) {
  return {
    id: PID,
    name: 'Test Patient D',
    linked: true,
    ga_weeks: 24,
    ga_days: 2,
    due_date: '2027-03-01',
    fetal: null,
    maternal: null,
    genetic: null,
    symptom: null,
    unseen_count: 0,
    pregnancy_status: 'active',
    group: 4,
    age: 30,
    notes: null,
    due_date_source: 'lmp_estimate',
    doctors: [
      { id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', is_primary: true },
    ],
    hba1c_note: false,
    ...over,
  }
}

const INPUTS = {
  haemoglobin_group: {
    mother: { status: 'beta_thal_carrier', evidence: 'hplc_report' },
    father: { status: 'unknown' },
    previous_child: 'no',
  },
  haemophilia: { entry: 'no' },
  marfan: { entry: 'no' },
  consanguinity: 'no',
}

function assessment(over: Record<string, unknown> = {}) {
  return {
    id: AID,
    patient_id: PID,
    patient_name: 'Test Patient D',
    created_at: AT,
    rules_version: '1.0.0',
    review_status: 'pending_review',
    priority: 'high',
    risk_indicated: true,
    result: {
      rules_version: '1.0.0',
      conditions: [
        {
          condition: 'haemoglobin_group',
          status: 'needs_testing_or_counselling',
          rule_id: 'HBB-03',
          outcomes: null,
          outcomes_if_boy: null,
          outcomes_if_girl: null,
          message_keys: [],
          warnings: [],
          notes: [],
        },
      ],
      flags: { risk_indicated: true, counselling_recommended: true, consanguinity: false },
      priority: 'high',
      show_numbers_to_patient: false,
      message_keys: [],
      disclaimer_key: 'disclaimer_main',
    },
    inputs: INPUTS,
    doctor_note: null,
    reviewed_at: null,
    reviewed_by_name: null,
    supersedes_id: null,
    replaced: false,
    by_doctor: false,
    ...over,
  }
}

async function json(page: Page, url: string, data: unknown, status = 200) {
  await page.route(url, (route) => route.fulfill({ status, json: { data, error: null } }))
}

test('genetic review: queue, confirm with a note, and correct inputs', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, '**/api/v1/doctor/genetic/review-queue', [assessment()])
  await json(page, `**/api/v1/doctor/patients/${PID}`, patient())
  await json(page, `**/api/v1/doctor/patients/${PID}/genetic`, [assessment()])
  let confirmed: unknown = null
  await page.route(`**/api/v1/doctor/genetic/assessments/${AID}/review`, (route) => {
    confirmed = route.request().postDataJSON()
    return route.fulfill({
      status: 409,
      json: { data: null, error: { code: 'CONFLICT', message: 'Already reviewed by Dr Test.' } },
    })
  })
  let corrected: unknown = null
  await page.route(`**/api/v1/doctor/genetic/assessments/${AID}/correct`, (route) => {
    corrected = route.request().postDataJSON()
    return route.fulfill({ status: 201, json: { data: assessment(), error: null } })
  })

  await page.goto(`${DOCTOR}/genetic-review`)
  await expect(page.getByText('High priority')).toBeVisible()
  await expectNoA11yViolations(page)
  await page.getByRole('link', { name: 'Test Patient D' }).click()
  await expect(page).toHaveURL(`${DOCTOR}/patients/${PID}/genetic`)
  await expect(page.getByText('rule HBB-03')).toBeVisible()

  await page.getByRole('button', { name: 'Confirm with note' }).click()
  await page.getByRole('button', { name: 'Confirm review' }).click()
  await expect(page.getByText('Please write a note.')).toBeVisible()
  await page.getByLabel(/Doctor's note/).fill(' Test review ')
  await page.getByRole('button', { name: 'Confirm review' }).click()
  expect(confirmed).toEqual({ doctor_note: 'Test review' })
  await expect(page.getByText('Already reviewed by Dr Test.')).toBeVisible() // second doctor
  await page.getByRole('button', { name: 'Cancel' }).click()

  await page.getByRole('button', { name: 'Correct inputs' }).click()
  await page.getByLabel('Father: status').selectOption('tested_negative')
  await page.getByLabel('Father: evidence').selectOption('hplc_report')
  await page.getByLabel("Doctor's note (required)").fill('Father tested')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Save correction' }).click()
  expect(corrected).toEqual({
    inputs: {
      ...INPUTS,
      haemoglobin_group: {
        ...INPUTS.haemoglobin_group,
        father: { status: 'tested_negative', evidence: 'hplc_report' },
      },
    },
    doctor_note: 'Father tested',
  })
})

test('symptoms tab: levels, rule IDs, pattern badges and notes in full', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, `**/api/v1/doctor/patients/${PID}`, patient())
  await json(page, `**/api/v1/doctor/patients/${PID}/symptoms`, {
    checkins: [
      {
        checkin_id: 'c1',
        created_at: AT,
        pregnancy_week: 24,
        red_flag_level: 'L2',
        matched_rules: ['L2-07'],
        message_keys: [],
        source: 'form',
        local_date: '2026-11-19',
        entries: [
          {
            symptom: 'headache',
            severity: 'moderate',
            duration: 'over_24_hours',
            body_area: null,
            details: null,
            occurred_at: null,
            notes: 'Test note text',
          },
        ],
        pattern_changes: [{ code: 'P1', symptom: 'headache' }],
      },
    ],
    charts: {
      symptoms: [
        {
          symptom: 'headache',
          label: 'Headache',
          points: [
            {
              local_date: '2026-11-19',
              pregnancy_week: 24,
              severity: 'moderate',
              duration: 'over_24_hours',
            },
          ],
        },
      ],
      puqe: [],
    },
    labels: { headache: 'Headache' },
    puqe_bands: [{ band: 'mild', min: 3, max: 6 }],
  })
  await page.goto(`${DOCTOR}/patients/${PID}/symptoms`)
  await expect(page.getByText('Level L2')).toBeVisible()
  await expect(page.getByText('Rules: L2-07')).toBeVisible()
  await expect(page.getByRole('list', { name: 'Pattern changes' })).toContainText('P1: Headache')
  await expect(page.getByText('Note: Test note text')).toBeVisible()
  await expectNoA11yViolations(page)
})

test('notes, appointments and pregnancy tabs', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, `**/api/v1/doctor/patients/${PID}`, patient())
  let notes = [
    {
      id: 'n1',
      body: 'Private test note',
      visible_to_patient: false,
      doctor_name: 'Test Doctor',
      created_at: AT,
      related_ref: null,
    },
  ]
  await page.route(`**/api/v1/doctor/patients/${PID}/notes`, (route) => {
    if (route.request().method() === 'POST') {
      return route.fulfill({ status: 201, json: { data: notes[0], error: null } })
    }
    return route.fulfill({ json: { data: notes, error: null } })
  })
  await page.route('**/api/v1/doctor/notes/n1/share', (route) => {
    notes = notes.map((n) => ({ ...n, visible_to_patient: true }))
    return route.fulfill({ json: { data: notes[0], error: null } })
  })
  await page.goto(`${DOCTOR}/patients/${PID}/notes`)
  await expect(page.getByText('Private', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Share with patient' }).click()
  await expect(page.getByText('Shared with the patient')).toBeVisible()
  await expectNoA11yViolations(page)

  const appt = (id: string, source: string) => ({
    id,
    appointment_at: '2026-12-01T10:30:00+05:30',
    has_time: true,
    date: '2026-12-01',
    time: '10:30:00',
    title: `${source} visit`,
    note: null,
    source,
    can_edit: source === 'doctor',
  })
  await json(page, `**/api/v1/doctor/patients/${PID}/appointments`, {
    upcoming: [appt('a1', 'doctor'), appt('a2', 'patient')],
    past: [],
  })
  await page.goto(`${DOCTOR}/patients/${PID}/appointments`)
  await expect(page.getByText('Added by the patient')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Edit' })).toHaveCount(1) // own only (§16)
  await expectNoA11yViolations(page)

  let dates: unknown = null
  await page.route(`**/api/v1/doctor/patients/${PID}/dates`, (route) => {
    dates = route.request().postDataJSON()
    return route.fulfill({ json: { data: patient(), error: null } })
  })
  await page.goto(`${DOCTOR}/patients/${PID}/pregnancy`)
  // the source shows in the header card and in the tab's own dates section
  await expect(page.getByText('(LMP estimate)')).toHaveCount(2)
  await expect(page.locator('main').getByText('(LMP estimate)').last()).toBeVisible()
  await page.getByLabel('Due date', { exact: true }).fill('2027-03-05')
  await page.getByRole('button', { name: 'Save dates' }).click()
  await expect.poll(() => dates).toEqual({ option: 'due_date', due_date: '2027-03-05' })
  await page.getByLabel('Ended (loss)').check()
  await page.getByRole('button', { name: 'Set pregnancy ended' }).click()
  await expect(page.getByRole('button', { name: 'Confirm: pregnancy ended' })).toBeVisible()
  await expectNoA11yViolations(page)
})

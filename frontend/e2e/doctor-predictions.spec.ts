import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  expectNoA11yViolations,
  journeyHome,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
} from './helpers'

const PID = 'aaaaaaaa-0000-0000-0000-000000000009'
const AT = '2026-11-19T05:00:00Z'
const HBA1C = 'Blood Glucose(HbA1c mmol/mol)'

const SCHEMA = {
  model: 'maternal',
  groups: [
    {
      label: 'Vitals',
      fields: [{ feature: 'Age', label: 'Age (years)', range: { min: 15, max: 48 }, unit: null }],
    },
    {
      label: 'Metabolic',
      fields: [
        {
          feature: HBA1C,
          label: 'HbA1c',
          range: { min: 20, max: 120 },
          unit: { name: 'hba1c', model_unit: 'mmol/mol', other_unit: '%', default: '%' },
        },
      ],
    },
  ],
  limitation_keys: ['lim_decision_support', 'lim_public_data', 'lim_maternal_separable'],
  messages: {},
  conversions: {
    hba1c: { multiply: 10.93, divide: 1, add: -23.5 },
    glucose: { multiply: 1, divide: 18, add: 0 },
    temperature: { multiply: 9, divide: 5, add: 32 },
  },
}

function result(over: Record<string, unknown> = {}) {
  return {
    id: 'cccccccc-0000-0000-0000-000000000001',
    model: 'maternal',
    created_at: AT,
    predicted_class: 'Mid',
    confidence: 0.82,
    class_probabilities: { Low: 0.1, Mid: 0.82, High: 0.08 },
    top_contributing_factors: [
      { feature: HBA1C, impact: 1.2345, direction: "supports 'Mid' prediction" },
    ],
    input_values: { Age: 50, [HBA1C]: 53.01 },
    entered_values: { Age: { value: 50, unit: null }, [HBA1C]: { value: 7, unit: '%' } },
    range_warnings: ['Age'],
    model_version: 'XGBoost 2026-09-17',
    entered_by_name: 'Test Doctor',
    hba1c_note: true,
    share: null,
    ...over,
  }
}

function patient() {
  return {
    id: PID,
    name: 'Test Patient C',
    linked: true,
    ga_weeks: 24,
    ga_days: 0,
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
    due_date_source: null,
    doctors: [
      { id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', is_primary: true },
    ],
    hba1c_note: true,
  }
}

async function json(page: Page, url: string, data: unknown, status = 200) {
  await page.route(url, (route) => route.fulfill({ status, json: { data, error: null } }))
}

test('doctor: enter vitals with a unit switch, see the result, share it', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, `**/api/v1/doctor/patients/${PID}`, patient())
  await json(page, '**/api/v1/doctor/predictions/schema/maternal', SCHEMA)
  let history: unknown[] = []
  await page.route(`**/api/v1/doctor/patients/${PID}/predictions?model=maternal`, (route) =>
    route.fulfill({ json: { data: history, error: null } }),
  )
  await json(page, `**/api/v1/doctor/patients/${PID}/trends`, {
    maternal_features: ['Age', HBA1C],
    fetal_features: ['LB'],
    maternal: [],
    fetal: [],
  })
  let sent: unknown = null
  await page.route(`**/api/v1/doctor/patients/${PID}/predictions/maternal`, (route) => {
    sent = route.request().postDataJSON()
    history = [result()]
    return route.fulfill({ status: 201, json: { data: result(), error: null } })
  })
  let shareBody: unknown = null
  await page.route('**/api/v1/doctor/predictions/maternal/*/share', (route) => {
    shareBody = route.request().postDataJSON()
    const shared = result({
      share: {
        shared_at: AT,
        shared_by_name: 'Test Doctor',
        template_key: 'result_template_maternal_mid',
        doctor_message: 'Test message',
      },
    })
    history = [shared]
    return route.fulfill({ status: 201, json: { data: shared, error: null } })
  })

  await page.goto(`${DOCTOR}/patients/${PID}/maternal`)
  await expect(page.getByRole('heading', { name: 'Enter vitals' })).toBeVisible()
  await expect(page.getByText('[Text pending doctor approval]').first()).toBeVisible() // HbA1c note
  await page.getByLabel('Age (years)').fill('50')
  await expect(page.getByText('[Text pending doctor approval]')).toHaveCount(2) // + range warning
  await page.getByLabel('HbA1c').fill('7.0')
  await expect(page.getByText('7 % = 53.01 mmol/mol')).toBeVisible() // §9.3 preview
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Run prediction' }).click()
  expect(sent).toEqual({ values: { Age: 50, [HBA1C]: 7 }, units: { hba1c: '%' } })

  await expect(page.getByRole('heading', { name: 'Predicted class: Mid' })).toBeVisible()
  await expect(page.getByText('82%').first()).toBeVisible()
  await expect(page.getByRole('cell', { name: "supports 'Mid' prediction" })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Limitations' })).toBeVisible()
  await expectNoA11yViolations(page)

  await page.getByRole('button', { name: 'Share with patient' }).click()
  await expect(page.getByText('What the patient will see')).toBeVisible()
  await page.getByLabel('Message to the patient (optional)').fill(' Test message ')
  await page.getByRole('button', { name: 'Confirm and share' }).click()
  expect(shareBody).toEqual({ doctor_message: 'Test message' })
  await expect(page.getByText(/^Shared with the patient on/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Share with patient' })).toHaveCount(0)
})

test('doctor: trends draw a chart per input with the class as text', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, `**/api/v1/doctor/patients/${PID}`, patient())
  await json(page, '**/api/v1/doctor/predictions/schema/maternal', SCHEMA)
  await json(page, `**/api/v1/doctor/patients/${PID}/predictions?model=maternal`, [result()])
  const point = (id: string, cls: string, a: number) => ({
    result_id: id,
    created_at: AT,
    ga_week: 24,
    predicted_class: cls,
    values: { Age: 30, [HBA1C]: a },
  })
  await json(page, `**/api/v1/doctor/patients/${PID}/trends`, {
    maternal_features: ['Age', HBA1C],
    fetal_features: ['LB'],
    maternal: [point('p1', 'Low', 40), point('p2', 'High', 60)],
    fetal: [],
  })
  await page.goto(`${DOCTOR}/patients/${PID}/maternal`)
  await expect(page.getByRole('heading', { name: 'Trends' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 4, name: 'HbA1c' })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'High' })).toBeAttached() // table view of the chart
  await expectNoA11yViolations(page)
})

test('patient: My results shows only the shared text and message', async ({ page }) => {
  await signInAsPatient(page)
  await json(page, '**/api/v1/patient/journey/home', journeyHome())
  await json(page, '**/api/v1/patient/results', [
    {
      id: 'dddddddd-0000-0000-0000-000000000001',
      result_type: 'maternal',
      result_date: AT,
      shared_at: AT,
      template_key: 'result_template_maternal_mid',
      template_text: null,
      doctor_message: 'Test message',
      doctor_name: 'Test Doctor',
    },
  ])
  await page.goto(`${PATIENT}/more`)
  await page.getByRole('link', { name: 'My results' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'My results' })).toBeVisible()
  await expect(page.getByText('[Text pending doctor approval]')).toBeVisible()
  await expect(page.getByText('Message from Test Doctor')).toBeVisible()
  await expect(page.getByText(/%|confidence|probabilit/i)).toHaveCount(0)
  await expectNoA11yViolations(page)
})

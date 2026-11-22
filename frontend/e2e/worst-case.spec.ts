import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  journeyHome,
  MONTHS,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
  testAppointment,
} from './helpers'

// Step 8 harden: worst-case data never widens the page on a 375 px phone (synthetic name).
const LONG = 'Venkatalakshminarasimhaswamyreddygaripallisrinivasaraghavendraprasad'
const AT = '2026-11-19T05:00:00Z'
const ROW = {
  id: '00000000-0000-0000-0000-000000000001',
  name: LONG,
  linked: false,
  ga_weeks: 41,
  ga_days: 6,
  due_date: '2027-03-01',
  fetal: { predicted_class: 'Pathological', created_at: AT },
  maternal: { predicted_class: 'High', created_at: AT },
  genetic: { review_status: 'pending', priority: 'high', created_at: AT },
  symptom: { level: 'L1', created_at: AT },
  unseen_count: 1234,
  pregnancy_status: 'ended_not_specified',
  group: 1,
}
const fits = async (page: Page) =>
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(375)

test.use({ viewport: { width: 375, height: 800 } })

test('doctor screens with a very long name and big counts stay within the screen', async ({
  page,
}) => {
  await signInAsDoctor(page)
  const json = (url: string, data: unknown) =>
    page.route(url, (r) => r.fulfill({ json: { data, error: null } }))
  await json('**/api/v1/doctor/patients', [ROW])
  await json(`**/api/v1/doctor/patients/${ROW.id}`, {
    ...ROW,
    age: 45,
    notes: LONG,
    due_date_source: 'clinician_confirmed',
    doctors: [],
    hba1c_note: false,
  })
  await json('**/api/v1/doctor/inbox', [
    {
      id: 'a',
      patient_id: ROW.id,
      patient_name: LONG,
      type: 'chat_urgent',
      ref_table: null,
      ref_id: null,
      created_at: AT,
      seen_at: null,
      seen_by_name: null,
    },
  ])
  for (const path of ['/home', '/patients', `/patients/${ROW.id}`]) {
    await page.goto(`${DOCTOR}${path}`)
    await expect(page.getByText(LONG).first()).toBeVisible()
    await fits(page)
  }
})

test('patient screens with a very long appointment title stay within the screen', async ({
  page,
}) => {
  await signInAsPatient(page)
  const home = journeyHome({
    state: 'active',
    dates: { due_date: '2027-03-01', lmp_date: '2026-05-25', due_date_source: 'lmp_estimate' },
    pregnancy: {
      completed_weeks: 24,
      days: 3,
      days_to_go: 104,
      content_week: 24,
      trimester: 2,
      month: 6,
      is_estimate: true,
    },
    months: MONTHS,
    next_appointment: testAppointment({ title: `${LONG} ${LONG}` }),
  })
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: home, error: null } }),
  )
  await page.route('**/api/v1/patient/appointments', (r) =>
    r.fulfill({
      json: { data: { upcoming: [testAppointment({ title: LONG })], past: [] }, error: null },
    }),
  )
  for (const path of ['/home', '/appointments']) {
    await page.goto(`${PATIENT}${path}`)
    await expect(page.getByText(LONG).first()).toBeVisible()
    await fits(page)
  }
})

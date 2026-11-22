import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  journeyHome,
  MONTHS,
  mockCalendar,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
  testAppointment,
  testContentItem,
} from './helpers'

// FRONTEND_REDESIGN §13 "Visual snapshots": key screens at 375 and 1280 px, light and dark,
// compared with the stored images in snapshots.spec.ts-snapshots/. The images are made on
// Windows; another OS (e.g. Linux CI) needs its own set (npx playwright test snapshots
// --update-snapshots). Fixed clock and no motion, so runs are repeatable.
const NOW = new Date('2026-11-17T10:00:00')
const AT = '2026-11-16T05:00:00Z'
const PID = '00000000-0000-0000-0000-000000000001'
const HOME = journeyHome({
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
  stage_items: [testContentItem()],
  next_appointment: testAppointment({ title: 'Check-up' }),
})
const VOCAB = {
  logging_open: true,
  pregnancy_week: 28,
  severities: { mild: 'Mild', moderate: 'Moderate', severe: 'Severe' },
  durations: { under_1_hour: 'Under 1 hour' },
  labour_durations: {},
  body_areas: {},
  common: [
    { id: 'fatigue', label: 'Tiredness', puqe: false, flags: {}, severity: true, duration: true },
    { id: 'headache', label: 'Headache', puqe: false, flags: {}, severity: true, duration: true },
  ],
  warning: [
    { id: 'fits', label: 'Fits / convulsions', labour_duration: false },
    { id: 'high_fever', label: 'High fever', labour_duration: false },
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
const ROW = {
  id: PID,
  name: 'Test Patient A',
  linked: true,
  ga_weeks: 28,
  ga_days: 1,
  due_date: '2027-02-08',
  fetal: { predicted_class: 'Suspect', created_at: AT },
  maternal: null,
  genetic: null,
  symptom: { level: 'L2', created_at: AT },
  unseen_count: 1,
  pregnancy_status: 'active',
  group: 2,
}

async function patient(page: Page) {
  await signInAsPatient(page)
  await mockCalendar(page, {
    start: '2026-05-04',
    end: '2027-02-22',
    symptom_days: [{ date: '2026-11-12', levels: ['L0', 'L2'] }],
  })
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.route('**/api/v1/patient/symptoms/vocabulary', (r) =>
    r.fulfill({ json: { data: VOCAB, error: null } }),
  )
}
async function doctor(page: Page) {
  await signInAsDoctor(page)
  const json = (url: string, data: unknown) =>
    page.route(url, (r) => r.fulfill({ json: { data, error: null } }))
  await json('**/api/v1/doctor/patients', [
    ROW,
    {
      ...ROW,
      id: `${PID.slice(0, -1)}2`,
      name: 'Test Patient B',
      symptom: null,
      fetal: null,
      unseen_count: 0,
      group: 4,
    },
  ])
  await json(`**/api/v1/doctor/patients/${PID}`, {
    ...ROW,
    age: 30,
    notes: null,
    due_date_source: 'lmp_estimate',
    doctors: [],
    hba1c_note: false,
  })
  await json('**/api/v1/doctor/inbox', [
    {
      id: 'i1',
      patient_id: PID,
      patient_name: 'Test Patient A',
      type: 'symptom_l2',
      ref_table: 'symptom_checkins',
      ref_id: 'c1',
      created_at: AT,
      seen_at: null,
      seen_by_name: null,
    },
  ])
  await json(`**/api/v1/doctor/patients/${PID}/audit*`, [])
}

const SCREENS: [string, (page: Page) => Promise<void>, string, string][] = [
  ['patient-home', patient, `${PATIENT}/home`, 'Month 7 · now'],
  ['patient-log', patient, `${PATIENT}/log`, 'Fits / convulsions'],
  ['patient-calendar', patient, `${PATIENT}/calendar`, 'What these mean'],
  ['doctor-home', doctor, `${DOCTOR}/home`, 'Needs attention'],
  ['doctor-patients', doctor, `${DOCTOR}/patients`, '2 of 2 patients'],
  ['doctor-patient', doctor, `${DOCTOR}/patients/${PID}`, 'Latest results'],
]

for (const [name, setUp, url, ready] of SCREENS) {
  for (const width of [375, 1280]) {
    for (const theme of ['light', 'dark'] as const) {
      test(`${name} ${width} ${theme}`, async ({ page }) => {
        test.skip(test.info().project.name !== 'phone-light', 'sizes are set per test')
        await page.clock.setFixedTime(NOW)
        await page.setViewportSize({ width, height: width < 1024 ? 812 : 800 })
        await page.emulateMedia({ reducedMotion: 'reduce' })
        await page.addInitScript((t) => localStorage.setItem('alovia-theme', t), theme)
        await setUp(page)
        await page.goto(url)
        await expect(page.getByText(ready, { exact: true }).first()).toBeVisible()
        await page.waitForLoadState('networkidle')
        await page.evaluate(() => document.fonts.ready)
        await expect(page).toHaveScreenshot(`${name}-${width}-${theme}.png`, {
          animations: 'disabled',
          maxDiffPixelRatio: 0.01,
        })
      })
    }
  }
}

import { expect, test, type Page } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsDoctor } from './helpers'

const AT = '2026-11-19T05:00:00Z'
const P1 = 'aaaaaaaa-0000-0000-0000-000000000001'
const P2 = 'aaaaaaaa-0000-0000-0000-000000000002'

function row(over: Record<string, unknown>) {
  return {
    id: P1,
    name: 'Test Patient A',
    linked: true,
    ga_weeks: 24,
    ga_days: 3,
    due_date: '2027-03-01',
    fetal: null,
    maternal: null,
    genetic: null,
    symptom: null,
    unseen_count: 0,
    pregnancy_status: 'active',
    group: 4,
    ...over,
  }
}

const PATIENTS = [
  row({
    name: 'Test Patient A',
    group: 1,
    unseen_count: 1,
    symptom: { level: 'L1', created_at: AT },
    fetal: { predicted_class: 'Suspect', created_at: AT },
  }),
  row({
    id: P2,
    name: 'Test Patient B',
    linked: false,
    ga_weeks: null,
    ga_days: null,
    due_date: null,
    maternal: { predicted_class: 'Low', created_at: AT },
  }),
]

function inboxItem(over: Record<string, unknown>) {
  return {
    id: 'bbbbbbbb-0000-0000-0000-000000000001',
    patient_id: P1,
    patient_name: 'Test Patient A',
    type: 'symptom_l1',
    ref_table: 'symptom_checkins',
    ref_id: 'cccccccc-0000-0000-0000-000000000001',
    created_at: AT,
    seen_by_name: null,
    seen_at: null,
    ...over,
  }
}

function detail(over: Record<string, unknown> = {}) {
  return {
    ...PATIENTS[1],
    age: 29,
    notes: 'Test note',
    due_date_source: null,
    doctors: [
      { id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', is_primary: true },
    ],
    ...over,
  }
}

async function json(page: Page, url: string, data: unknown) {
  await page.route(url, (route) => route.fulfill({ json: { data, error: null } }))
}

test('doctor home: inbox, mark as seen, patient list in server order with filters', async ({
  page,
}) => {
  await signInAsDoctor(page)
  let seen = false
  await page.route('**/api/v1/doctor/inbox', (route) =>
    route.fulfill({
      json: {
        data: seen ? [] : [inboxItem({}), inboxItem({ id: 'b2', type: 'ai_note_flag' })],
        error: null,
      },
    }),
  )
  await page.route('**/api/v1/doctor/inbox/*/seen', (route) => {
    seen = true
    return route.fulfill({
      json: { data: inboxItem({ seen_by_name: 'Test Doctor', seen_at: AT }), error: null },
    })
  })
  await json(page, '**/api/v1/doctor/patients', PATIENTS)
  await page.goto(`${DOCTOR}/home`)

  await expect(page.getByRole('heading', { level: 1, name: 'Home' })).toBeVisible()
  await expect(page.getByText('Symptom check-in: level L1')).toBeVisible()
  await expect(page.getByText('AI suggestion')).toBeVisible() // labelled (§7.2)
  // summary tiles (FRONTEND_REDESIGN §8.2): patients and unseen alerts
  const summary = page.locator('dl[aria-label="Summary"]')
  await expect(summary.locator('dt')).toHaveText(['Patients', 'Unseen alerts'])
  await expect(summary.locator('dd')).toHaveText(['2', '2'])
  // the patient list preview keeps the server's order and links to the full list
  const laptopOrTablet = (page.viewportSize()?.width ?? 0) >= 768
  const list = laptopOrTablet
    ? page.getByRole('region', { name: 'Patient list' }).getByRole('row')
    : page.getByRole('list', { name: 'Patient list' }).getByRole('listitem')
  const first = laptopOrTablet ? 1 : 0 // the table has a header row
  await expect(list.nth(first)).toContainText('Test Patient A')
  await expect(list.nth(first)).toContainText('Suspect') // class as text, not colour only
  await expect(list.nth(first + 1)).toContainText('Not joined yet')
  await expect(page.getByRole('link', { name: 'All patients (2)' })).toBeVisible()
  await expectNoA11yViolations(page)

  await page
    .getByRole('button', { name: 'Mark as seen: Symptom check-in: level L1, Test Patient A' })
    .click()
  await expect(page.getByText('Nothing needs attention right now.')).toBeVisible()

  // filters live on the Patients page; on phones they open in a sheet (§8.5)
  await page.getByRole('link', { name: 'All patients (2)' }).click()
  if (!laptopOrTablet) await page.getByRole('button', { name: 'Filters' }).click()
  const filters = laptopOrTablet
    ? page.locator('main')
    : page.getByRole('dialog', { name: 'Filters' })
  await filters.getByLabel('Latest maternal class').selectOption('Low')
  if (!laptopOrTablet) await page.getByRole('button', { name: 'Show 1 patients' }).click()
  await expect(page.getByText('1 of 2 patients')).toBeVisible()
  await expect(list).toHaveCount(laptopOrTablet ? 2 : 1) // Test Patient B (+ header)
  await expect(list.nth(first)).toContainText('Test Patient B')
  // the active filter is a chip that removes it
  await page.getByRole('button', { name: /Maternal: Low/ }).click()
  await expect(page.getByText('2 of 2 patients')).toBeVisible()
  await expectNoA11yViolations(page)
})

test('doctor: inbox item opens the related tab of the patient', async ({ page }) => {
  await signInAsDoctor(page)
  await json(page, '**/api/v1/doctor/inbox', [inboxItem({})])
  await json(page, `**/api/v1/doctor/patients/${P1}`, detail({ id: P1, name: 'Test Patient A' }))
  await page.goto(`${DOCTOR}/home`)
  await page.getByRole('link', { name: 'Test Patient A' }).first().click()
  await expect(page).toHaveURL(`${DOCTOR}/patients/${P1}/symptoms`)
  await expect(page.getByRole('link', { name: 'Symptoms' })).toHaveAttribute('aria-current', 'page')
})

test('doctor: create a patient, then show and copy the invite link', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'])
  await signInAsDoctor(page)
  let created: unknown = null
  await page.route('**/api/v1/doctor/patients', (route) => {
    if (route.request().method() !== 'POST') return route.fallback()
    created = route.request().postDataJSON()
    return route.fulfill({ status: 201, json: { data: detail(), error: null } })
  })
  await json(page, `**/api/v1/doctor/patients/${P2}`, detail())
  await page.route(`**/api/v1/doctor/patients/${P2}/invite`, (route) =>
    route.fulfill({
      status: 201,
      json: {
        data: { link: 'http://localhost:5173/join?code=TESTCODE', expires_at: AT },
        error: null,
      },
    }),
  )
  await page.goto(`${DOCTOR}/patients/new`)
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Enter the patient’s name.')).toBeVisible()
  await page.getByLabel('Name').fill('  Test Patient B ')
  await page.getByLabel('Age (optional)').fill('17')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Age must be a whole number, 18 or more.')).toBeVisible()
  await page.getByLabel('Age (optional)').fill('29')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Save' }).click()
  expect(created).toEqual({ name: 'Test Patient B', age: 29, notes: null })

  await expect(page).toHaveURL(`${DOCTOR}/patients/${P2}`)
  await expect(page.getByRole('heading', { level: 1, name: 'Test Patient B' })).toBeVisible()
  await expect(page.getByText('Test Doctor (primary)')).toBeVisible()
  await page.getByRole('button', { name: 'Invite patient' }).click()
  await expect(page.getByLabel('Invite link')).toHaveValue(
    'http://localhost:5173/join?code=TESTCODE',
  )
  await page.getByRole('button', { name: 'Copy' }).click()
  await expect(page.getByText(/^Copied\./)).toBeVisible()
  await expectNoA11yViolations(page)
})

test('doctor: an unknown or unassigned patient shows the not-found message', async ({ page }) => {
  await signInAsDoctor(page)
  await page.route(`**/api/v1/doctor/patients/${P1}`, (route) =>
    route.fulfill({
      status: 404,
      json: { data: null, error: { code: 'NOT_FOUND', message: 'Patient not found.' } },
    }),
  )
  await page.goto(`${DOCTOR}/patients/${P1}`)
  await expect(page.getByText("We couldn't find this.")).toBeVisible()
})

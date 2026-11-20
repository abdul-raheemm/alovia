import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  expectNoA11yViolations,
  signInAsDoctor,
  signInAsPatient,
  TEST_DOCTOR_ME,
} from './helpers'

const AT = '2026-11-19T05:00:00Z'

async function json(page: Page, url: string, data: unknown, status = 200) {
  await page.route(url, (route) => route.fulfill({ status, json: { data, error: null } }))
}

function ruleRow(key: string, checked: boolean | null) {
  return {
    key,
    item_id: key.split(':')[1],
    section: '1 Test section',
    what_to_check: `Check ${key}`,
    current_value: 'Test value',
    source: 'Test spec §1',
    checked,
    comment: null,
    doctor_name: checked === null ? null : 'Test Doctor',
    signed_at: checked === null ? null : AT,
  }
}

test('rule review: sign a row, filter open rows, export', async ({ page }) => {
  await signInAsDoctor(page)
  const modules = [
    {
      module: 'genetic',
      rules_version: '1.0.0',
      total: 2,
      checked: 1,
      rows: [ruleRow('1:HBB-01', true), ruleRow('1:HBB-02', null)],
    },
    { module: 'symptom', rules_version: '1.0.0', total: 0, checked: 0, rows: [] },
    { module: 'journey', rules_version: 'j-abc', total: 0, checked: 0, rows: [] },
  ]
  await json(page, '**/api/v1/doctor/rules', modules)
  let signed: unknown = null
  await page.route('**/api/v1/doctor/rules/genetic/signoff', (route) => {
    signed = route.request().postDataJSON()
    return route.fulfill({ status: 201, json: { data: ruleRow('1:HBB-02', true), error: null } })
  })
  let exported = false
  await page.route('**/api/v1/doctor/rules/genetic/export', (route) => {
    exported = true
    return route.fulfill({ body: '# Rule review', contentType: 'text/markdown' })
  })

  await page.goto(`${DOCTOR}/rule-review`)
  await expect(page.getByRole('button', { name: 'Genetic risk (1/2)' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await expect(page.getByText('Checked by Test Doctor')).toBeVisible()
  await page.getByLabel('Show only rows not checked yet').check()
  await expect(page.getByText('Check 1:HBB-01')).toHaveCount(0)
  await page.getByLabel('Checked', { exact: true }).check()
  await page.getByLabel('Comment (optional)').fill(' Looks right ')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Save sign-off for 1:HBB-02' }).click()
  await expect
    .poll(() => signed)
    .toEqual({ key: '1:HBB-02', checked: true, comment: 'Looks right' })

  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export sign-off' }).click()
  expect((await download).suggestedFilename()).toBe('rule_review_signoff_genetic.md')
  expect(exported).toBe(true)
})

test('admin: invite, deactivate, keep one doctor, filter the log', async ({ page }) => {
  await signInAsPatient(page, {
    ...TEST_DOCTOR_ME,
    user: { ...TEST_DOCTOR_ME.user, role: 'admin' },
    doctor: null,
  })
  const doctor = (id: string, name: string, active = true) => ({
    id,
    name,
    specialty: null,
    email: `${name.toLowerCase().replace(/\W/g, '')}@example.test`,
    is_active: active,
    patient_count: 1,
  })
  let doctors = [doctor('d1', 'Dr One'), doctor('d2', 'Dr Two')]
  let invited: unknown = null
  await page.route('**/api/v1/admin/doctors', (route) => {
    if (route.request().method() === 'POST') {
      invited = route.request().postDataJSON()
      return route.fulfill({ status: 201, json: { data: doctor('d3', 'Dr New'), error: null } })
    }
    return route.fulfill({ json: { data: doctors, error: null } })
  })
  let toggled: unknown = null
  await page.route('**/api/v1/admin/doctors/d2', (route) => {
    toggled = route.request().postDataJSON()
    doctors = doctors.map((d) => (d.id === 'd2' ? doctor('d2', 'Dr Two', false) : d))
    return route.fulfill({ json: { data: doctor('d2', 'Dr Two', false), error: null } })
  })
  await json(page, '**/api/v1/admin/assignments?q=*', [
    {
      patient_id: 'p1',
      patient_name: 'Test Patient F',
      doctors: [{ doctor_id: 'd1', name: 'Dr One', is_primary: true, is_active: true }],
    },
  ])
  await page.route('**/api/v1/admin/assignments?patient_id=*', (route) =>
    route.fulfill({
      status: 409,
      json: {
        data: null,
        error: { code: 'CONFLICT', message: 'A patient must keep at least one assigned doctor.' },
      },
    }),
  )
  await json(page, '**/api/v1/admin/audit/actions', ['patient created'])
  let auditUrl = ''
  await page.route('**/api/v1/admin/audit?*', (route) => {
    auditUrl = route.request().url()
    return route.fulfill({
      json: {
        data: [
          {
            id: 'a1',
            created_at: AT,
            actor_email: 'drone@example.test',
            actor_role: 'doctor',
            actor_name: 'Dr One',
            action: 'patient created',
            entity_type: 'patient',
            entity_id: 'p1',
            patient_id: 'p1',
            patient_name: 'Test Patient F',
          },
        ],
        error: null,
      },
    })
  })

  await page.goto(`${DOCTOR}/admin`)
  await expect(page.getByRole('heading', { level: 1, name: 'Admin' })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill('new@example.test')
  await page.getByLabel('Name', { exact: true }).fill('Dr New')
  await page.getByRole('button', { name: 'Send invite' }).click()
  await expect(page.getByText('Invite sent to drnew@example.test.')).toBeVisible()
  expect(invited).toEqual({ email: 'new@example.test', name: 'Dr New', specialty: null })

  await page.getByRole('button', { name: 'Deactivate Dr Two' }).click()
  await expect(page.getByRole('button', { name: 'Reactivate Dr Two' })).toBeVisible()
  expect(toggled).toEqual({ name: 'Dr Two', specialty: null, is_active: false })

  await page.getByRole('button', { name: 'Remove Dr One from Test Patient F' }).click()
  await expect(page.getByText('A patient must keep at least one assigned doctor.')).toBeVisible()

  await page.getByLabel('Action').selectOption('patient created')
  await expect.poll(() => auditUrl).toContain('action=patient+created')
  await expect(page.getByRole('region', { name: 'Activity log entries' })).toContainText(
    'Test Patient F',
  )
  await expectNoA11yViolations(page)
})

test('admin page is for admins only', async ({ page }) => {
  await signInAsDoctor(page)
  await page.goto(`${DOCTOR}/admin`)
  await expect(page).toHaveURL(`${DOCTOR}/home`)
  await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0)
})

test('set password: invalid link without a session; saves with one', async ({ page }) => {
  await page.goto(`${DOCTOR}/set-password`)
  await expect(page.getByText('This invite link is not valid any more.')).toBeVisible()
  await expectNoA11yViolations(page)

  await signInAsDoctor(page)
  let updated: unknown = null
  await page.route('**/auth/v1/user', (route) => {
    updated = route.request().postDataJSON()
    return route.fulfill({
      json: { id: TEST_DOCTOR_ME.user.id, aud: 'authenticated', email: TEST_DOCTOR_ME.user.email },
    })
  })
  await page.goto(`${DOCTOR}/set-password`)
  await page.getByLabel('New password').fill('test-password-1')
  await page.getByLabel('Repeat the password').fill('different')
  await page.getByRole('button', { name: 'Save password' }).click()
  await expect(page.getByText('The passwords do not match.')).toBeVisible()
  await page.getByLabel('Repeat the password').fill('test-password-1')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Save password' }).click()
  await expect(page).toHaveURL(`${DOCTOR}/home`)
  expect(updated).toMatchObject({ password: 'test-password-1' })
})

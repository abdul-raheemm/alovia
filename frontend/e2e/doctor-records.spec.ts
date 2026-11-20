import { expect, test } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsDoctor } from './helpers'

const PID = 'aaaaaaaa-0000-0000-0000-000000000005'
const AT = '2026-11-19T05:00:00Z'

function patient() {
  return {
    id: PID,
    name: 'Test Patient E',
    linked: true,
    ga_weeks: null,
    ga_days: null,
    due_date: null,
    fetal: null,
    maternal: null,
    genetic: null,
    symptom: null,
    unseen_count: 0,
    pregnancy_status: 'active',
    group: 4,
    age: null,
    notes: null,
    due_date_source: null,
    doctors: [
      { id: '77777777-7777-7777-7777-777777777777', name: 'Test Doctor', is_primary: true },
    ],
    hba1c_note: false,
  }
}

const RECORD = {
  id: 'ffffffff-0000-0000-0000-000000000001',
  file_type: 'blood_report',
  original_filename: 'test-report.pdf',
  note: 'Test note',
  uploaded_at: AT,
  uploaded_by_name: 'Test Doctor',
}

test('records: upload a file as multipart, list it, open a short-lived link', async ({ page }) => {
  await signInAsDoctor(page)
  // record the link the app opens instead of leaving the test page
  await page.addInitScript(() => {
    ;(window as unknown as { opened: string[] }).opened = []
    window.open = (url?: string | URL) => {
      ;(window as unknown as { opened: string[] }).opened.push(String(url))
      return null
    }
  })
  await page.route(`**/api/v1/doctor/patients/${PID}`, (route) =>
    route.fulfill({ json: { data: patient(), error: null } }),
  )
  let records: unknown[] = []
  let uploaded: { type: string | null; body: string } | null = null
  await page.route(`**/api/v1/doctor/patients/${PID}/records`, (route) => {
    if (route.request().method() === 'POST') {
      uploaded = {
        type: route.request().headers()['content-type'] ?? null,
        body: route.request().postData() ?? '',
      }
      records = [RECORD]
      return route.fulfill({ status: 201, json: { data: RECORD, error: null } })
    }
    return route.fulfill({ json: { data: records, error: null } })
  })
  await page.route(`**/api/v1/doctor/records/${RECORD.id}/download`, (route) =>
    route.fulfill({
      json: {
        data: { url: 'https://storage.example.test/signed/x', expires_in: 300 },
        error: null,
      },
    }),
  )

  await page.goto(`${DOCTOR}/patients/${PID}/records`)
  await expect(page.getByText('No records yet.')).toBeVisible()
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByText('Choose a file.')).toBeVisible()
  await page.getByLabel('File').setInputFiles({
    name: 'test-report.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('%PDF-1.7 test'),
  })
  await page.getByLabel('Type').selectOption('blood_report')
  await page.getByLabel('Note (optional)').fill('Test note')
  await expectNoA11yViolations(page)
  await page.getByRole('button', { name: 'Upload' }).click()

  await expect(page.getByText('test-report.pdf')).toBeVisible()
  expect(uploaded).not.toBeNull()
  const sent = uploaded as unknown as { type: string; body: string }
  expect(sent.type).toMatch(/^multipart\/form-data; boundary=/)
  expect(sent.body).toContain('name="file_type"\r\n\r\nblood_report')
  expect(sent.body).toContain('filename="test-report.pdf"')

  await page.getByRole('button', { name: 'Download test-report.pdf' }).click()
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { opened: string[] }).opened))
    .toEqual(['https://storage.example.test/signed/x'])
  await expectNoA11yViolations(page)
})

test('records: a server refusal is shown in plain words', async ({ page }) => {
  await signInAsDoctor(page)
  await page.route(`**/api/v1/doctor/patients/${PID}`, (route) =>
    route.fulfill({ json: { data: patient(), error: null } }),
  )
  await page.route(`**/api/v1/doctor/patients/${PID}/records`, (route) =>
    route.request().method() === 'POST'
      ? route.fulfill({
          status: 415,
          json: {
            data: null,
            error: { code: 'UNSUPPORTED_FILE_TYPE', message: 'Only PDF, JPG, PNG' },
          },
        })
      : route.fulfill({ json: { data: [], error: null } }),
  )
  await page.goto(`${DOCTOR}/patients/${PID}/records`)
  await page.getByLabel('File').setInputFiles({
    name: 'photo.gif',
    mimeType: 'image/gif',
    buffer: Buffer.from('GIF89a'),
  })
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByRole('alert')).toHaveText('Only PDF, JPG, PNG')
})

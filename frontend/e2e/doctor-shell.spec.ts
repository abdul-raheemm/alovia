import { expect, test, type Page } from '@playwright/test'

import { DOCTOR, expectNoA11yViolations, signInAsDoctor } from './helpers'

// FRONTEND_REDESIGN §8.1, §8.3, §8.5 (step 6a). Mocked API, synthetic names only.
function row(i: number, over: Record<string, unknown> = {}) {
  return {
    id: `00000000-0000-0000-0000-${String(i).padStart(12, '0')}`,
    name: `Test Patient ${String(i).padStart(2, '0')}`,
    linked: true,
    ga_weeks: 10 + (i % 20),
    ga_days: 0,
    due_date: null,
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
const MANY = Array.from({ length: 30 }, (_, i) => row(i + 1))

async function setUp(page: Page, patients: unknown[] = MANY) {
  await signInAsDoctor(page)
  await page.route('**/api/v1/doctor/patients', (r) =>
    r.fulfill({ json: { data: patients, error: null } }),
  )
}
const width = (page: Page) => page.viewportSize()?.width ?? 0

test('laptop side bar: 240 px, active pill with a 2 px marker, collapses to 72 px', async ({
  page,
}) => {
  test.skip(width(page) < 1024, 'laptop layout only')
  await setUp(page)
  await page.goto(`${DOCTOR}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  expect(Math.round((await nav.boundingBox())?.width ?? 0)).toBe(240)
  const active = nav.getByRole('link', { name: 'Home' })
  await expect(active).toHaveAttribute('aria-current', 'page')
  expect(await active.evaluate((e) => getComputedStyle(e, '::before').width)).toBe('2px')
  await nav.getByRole('button', { name: 'Collapse menu' }).click()
  expect(Math.round((await nav.boundingBox())?.width ?? 0)).toBe(72)
  const header = await page.locator('header').boundingBox()
  expect(Math.round(header?.height ?? 0)).toBe(56)
})

test('tablet: the side bar shows icons only', async ({ page }) => {
  await page.setViewportSize({ width: 800, height: 900 })
  await setUp(page)
  await page.goto(`${DOCTOR}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  expect(Math.round((await nav.boundingBox())?.width ?? 0)).toBe(72)
  await expect(nav.getByRole('link', { name: 'Patients' })).toBeVisible() // name kept for AT
})

test('phone: the menu button opens the side bar as a sheet; a link closes it', async ({ page }) => {
  test.skip(width(page) >= 768, 'phone layout only')
  await setUp(page)
  await page.goto(`${DOCTOR}/home`)
  await page.getByRole('button', { name: 'Open menu' }).click()
  const sheet = page.getByRole('dialog')
  await expect(sheet.getByRole('link', { name: 'Rule review' })).toBeVisible()
  await expectNoA11yViolations(page)
  await sheet.getByRole('link', { name: 'Patients' }).click()
  await expect(page).toHaveURL(`${DOCTOR}/patients`)
  await expect(sheet).toBeHidden()
})

test('"/" focuses the patient search; Enter opens the filtered list', async ({ page }) => {
  await setUp(page)
  await page.goto(`${DOCTOR}/home`)
  await page.getByRole('heading', { level: 1, name: 'Home' }).click() // focus outside a field
  await page.keyboard.press('/')
  const search = page.getByRole('searchbox', { name: 'Search patients' })
  await expect(search).toBeFocused()
  await search.fill('Patient 07')
  await search.press('Enter')
  await expect(page).toHaveURL(`${DOCTOR}/patients?q=Patient%2007`)
  await expect(page.getByText('1 of 30 patients')).toBeVisible()
})

test('user menu shows the name and role with Sign out', async ({ page }) => {
  await setUp(page)
  await page.goto(`${DOCTOR}/home`)
  await page.locator('header summary').click()
  await expect(page.getByText('doctor', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
})

test('patient table: sort, 25 per page, arrow keys and Enter open a patient', async ({ page }) => {
  test.skip(width(page) < 768, 'table layout only')
  await setUp(page)
  await page.goto(`${DOCTOR}/patients`)
  const table = page.getByRole('region', { name: 'Patient list' })
  const rows = table.getByRole('row')
  await expect(rows).toHaveCount(26) // header + 25
  await expect(page.getByText('Page 1 of 2')).toBeVisible()
  await page.getByRole('button', { name: 'Next' }).click()
  await expect(rows).toHaveCount(6) // header + 5
  await page.getByRole('button', { name: 'Previous' }).click()

  await table.getByRole('button', { name: 'Patient' }).click() // A to Z
  await table.getByRole('button', { name: 'Patient' }).click() // Z to A
  await expect(table.getByRole('columnheader', { name: 'Patient' })).toHaveAttribute(
    'aria-sort',
    'descending',
  )
  await expect(rows.nth(1)).toContainText('Test Patient 30')

  await rows.nth(1).focus()
  await page.keyboard.press('ArrowDown')
  await expect(rows.nth(2)).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(`${DOCTOR}/patients/${row(29).id}`)
})

test('phone: patients are cards with name, week, badges and a chevron', async ({ page }) => {
  test.skip(width(page) >= 768, 'phone layout only')
  await setUp(page, [
    row(1, { symptom: { level: 'L1', created_at: '2026-11-19T05:00:00Z' }, unseen_count: 2 }),
    row(2),
  ])
  await page.goto(`${DOCTOR}/patients`)
  const cards = page.getByRole('list', { name: 'Patient list' }).getByRole('listitem')
  await expect(cards).toHaveCount(2)
  await expect(cards.first()).toContainText('Test Patient 01')
  await expect(cards.first()).toContainText('11w 0d · 2 unseen')
  await expect(cards.first()).toContainText('L1')
  const box = await cards.first().getByRole('link').boundingBox()
  expect(box?.height).toBeGreaterThanOrEqual(44)
  const wide = await page.evaluate(() => document.documentElement.scrollWidth)
  expect(wide).toBeLessThanOrEqual(width(page))
  await expectNoA11yViolations(page)
})

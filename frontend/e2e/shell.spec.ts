import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  expectNoA11yViolations,
  journeyHome,
  MONTHS,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
} from './helpers'

// FRONTEND_REDESIGN §7.4, §11 rules 4, 6, 13; DEC-112
const HOME = journeyHome({
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
})

const isLaptop = (page: Page) => (page.viewportSize()?.width ?? 0) >= 1024

test('phone bottom bar: Log raised in the centre, full labels, 44 px targets', async ({ page }) => {
  test.skip(isLaptop(page), 'phone layout only')
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  const links = nav.getByRole('link')
  await expect(links).toHaveCount(5)
  await expect(links.nth(2)).toHaveText('Log')
  await expect(nav.getByRole('link', { name: 'Home' })).toHaveAttribute('aria-current', 'page')

  for (const link of await links.all()) {
    const box = await link.boundingBox()
    expect(box?.height).toBeGreaterThanOrEqual(44)
    expect(box?.width).toBeGreaterThanOrEqual(44)
    // labels are never cut off (no ellipsis)
    const cut = await link
      .locator('span')
      .last()
      .evaluate((e) => e.scrollWidth > e.clientWidth)
    expect(cut).toBe(false)
  }
  // the Log circle sits higher than the other items
  const logTop = (await links.nth(2).boundingBox())?.y ?? 0
  const homeTop = (await links.nth(0).boundingBox())?.y ?? 0
  expect(logTop).toBeLessThan(homeTop)
  // all five labels sit on one line
  const labelTops = await Promise.all(
    (await links.all()).map(async (l) => (await l.locator('span').last().boundingBox())?.y ?? 0),
  )
  expect(Math.max(...labelTops) - Math.min(...labelTops)).toBeLessThanOrEqual(2)
  await expectNoA11yViolations(page)
})

test('laptop side bar: Log is the button at the top', async ({ page }) => {
  test.skip(!isLaptop(page), 'laptop layout only')
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: HOME, error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  await expect(nav.getByRole('link').first()).toHaveText('Log')
  await nav.getByRole('link', { name: 'Log' }).click()
  await expect(page).toHaveURL(`${PATIENT}/log`)
  await expectNoA11yViolations(page)
})

test('while home loads: skeleton, no pulse with reduced motion, the bar still works', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await signInAsPatient(page)
  // the home reply never arrives during this test
  await page.route('**/api/v1/patient/journey/home', () => undefined)
  await page.goto(`${PATIENT}/home`)
  const loading = page.getByRole('status', { name: 'Loading' })
  await expect(loading).toBeVisible()
  const pulse = await loading
    .locator('[data-skeleton]')
    .first()
    .evaluate((e) => getComputedStyle(e).animationName)
  expect(pulse).toBe('none')
  await expectNoA11yViolations(page)
  // the fallback items keep the bar usable
  await page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'More' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'More' })).toBeVisible()
})

test('doctor side bar collapses to icons and expands again', async ({ page }) => {
  test.skip(!isLaptop(page), 'laptop layout only')
  await signInAsDoctor(page)
  await page.goto(`${DOCTOR}/home`)
  const nav = page.getByRole('navigation', { name: 'Main' })
  const toggle = nav.getByRole('button', { name: 'Collapse menu' })
  await expect(toggle).toHaveAttribute('aria-expanded', 'true')
  await toggle.click()
  const expand = nav.getByRole('button', { name: 'Expand menu' })
  await expect(expand).toHaveAttribute('aria-expanded', 'false')
  // labels stay for screen readers; the links still work
  await expect(nav.getByRole('link', { name: 'Patients' })).toBeVisible()
  expect((await nav.boundingBox())?.width).toBeLessThan(100)
  await expectNoA11yViolations(page)
  await expand.click()
  await expect(nav.getByRole('button', { name: 'Collapse menu' })).toBeVisible()
})

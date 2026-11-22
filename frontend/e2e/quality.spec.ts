import { expect, test, type Page } from '@playwright/test'

import {
  DOCTOR,
  journeyHome,
  MONTHS,
  mockCalendar,
  PATIENT,
  signInAsDoctor,
  signInAsPatient,
} from './helpers'

// FRONTEND_REDESIGN §13: no horizontal scroll at 360 px on every screen, 44 px touch targets,
// layout shift under 0.1 on Home, Log and Calendar (Home: home-ring.spec.ts).
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
const PATIENT_SCREENS = [
  '/home',
  '/calendar',
  '/appointments',
  '/more',
  '/doctor-notes',
  '/dates',
  '/urgent',
  '/log/history',
  '/genetic',
  '/results',
]
const DOCTOR_SCREENS = ['/home', '/patients', '/patients/new', '/genetic-review', '/rule-review']
const PUBLIC_SCREENS = ['/', '/sign-in', '/privacy']

/** Interactive elements smaller than 44 × 44 px. A checkbox or radio counts with its label;
 * links inside running text are exempt (WCAG 2.5.8 inline exception). */
function smallTargets(page: Page) {
  return page.evaluate(() => {
    const bad: string[] = []
    const all = document.querySelectorAll<HTMLElement>(
      'a[href], button, select, summary, input:not([type=hidden]), textarea',
    )
    for (const el of all) {
      if (el.closest('[aria-hidden="true"]')) continue
      let target: HTMLElement = el
      if (el instanceof HTMLInputElement && (el.type === 'checkbox' || el.type === 'radio')) {
        target = el.labels?.[0] ?? el.closest('label') ?? el
      }
      const box = target.getBoundingClientRect()
      if (box.width <= 1 || box.height <= 1) continue // visually hidden (skip link, sr-only)
      if (el.tagName === 'A') {
        const around = (el.parentElement?.textContent ?? '').trim().length
        if (around > (el.textContent ?? '').trim().length + 2) continue
      }
      if (box.width < 44 || box.height < 44) {
        const name = (el.textContent || el.getAttribute('aria-label') || el.tagName).trim()
        bad.push(`${name.slice(0, 30)} ${Math.round(box.width)}x${Math.round(box.height)}`)
      }
    }
    return bad
  })
}

async function check(page: Page, url: string) {
  await page.setViewportSize({ width: 360, height: 780 })
  await page.goto(url)
  await page.waitForLoadState('networkidle')
  const wide = await page.evaluate(() => document.documentElement.scrollWidth)
  expect(wide, `${url} is ${wide} px wide at 360`).toBeLessThanOrEqual(360)
  await page.setViewportSize({ width: 375, height: 812 })
  expect(await smallTargets(page), url).toEqual([])
}

test.describe('every screen', () => {
  test.beforeEach(() => {
    test.skip(
      test.info().project.name !== 'phone-light',
      'sizes are set per test; one project is enough',
    )
  })
  test.setTimeout(180_000)

  test('patient screens: no sideways scroll at 360 px, 44 px targets', async ({ page }) => {
    await signInAsPatient(page)
    await mockCalendar(page, { start: '2026-05-25', end: '2027-03-15' })
    await page.route('**/api/v1/patient/journey/home', (r) =>
      r.fulfill({ json: { data: HOME, error: null } }),
    )
    await page.route('**/api/v1/patient/appointments', (r) =>
      r.fulfill({ json: { data: { upcoming: [], past: [] }, error: null } }),
    )
    for (const path of PATIENT_SCREENS) await check(page, `${PATIENT}${path}`)
  })

  test('doctor screens: no sideways scroll at 360 px, 44 px targets', async ({ page }) => {
    await signInAsDoctor(page)
    for (const path of DOCTOR_SCREENS) await check(page, `${DOCTOR}${path}`)
  })

  test('public pages: no sideways scroll at 360 px, 44 px targets', async ({ page }) => {
    for (const path of PUBLIC_SCREENS) await check(page, `${PATIENT}${path}`)
  })
})

for (const [name, path] of [
  ['Log', '/log'],
  ['Calendar', '/calendar'],
] as const) {
  test(`${name} loads without layout shift (CLS under 0.1)`, async ({ page }) => {
    await page.addInitScript(() => {
      const w = window as unknown as { cls: number }
      w.cls = 0
      new PerformanceObserver((list) => {
        for (const e of list.getEntries() as unknown as {
          value: number
          hadRecentInput: boolean
        }[])
          if (!e.hadRecentInput) w.cls += e.value
      }).observe({ type: 'layout-shift', buffered: true })
    })
    await signInAsPatient(page)
    await mockCalendar(page, { start: '2026-05-25', end: '2027-03-15' })
    await page.route('**/api/v1/patient/journey/home', (r) =>
      r.fulfill({ json: { data: HOME, error: null } }),
    )
    await page.goto(`${PATIENT}${path}`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)
    expect(await page.evaluate(() => (window as unknown as { cls: number }).cls)).toBeLessThan(0.1)
  })
}

import { expect, test, type Page } from '@playwright/test'

import { expectNoA11yViolations, journeyHome, MONTHS, PATIENT, signInAsPatient } from './helpers'

// FRONTEND_REDESIGN §7.1-7.3 and §11 rules 1-5, 10. Mocked API, test strings only.
const PREGNANCY = {
  completed_weeks: 24,
  days: 3,
  days_to_go: 104,
  content_week: 24,
  trimester: 2,
  month: 6,
  is_estimate: true,
}
const ACTIVE = journeyHome({
  state: 'active',
  dates: { due_date: '2027-03-01', lmp_date: '2026-05-25', due_date_source: 'lmp_estimate' },
  pregnancy: PREGNANCY,
  months: MONTHS,
  size: {
    week: 24,
    length_cm: null,
    weight_g: 600,
    object_icon_id: 'test_icon',
    object_name: 'test object',
    source: {
      publisher: 'Test Publisher',
      title: 'Test size table',
      url: 'https://example.test/sizes',
      licence: 'CC BY 4.0',
      date_accessed: '2026-11-17',
      kb_doc_id: null,
    },
    review_status: 'unreviewed',
  },
})
const RING = /^Pregnancy ring in three parts/

async function openHome(page: Page, data: unknown = ACTIVE) {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data, error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByText('Month 6 · now')).toBeVisible()
}

/** Screen point on the ring for a week, with the same geometry as app/ring.ts. */
async function ringPoint(page: Page, week: number): Promise<[number, number]> {
  const box = await page.getByRole('img', { name: RING }).boundingBox()
  if (!box) throw new Error('ring not found')
  const degPerWeek = (360 - 9) / 43
  const angle = 1.5 + week * degPerWeek + (week < 14 ? 0 : week < 28 ? 3 : 6)
  const rad = (angle * Math.PI) / 180
  const r = (140 / 320) * box.width
  const cx = box.x + box.width / 2
  const cy = box.y + box.height / 2
  return [cx + r * Math.sin(rad), cy - r * Math.cos(rad)]
}

test('ring, headline and size line are on the first screen at 375 by 667', async ({ page }) => {
  test.skip((page.viewportSize()?.width ?? 0) >= 1024, 'phone layout only')
  await page.setViewportSize({ width: 375, height: 667 })
  await openHome(page)
  await expect(page.getByRole('img', { name: RING })).toBeVisible()
  await expect(page.getByRole('heading', { name: '24 weeks, 3 days pregnant' })).toBeVisible()
  await expect(page.getByText('Second trimester')).toBeVisible()
  await expect(page.getByText('104 days to go')).toBeVisible()
  // rows 1-6 visible without scrolling: the size line sits above the bottom bar
  const size = await page.getByText('About the size of a test object').boundingBox()
  const bar = await page.getByRole('navigation', { name: 'Main' }).boundingBox()
  expect((size?.y ?? 999) + (size?.height ?? 0)).toBeLessThanOrEqual(bar?.y ?? 0)
  await expectNoA11yViolations(page)
})

test('dragging previews a week: headline, date and link change; image and data do not', async ({
  page,
}) => {
  let posted = 0
  await page.route('**/api/v1/patient/**', async (route) => {
    if (route.request().method() !== 'GET') posted += 1
    await route.fallback()
  })
  await openHome(page)
  const image = page.getByRole('img', {
    name: 'Illustration of a typical baby in month 6 of pregnancy',
  })
  await expect(page.locator('[data-ring-marker]')).toHaveText('Wk 24')

  await page.locator('[data-ring-marker] circle').hover()
  await page.mouse.down()
  for (const week of [26, 28.5, 30.5]) {
    const [x, y] = await ringPoint(page, week)
    await page.mouse.move(x, y, { steps: 4 })
  }
  await page.mouse.up()

  await expect(page.getByRole('heading', { name: 'Week 30' })).toBeVisible()
  await expect(page.getByText('Starts 21 December 2026')).toBeVisible() // due date − 280 + 7 × 30
  await expect(page.getByText('Viewing week 30')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Read about week 30' })).toHaveAttribute(
    'href',
    '/months/7',
  )
  await expect(page.locator('[data-ring-marker]')).toHaveText('Wk 30')
  // §7.3: the image and caption stay on today's month; §11 rule 2: nothing is written
  await expect(image.first()).toHaveAttribute('src', '/illustrations/month_6.webp')
  await expect(page.getByText('Month 6 · now')).toBeVisible()
  expect(posted).toBe(0)
  await expectNoA11yViolations(page)

  await page.getByRole('button', { name: 'Back to today' }).click()
  await expect(page.getByRole('heading', { name: '24 weeks, 3 days pregnant' })).toBeVisible()
  await expect(page.getByText('Viewing week')).toHaveCount(0)
})

test('no due date: onboarding card, no ring; quick log stays', async ({ page }) => {
  await signInAsPatient(page)
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: journeyHome(), error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByRole('heading', { name: 'Your pregnancy dates' })).toBeVisible()
  await expect(page.getByRole('img', { name: RING })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toBeVisible()
})

test('past 42 weeks the marker stops at the end', async ({ page }) => {
  await signInAsPatient(page)
  const beyond = journeyHome({
    state: 'beyond_42',
    dates: { due_date: '2026-10-20', lmp_date: null, due_date_source: 'clinician_confirmed' },
    pregnancy: { ...PREGNANCY, completed_weeks: 44, days: 0, days_to_go: null, month: 9 },
    months: MONTHS,
  })
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: beyond, error: null } }),
  )
  await page.goto(`${PATIENT}/home`)
  await expect(page.getByRole('heading', { name: '42 weeks pregnant' })).toBeVisible()
  await expect(page.locator('[data-ring-marker]')).toHaveText('Wk 42')
  await expect(page.getByText('Month 9 · now')).toBeVisible()
})

test('the image floats only when motion is allowed', async ({ page }) => {
  await openHome(page)
  const float = page.locator('.ring-float')
  expect(await float.evaluate((e) => getComputedStyle(e).animationName)).toBe('alovia-float')
  await page.emulateMedia({ reducedMotion: 'reduce' })
  expect(await float.evaluate((e) => getComputedStyle(e).animationName)).toBe('none')
})

test('laptop: ring column on the left, cards on the right', async ({ page }) => {
  test.skip((page.viewportSize()?.width ?? 0) < 1024, 'laptop layout only')
  await openHome(page)
  const ring = await page.getByRole('img', { name: RING }).boundingBox()
  const quickLog = await page.getByRole('link', { name: 'Log a symptom' }).boundingBox()
  expect((ring?.x ?? 0) + (ring?.width ?? 0)).toBeLessThan(quickLog?.x ?? 0)
  expect(Math.abs((ring?.y ?? 0) - (quickLog?.y ?? 999))).toBeLessThan(120) // side by side
  await expectNoA11yViolations(page)
})

test('home loads without layout shift (CLS under 0.1, §11 rule 5)', async ({ page }) => {
  await page.addInitScript(() => {
    ;(window as unknown as { cls: number }).cls = 0
    new PerformanceObserver((list) => {
      for (const e of list.getEntries() as unknown as { value: number; hadRecentInput: boolean }[])
        if (!e.hadRecentInput) (window as unknown as { cls: number }).cls += e.value
    }).observe({ type: 'layout-shift', buffered: true })
  })
  await openHome(page)
  await page.waitForTimeout(500)
  expect(await page.evaluate(() => (window as unknown as { cls: number }).cls)).toBeLessThan(0.1)
})

async function drag(page: Page, weeks: number[]) {
  await page.locator('[data-ring-marker] circle').hover()
  await page.mouse.down()
  for (const week of weeks) {
    const [x, y] = await ringPoint(page, week)
    await page.mouse.move(x, y, { steps: 4 })
  }
  await page.mouse.up()
}

test('preview is read-only and works backwards too: week 2, image unchanged, no actions', async ({
  page,
}) => {
  await openHome(page)
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toBeVisible()
  await drag(page, [20, 12, 6, 2.5])
  await expect(page.getByRole('heading', { name: 'Week 2' })).toBeVisible()
  await expect(page.getByText('Month 6 · now')).toBeVisible()
  await expect(
    page
      .getByRole('img', { name: 'Illustration of a typical baby in month 6 of pregnancy' })
      .first(),
  ).toHaveAttribute('src', '/illustrations/month_6.webp')
  // §7.2 (b): no log or action buttons while previewing
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Change pregnancy dates' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Back to today' }).click()
  await expect(page.getByRole('link', { name: 'Log a symptom' })).toBeVisible()
})

test('haptics: a short pulse when the day changes; none with reduced motion', async ({ page }) => {
  await page.addInitScript(() => {
    const w = window as unknown as { pulses: number[] }
    w.pulses = []
    Object.defineProperty(navigator, 'vibrate', {
      value: (ms: number) => {
        w.pulses.push(ms)
        return true
      },
    })
  })
  await openHome(page)
  await drag(page, [25, 26, 27])
  const pulses = await page.evaluate(() => (window as unknown as { pulses: number[] }).pulses)
  expect(pulses.length).toBeGreaterThan(0)
  expect(pulses.length).toBeLessThanOrEqual(3 * 7) // never more than one per day crossed
  expect(new Set(pulses)).toEqual(new Set([8])) // one short 8 ms pulse each (§7.2)

  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.reload()
  await expect(page.getByText('Month 6 · now')).toBeVisible()
  await drag(page, [25, 26, 27])
  expect(await page.evaluate(() => (window as unknown as { pulses: number[] }).pulses)).toEqual([])
})

test('month image: each month boundary week shows that month (served month map)', async ({
  page,
}) => {
  test.setTimeout(120_000) // 18 page loads, two per month
  await signInAsPatient(page)
  let current = ACTIVE
  await page.route('**/api/v1/patient/journey/home', (r) =>
    r.fulfill({ json: { data: current, error: null } }),
  )
  for (const m of MONTHS) {
    for (const week of [m.week_start ?? 0, m.week_end ?? 0]) {
      current = journeyHome({
        state: week >= 42 ? 'beyond_42' : 'active',
        dates: ACTIVE.dates,
        pregnancy: {
          ...PREGNANCY,
          completed_weeks: week,
          days: 0,
          content_week: week,
          month: m.month,
        },
        months: MONTHS,
      })
      await page.goto(`${PATIENT}/home`)
      await expect(page.getByText(`Month ${m.month} · now`)).toBeVisible()
      await expect(
        page
          .getByRole('img', {
            name: `Illustration of a typical baby in month ${m.month} of pregnancy`,
          })
          .first(),
      ).toHaveAttribute('src', `/illustrations/month_${m.month}.webp`)
    }
  }
})

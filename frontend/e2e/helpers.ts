import AxeBuilder from '@axe-core/playwright'
import { expect, type Page } from '@playwright/test'

export const PATIENT = 'http://localhost:5173'
export const DOCTOR = 'http://localhost:5174'

/** WCAG 2.1 AA checks with axe (DESIGN_SYSTEM §16, TESTING.md §2). */
export async function expectNoA11yViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  const summary = results.violations.map(
    (v) => `${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`,
  )
  expect(summary).toEqual([])
}

/** Answer GET /invites/{code}/check without a backend. */
export async function mockInviteCheck(page: Page, valid: boolean): Promise<void> {
  await page.route('**/api/v1/invites/*/check', (route) =>
    route.fulfill({ json: { data: { valid }, error: null } }),
  )
}

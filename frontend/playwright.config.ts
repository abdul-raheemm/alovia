import { defineConfig } from '@playwright/test'

// Public test settings only: a fake Supabase URL (no sign-in happens) and the local API URL,
// whose calls the tests answer themselves with page.route().
const env = {
  VITE_API_BASE_URL: 'http://localhost:8000/api/v1',
  VITE_SUPABASE_URL: 'https://e2e-test.supabase.co',
  VITE_SUPABASE_PUBLISHABLE_KEY: 'e2e-test-publishable-key',
  VITE_APP_ENV: 'development',
}

// TESTING.md §2: phone 375px and laptop 1280px, light and dark
export default defineConfig({
  testDir: './e2e',
  // the redesign's suite runs seven projects in parallel and axe scans of the phone calendar's
  // month list are slow: more time per test and per wait (the checks themselves are unchanged)
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: { trace: 'retain-on-failure' },
  projects: [
    {
      name: 'phone-light',
      use: { browserName: 'chromium', viewport: { width: 375, height: 812 }, colorScheme: 'light' },
    },
    {
      name: 'laptop-dark',
      use: { browserName: 'chromium', viewport: { width: 1280, height: 800 }, colorScheme: 'dark' },
    },
    // FRONTEND_REDESIGN §13: more sizes and both themes, for the layout checks only
    ...(
      [
        ['phone-360-dark', 360, 780, 'dark'],
        ['phone-390-light', 390, 844, 'light'],
        ['tablet-768-dark', 768, 1024, 'dark'],
        ['tablet-768-light', 768, 1024, 'light'],
        ['desktop-1440-light', 1440, 900, 'light'],
      ] as const
    ).map(([name, width, height, colorScheme]) => ({
      name,
      testMatch: /responsive\.spec\.ts/,
      use: { browserName: 'chromium' as const, viewport: { width, height }, colorScheme },
    })),
  ],
  webServer: [
    {
      command: 'npm run dev -w patient-web',
      url: 'http://localhost:5173',
      env,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev -w doctor-web',
      url: 'http://localhost:5174',
      env,
      reuseExistingServer: !process.env.CI,
    },
  ],
})

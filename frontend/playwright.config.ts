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

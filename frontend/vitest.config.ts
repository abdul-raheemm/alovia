import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

// One test run for both apps and the shared packages.
export default defineConfig({
  plugins: [react()],
  // one React for the apps and the linked workspace packages (else: "Invalid hook call")
  resolve: { dedupe: ['react', 'react-dom'] },
  // legal pages are read from docs/legal (outside frontend/)
  server: { fs: { allow: [fileURLToPath(new URL('..', import.meta.url))] } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['apps/*/src/**/*.test.{ts,tsx}', 'packages/*/src/**/*.test.{ts,tsx}'],
  },
})

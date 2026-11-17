import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

const repoRoot = fileURLToPath(new URL('../../..', import.meta.url))

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // one React for the app and the linked workspace packages
  resolve: { dedupe: ['react', 'react-dom'] },
  // legal pages are read from docs/legal at build time
  server: { port: 5174, strictPort: true, fs: { allow: [repoRoot] } },
  preview: { port: 5174, strictPort: true },
})

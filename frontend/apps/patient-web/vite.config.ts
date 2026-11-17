import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

const repoRoot = fileURLToPath(new URL('../../..', import.meta.url))

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    // DEC-014: installable to the phone home screen; it opens the web app.
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'Alovia',
        short_name: 'Alovia',
        description: 'Pregnancy companion — research prototype, not for clinical use.',
        theme_color: '#6B4FBB',
        background_color: '#FBF8FF',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/icons/icon-maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      // cache only the app's own files; health data from the API is never stored offline
      workbox: { globPatterns: ['**/*.{js,css,html,svg,png,woff2}'], runtimeCaching: [] },
    }),
  ],
  // one React for the app and the linked workspace packages
  resolve: { dedupe: ['react', 'react-dom'] },
  // legal pages are read from docs/legal at build time
  server: { port: 5173, strictPort: true, fs: { allow: [repoRoot] } },
  preview: { port: 5173, strictPort: true },
})

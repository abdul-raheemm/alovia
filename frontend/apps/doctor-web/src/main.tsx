import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import './index.css'

import { watchSystemTheme } from '@alovia/ui'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { missingConfig } from './app/config'

watchSystemTheme()
const root = createRoot(document.getElementById('root') as HTMLElement)

if (missingConfig.length > 0) {
  // Shown to the developer instead of a blank page; names only, never values.
  root.render(
    <main className="p-6">
      <h1>App not configured</h1>
      <p>Missing settings in apps/doctor-web/.env: {missingConfig.join(', ')}</p>
    </main>,
  )
} else {
  // services create the auth client from the settings, so load them only when they exist
  void import('./app/App').then(({ App }) =>
    root.render(
      <StrictMode>
        <App />
      </StrictMode>,
    ),
  )
}

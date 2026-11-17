import { AuthProvider, LEGAL_DOCS } from '@alovia/shared'
import { PlaceholderPage } from '@alovia/ui'
import { QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router'

import { AccountGate } from '../components/AccountGate'
import { PatientShell } from '../components/PatientShell'
import { PublicLayout } from '../components/PublicLayout'
import { JoinPage } from '../pages/JoinPage'
import { LandingPage } from '../pages/LandingPage'
import {
  AboutPage,
  CheckEmailPage,
  LegalPage,
  MorePage,
  NotFoundPage,
  SignInPage,
  UrgentPage,
} from '../pages/SimplePages'
import { authClient, queryClient } from './services'

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: <LandingPage /> },
      { path: '/join', element: <JoinPage /> },
      { path: '/signin', element: <SignInPage /> },
      { path: '/check-email', element: <CheckEmailPage /> },
      { path: '/about', element: <AboutPage /> },
      ...LEGAL_DOCS.map((doc) => ({ path: doc.path, element: <LegalPage doc={doc} /> })),
      { path: '*', element: <NotFoundPage /> },
    ],
  },
  {
    element: (
      <AccountGate>
        <PatientShell />
      </AccountGate>
    ),
    children: [
      // TODO(Phase 2): Journey home, calendar and appointments; TODO(Phase 3): symptom log
      { path: '/home', element: <PlaceholderPage title="Home" /> },
      { path: '/calendar', element: <PlaceholderPage title="Calendar" /> },
      { path: '/log', element: <PlaceholderPage title="Log" /> },
      { path: '/appointments', element: <PlaceholderPage title="Appointments" /> },
      { path: '/more', element: <MorePage /> },
      { path: '/urgent', element: <UrgentPage /> },
    ],
  },
])

export function App() {
  return (
    <AuthProvider client={authClient}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </AuthProvider>
  )
}

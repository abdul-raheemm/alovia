import { AuthProvider, LEGAL_DOCS } from '@alovia/shared'
import { PlaceholderPage } from '@alovia/ui'
import { QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router'

import { AccountGate } from '../components/AccountGate'
import { PatientShell } from '../components/PatientShell'
import { PublicLayout } from '../components/PublicLayout'
import { AppointmentsPage } from '../pages/AppointmentsPage'
import { CalendarPage } from '../pages/CalendarPage'
import { DatesPage } from '../pages/DatesPage'
import { HomePage } from '../pages/HomePage'
import { JoinPage } from '../pages/JoinPage'
import { MonthDetailPage } from '../pages/MonthDetailPage'
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
      { path: '/home', element: <HomePage /> },
      { path: '/dates', element: <DatesPage /> },
      { path: '/months/:month', element: <MonthDetailPage /> },
      // TODO(Phase 2 task 7): doctor notes; TODO(Phase 3): log
      { path: '/calendar', element: <CalendarPage /> },
      { path: '/log', element: <PlaceholderPage title="Log symptoms" /> },
      { path: '/appointments', element: <AppointmentsPage /> },
      { path: '/doctor-notes', element: <PlaceholderPage title="Doctor notes" /> },
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

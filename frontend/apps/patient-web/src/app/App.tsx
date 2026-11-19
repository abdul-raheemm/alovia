import { AuthProvider, LEGAL_DOCS } from '@alovia/shared'
import { QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router'

import { AccountGate } from '../components/AccountGate'
import { PatientShell } from '../components/PatientShell'
import { PublicLayout } from '../components/PublicLayout'
import { AppointmentsPage } from '../pages/AppointmentsPage'
import { CalendarPage } from '../pages/CalendarPage'
import { DatesPage } from '../pages/DatesPage'
import { DoctorNotesPage } from '../pages/DoctorNotesPage'
import { GeneticPage } from '../pages/GeneticPage'
import { ResultsPage } from '../pages/ResultsPage'
import { HomePage } from '../pages/HomePage'
import { JoinPage } from '../pages/JoinPage'
import { MonthDetailPage } from '../pages/MonthDetailPage'
import { PregnancyEndPage } from '../pages/PregnancyEndPage'
import { LandingPage } from '../pages/LandingPage'
import { LogPage } from '../pages/LogPage'
import { SymptomHistoryPage } from '../pages/SymptomHistoryPage'
import {
  AboutPage,
  CheckEmailPage,
  LegalPage,
  MorePage,
  NotFoundPage,
  SignInPage,
} from '../pages/SimplePages'
import { UrgentPage } from '../pages/UrgentPage'
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
      { path: '/calendar', element: <CalendarPage /> },
      { path: '/log', element: <LogPage /> },
      { path: '/log/history', element: <SymptomHistoryPage /> },
      { path: '/appointments', element: <AppointmentsPage /> },
      { path: '/doctor-notes', element: <DoctorNotesPage /> },
      { path: '/pregnancy-end', element: <PregnancyEndPage /> },
      { path: '/genetic', element: <GeneticPage /> },
      { path: '/results', element: <ResultsPage /> },
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

import { AuthProvider, CREDITS_SOURCE, LEGAL_DOCS, useAuth, type LegalDoc } from '@alovia/shared'
import { Logo, Markdown, PlaceholderPage, SignInForm } from '@alovia/ui'
import { QueryClientProvider } from '@tanstack/react-query'
import {
  createBrowserRouter,
  Link,
  Navigate,
  Outlet,
  RouterProvider,
  useNavigate,
} from 'react-router'

import { AccountGate } from '../components/AccountGate'
import { useMe } from '../components/DoctorShell'
import { authClient, queryClient } from './services'

function PublicLayout() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-3xl flex-col gap-6 px-4 py-6">
      <header>
        <Link to="/" className="no-underline">
          <Logo />
        </Link>
      </header>
      <main id="main" className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-border pt-4 text-sm">
        <nav aria-label="Legal">
          <ul className="flex flex-wrap gap-x-4 gap-y-2">
            {LEGAL_DOCS.map((doc) => (
              <li key={doc.path}>
                <Link to={doc.path}>{doc.title}</Link>
              </li>
            ))}
            <li>
              <Link to="/about">About</Link>
            </li>
          </ul>
        </nav>
      </footer>
    </div>
  )
}

function SignInPage() {
  const { client, session, loading } = useAuth()
  const navigate = useNavigate()
  if (!loading && session) return <Navigate to="/home" replace />
  return (
    <section className="flex max-w-md flex-col gap-4">
      <h1>Doctor sign-in</h1>
      <p className="text-muted">Research prototype. Not for clinical use. Use test data only.</p>
      <SignInForm
        onSubmit={async (email, password) => {
          const { error } = await client.auth.signInWithPassword({ email, password })
          if (error) return 'Email or password is not correct, or the email is not confirmed yet.'
          navigate('/home')
          return null
        }}
      />
      <p>Doctor accounts are invited by the administrator.</p>
    </section>
  )
}

function LegalPage({ doc }: { doc: LegalDoc }) {
  return (
    <article aria-label={doc.title}>
      <Markdown source={doc.source} />
    </article>
  )
}

function AboutPage() {
  return (
    <article className="flex flex-col gap-4">
      <h1>About Alovia</h1>
      <p>A woman-centric pregnancy companion web app with a doctor dashboard.</p>
      <p className="font-semibold">
        Research prototype (academic capstone, MJCET AI &amp; DS). Not for clinical use. Use test
        data only.
      </p>
      {/* TODO(OPEN): team names, supervisor and privacy contact email (owner to provide) */}
      <p>Team, supervisor and contact email: to be added.</p>
      <Markdown source={CREDITS_SOURCE} />
    </article>
  )
}

/** Admin screens are for the admin role only (Dashboard spec §21). */
function AdminOnly() {
  const me = useMe()
  if (me.user.role !== 'admin') return <Navigate to="/home" replace />
  return <PlaceholderPage title="Admin" />
}

function NotFound() {
  return (
    <section className="flex flex-col gap-4">
      <h1>We couldn't find this.</h1>
      <Link to="/">Back to the start page</Link>
    </section>
  )
}

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: <Navigate to="/home" replace /> },
      { path: '/signin', element: <SignInPage /> },
      { path: '/about', element: <AboutPage /> },
      ...LEGAL_DOCS.map((doc) => ({ path: doc.path, element: <LegalPage doc={doc} /> })),
      { path: '*', element: <NotFound /> },
    ],
  },
  {
    element: <AccountGate />,
    children: [
      // TODO(Phase 5): Dashboard spec screens (inbox, patient list, reviews, admin)
      { path: '/home', element: <PlaceholderPage title="Home" /> },
      { path: '/patients', element: <PlaceholderPage title="Patients" /> },
      { path: '/genetic-review', element: <PlaceholderPage title="Genetic review" /> },
      { path: '/rule-review', element: <PlaceholderPage title="Rule review" /> },
      { path: '/admin', element: <AdminOnly /> },
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

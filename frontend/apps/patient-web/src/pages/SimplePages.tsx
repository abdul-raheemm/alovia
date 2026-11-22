import { CREDITS_SOURCE, useAuth, type LegalDoc } from '@alovia/shared'
import { Button, Card, Markdown, SignInForm, ThemeSwitch } from '@alovia/ui'
import { Link, Navigate, useNavigate } from 'react-router'

import { useJourneyHome } from '../app/useJourneyHome'
import { END_TITLE } from './PregnancyEndPage'

export function SignInPage() {
  const { client, session, loading } = useAuth()
  const navigate = useNavigate()
  if (!loading && session) return <Navigate to="/home" replace />
  return (
    <section className="flex max-w-md flex-col gap-4">
      <h1>Sign in</h1>
      <SignInForm
        onSubmit={async (email, password) => {
          const { error } = await client.auth.signInWithPassword({ email, password })
          if (error) return 'Email or password is not correct, or the email is not confirmed yet.'
          navigate('/home')
          return null
        }}
      />
      <p>New here? Ask your doctor for an invite link.</p>
    </section>
  )
}

export function CheckEmailPage() {
  return (
    <section className="flex flex-col gap-4">
      <h1>Check your email</h1>
      <Card>
        <p>
          We sent you a confirmation link. Open it on this device to finish setting up your account.
        </p>
      </Card>
    </section>
  )
}

export function LegalPage({ doc }: { doc: LegalDoc }) {
  return (
    <article aria-label={doc.title}>
      <Markdown source={doc.source} />
    </article>
  )
}

/** About page (COMPLIANCE_CHECKLIST item 16) and credits (CREDITS.md). */
export function AboutPage() {
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

/** More: theme switch, legal pages, sign out. Settings (UX_FLOWS P12) grow here in later phases. */
export function MorePage() {
  const { client } = useAuth()
  const home = useJourneyHome()
  return (
    <section className="flex flex-col gap-6">
      <h1>More</h1>
      <Card>
        <ThemeSwitch />
      </Card>
      <Card>
        <h2 className="mb-2">My pregnancy</h2>
        <ul className="flex flex-col gap-2">
          <li>
            <Link className="tap" to="/dates">
              Pregnancy dates
            </Link>
          </li>
          {/* DEC-112: Doctor notes moved here from the bottom bar */}
          <li>
            <Link className="tap" to="/doctor-notes">
              Doctor notes
            </Link>
          </li>
          {/* §11.1 entry, only while the pregnancy is active */}
          {home.data && home.data.state !== 'ended' && (
            <li>
              <Link className="tap" to="/pregnancy-end">
                {END_TITLE}
              </Link>
            </li>
          )}
        </ul>
      </Card>
      <Card>
        {/* Journey §4.1: More holds Genetic risk (Module 3) */}
        <h2 className="mb-2">Checks</h2>
        <ul className="flex flex-col gap-2">
          <li>
            <Link className="tap" to="/genetic">
              Genetic risk
            </Link>
          </li>
          <li>
            {/* UX_FLOWS P10: results her doctor shared (Dashboard §10) */}
            <Link className="tap" to="/results">
              My results
            </Link>
          </li>
        </ul>
      </Card>
      <Card>
        <h2 className="mb-2">Legal</h2>
        <ul className="flex flex-col gap-2">
          <li>
            <Link className="tap" to="/privacy">
              Privacy Policy
            </Link>
          </li>
          <li>
            <Link className="tap" to="/terms">
              Terms of Use
            </Link>
          </li>
          <li>
            <Link className="tap" to="/disclaimer">
              Medical Disclaimer
            </Link>
          </li>
          <li>
            <Link className="tap" to="/about">
              About
            </Link>
          </li>
        </ul>
      </Card>
      <Button variant="secondary" className="self-start" onClick={() => void client.auth.signOut()}>
        Sign out
      </Button>
    </section>
  )
}

export function NotFoundPage() {
  return (
    <section className="flex flex-col gap-4">
      <h1>We couldn't find this.</h1>
      <Link to="/">Back to the start page</Link>
    </section>
  )
}

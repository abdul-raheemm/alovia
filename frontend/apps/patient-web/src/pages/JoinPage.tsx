import { CONSENT_VERSION, useAuth, userMessage, type InviteCheck, type Me } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton, TextField } from '@alovia/ui'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router'
import { z } from 'zod'

import { pendingConsentVersion, pendingInviteCode } from '../app/pending'
import { api } from '../app/services'
import { ConsentBoxes } from '../components/ConsentForm'

const INVALID = "This invite link isn't valid. Please ask your doctor for a new one."

const schema = z.object({
  email: z.email({ error: 'Enter a valid email address.' }),
  password: z.string().min(1, { error: 'Enter a password.' }),
})
type SignUpValues = z.infer<typeof schema>

/** Sign up only from a valid invite link (UX_FLOWS P1, DEC-024). */
export function JoinPage() {
  const [params] = useSearchParams()
  const code = params.get('code')?.trim() ?? ''
  const { session, loading, client } = useAuth()

  // kept for the email-confirmation round trip; only for someone not signed in, so a
  // signed-in patient's app never tries to link someone else's invite
  useEffect(() => {
    if (code && !loading && !session) pendingInviteCode.set(code)
  }, [code, loading, session])

  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<Me>('/me'),
    enabled: !!session,
    retry: false,
  })

  const check = useQuery({
    queryKey: ['invite-check', code],
    queryFn: () => api.get<InviteCheck>(`/invites/${encodeURIComponent(code)}/check`),
    enabled: !!code && !session,
  })

  if (!loading && session) {
    if (me.isPending) return <PageSkeleton />
    // someone who already has a patient account opened an invite link: say so, never jump
    // silently into her own app (the invite is for a new account)
    if (me.data?.patient) {
      return (
        <SignedInNotice email={me.data.user.email} onSignOut={() => void client.auth.signOut()} />
      )
    }
    // back from the confirmation email, not linked yet: the account gate links the invite
    return <Navigate to="/home" replace />
  }
  if (!code) return <Invalid />
  if (check.isPending) return <PageSkeleton />
  if (check.isError) {
    return (
      <ErrorState
        message={userMessage(check.error, 'patient')}
        onRetry={() => void check.refetch()}
      />
    )
  }
  if (!check.data.valid) return <Invalid />
  return <SignUpForm code={code} />
}

function SignedInNotice({ email, onSignOut }: { email: string; onSignOut: () => void }) {
  return (
    <Card role="alert" className="flex flex-col gap-3">
      <p>
        You are signed in as {email}. This invite link is for a new account. Sign out to use it.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button onClick={onSignOut}>Sign out</Button>
        <Link to="/home" className="self-center">
          Go to my app
        </Link>
      </div>
    </Card>
  )
}

function Invalid() {
  return (
    <Card role="alert" className="flex flex-col gap-3">
      <p>{INVALID}</p>
      <Link to="/">Back to the start page</Link>
    </Card>
  )
}

function SignUpForm({ code }: { code: string }) {
  const { client } = useAuth()
  const navigate = useNavigate()
  const [age, setAge] = useState(false)
  const [agree, setAgree] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignUpValues>({ resolver: zodResolver(schema) })

  async function onSubmit(values: SignUpValues) {
    setError(null)
    const { data, error: authError } = await client.auth.signUp({
      email: values.email,
      password: values.password,
      options: {
        emailRedirectTo: `${window.location.origin}/join?code=${encodeURIComponent(code)}`,
      },
    })
    if (authError) {
      setError(authError.message)
      return
    }
    // Supabase hides whether an email is taken: a known email comes back with no identities
    if (data.user && data.user.identities?.length === 0) {
      setError('An account with this email exists. Sign in instead.')
      return
    }
    pendingConsentVersion.set(CONSENT_VERSION) // both boxes were ticked to get here
    navigate(data.session ? '/home' : '/check-email')
  }

  return (
    <section className="flex flex-col gap-4">
      <h1>Create your account</h1>
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
        {error && (
          <ErrorState message={error}>
            {error.includes('Sign in') && <Link to="/signin">Go to sign in</Link>}
          </ErrorState>
        )}
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <ConsentBoxes age={age} agree={agree} onAge={setAge} onAgree={setAgree} />
        <Button type="submit" disabled={!(age && agree)} loading={isSubmitting}>
          Continue
        </Button>
      </form>
    </section>
  )
}

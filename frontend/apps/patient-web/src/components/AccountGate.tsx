import { ApiError, CONSENT_VERSION, userMessage, useAuth, type Me } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState, type ReactNode } from 'react'
import { Navigate } from 'react-router'

import { patientGateStep } from '../app/gate'
import { pendingConsentVersion, pendingInviteCode } from '../app/pending'
import { api } from '../app/services'
import { ConsentForm } from './ConsentForm'

/** Signed-in area guard: needs a session, a linked patient account and the current consent. */
export function AccountGate({ children }: { children: ReactNode }) {
  const { session, loading, client } = useAuth()
  const queryClient = useQueryClient()
  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<Me>('/me'),
    enabled: !!session,
  })
  const link = useMutation({
    mutationFn: (code: string) => api.post<Me>('/patient/link', { code }),
    onSuccess: (data) => {
      pendingInviteCode.clear()
      queryClient.setQueryData(['me'], data)
    },
    onError: () => pendingInviteCode.clear(), // a bad code will not get better; ask for a new one
  })
  const consent = useMutation({
    mutationFn: () =>
      api.post('/me/consent', { consent_version: CONSENT_VERSION, age_confirmed_18_plus: true }),
    onSuccess: () => {
      pendingConsentVersion.clear()
      void queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  const step = patientGateStep({
    me: me.data,
    meError: link.isPending || link.isSuccess ? null : me.error,
    pendingCode: pendingInviteCode.get(),
    pendingConsentVersion: pendingConsentVersion.get(),
    currentConsentVersion: CONSENT_VERSION,
  })

  const linkIdle = link.isIdle
  const linkMutate = link.mutate
  const consentIdle = consent.isIdle
  const consentMutate = consent.mutate
  useEffect(() => {
    const code = pendingInviteCode.get()
    if (step === 'link' && linkIdle && code) linkMutate(code)
    if (step === 'consent-auto' && consentIdle) consentMutate()
  }, [step, linkIdle, linkMutate, consentIdle, consentMutate])

  const signOut = () => void client.auth.signOut()

  if (loading) return <Connecting />
  if (!session) return <Navigate to="/signin" replace />
  if (link.isError)
    return <Problem message={userMessage(link.error, 'patient')} onSignOut={signOut} />
  if (consent.isError) {
    return <Problem message={userMessage(consent.error, 'patient')} onSignOut={signOut} />
  }
  switch (step) {
    case 'ready':
      return <>{children}</>
    case 'error':
      return (
        <div className="p-4">
          <ErrorState
            message={userMessage(me.error, 'patient')}
            onRetry={() => void me.refetch()}
          />
        </div>
      )
    case 'not-set-up':
      return (
        <Problem
          message={`${me.error instanceof ApiError ? me.error.message : ''} Please open the invite link from your doctor.`}
          onSignOut={signOut}
        />
      )
    case 'wrong-app':
      return (
        <Problem
          message="This app is for patients. Doctors and admins use the doctor app."
          onSignOut={signOut}
        />
      )
    case 'consent-form':
      return (
        <div className="mx-auto max-w-3xl p-4">
          <ConsentForm busy={consent.isPending} onAccept={() => consent.mutate()} />
        </div>
      )
    default:
      return <Connecting />
  }
}

/** Loading, with the cold-start note after a few seconds (UX_FLOWS §0, ERROR_HANDLING §2). */
function Connecting() {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 3000)
    return () => clearTimeout(t)
  }, [])
  return (
    <div>
      <PageSkeleton />
      {slow && (
        <p role="status" className="px-4 text-muted">
          Connecting… this can take up to a minute the first time.
        </p>
      )}
    </div>
  )
}

function Problem({ message, onSignOut }: { message: string; onSignOut: () => void }) {
  return (
    <div className="mx-auto max-w-xl p-4">
      <Card role="alert" className="flex flex-col items-start gap-4">
        <p>{message}</p>
        <Button variant="secondary" onClick={onSignOut}>
          Sign out
        </Button>
      </Card>
    </div>
  )
}

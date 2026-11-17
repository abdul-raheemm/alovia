import { userMessage, useAuth, type Me } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router'

import { doctorGateStep } from '../app/gate'
import { api } from '../app/services'
import { ConsentStep } from './ConsentStep'
import { DoctorShell } from './DoctorShell'

/** Signed-in area guard: needs a session, an active doctor or admin account and the
 * current consent. */
export function AccountGate() {
  const { session, loading, client } = useAuth()
  const me = useQuery({ queryKey: ['me'], queryFn: () => api.get<Me>('/me'), enabled: !!session })
  const signOut = () => void client.auth.signOut()

  if (loading) return <Connecting />
  if (!session) return <Navigate to="/signin" replace />
  const step = doctorGateStep(me.data, me.error)
  switch (step) {
    case 'consent':
      return <ConsentStep />
    case 'ready':
      return <DoctorShell me={me.data as Me} />
    case 'error':
      return (
        <div className="p-4">
          <ErrorState message={userMessage(me.error, 'doctor')} onRetry={() => void me.refetch()} />
        </div>
      )
    case 'not-set-up':
      return (
        <Problem
          message="Your account is not set up yet. Please ask the administrator."
          onSignOut={signOut}
        />
      )
    case 'wrong-app':
      return (
        <Problem
          message="This app is for doctors and admins. Patients use the patient app."
          onSignOut={signOut}
        />
      )
    default:
      return <Connecting />
  }
}

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

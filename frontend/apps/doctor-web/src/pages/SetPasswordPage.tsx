import { useAuth } from '@alovia/shared'
import { Button, TextField } from '@alovia/ui'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'

/** UX_FLOWS D1 / DEC-101: the admin's invite email opens this page signed in (Supabase reads
 * the link); the doctor chooses a password, then continues to Home. Password rules are
 * Supabase's own until Phase 8 (SECURITY §1). */
export function SetPasswordPage() {
  const { client, session, loading } = useAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [repeat, setRepeat] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (loading) return <p role="status">Checking your invite link…</p>
  if (!session) {
    return (
      <section className="flex max-w-md flex-col gap-4">
        <h1>Set your password</h1>
        <p>This invite link is not valid any more. Please ask the administrator for a new one.</p>
        <Link to="/signin">Go to sign-in</Link>
      </section>
    )
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    const found: Record<string, string> = {}
    if (!password) found.password = 'Enter a password.'
    if (password !== repeat) found.repeat = 'The passwords do not match.'
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length) return
    setBusy(true)
    const { error } = await client.auth.updateUser({ password })
    setBusy(false)
    if (error) setFormError('The password could not be saved. Please try a stronger password.')
    else void navigate('/home')
  }

  return (
    <section className="flex max-w-md flex-col gap-4">
      <h1>Set your password</h1>
      <p className="text-muted">
        Signed in as {session.user.email}. Research prototype; test data only.
      </p>
      <form noValidate onSubmit={(e) => void submit(e)} className="flex flex-col gap-3">
        <TextField
          label="New password"
          type="password"
          autoComplete="new-password"
          value={password}
          error={errors.password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <TextField
          label="Repeat the password"
          type="password"
          autoComplete="new-password"
          value={repeat}
          error={errors.repeat}
          onChange={(e) => setRepeat(e.target.value)}
        />
        {formError && (
          <p role="alert" className="text-urgent">
            {formError}
          </p>
        )}
        <Button type="submit" className="self-start" loading={busy}>
          Save password
        </Button>
      </form>
    </section>
  )
}

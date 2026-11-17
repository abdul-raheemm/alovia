import { useState, type FormEvent } from 'react'

import { Button } from './Button'
import { ErrorState } from './States'
import { TextField } from './Field'

/** Email + password sign-in used by both apps. `onSubmit` returns an error message or null. */
export function SignInForm({
  onSubmit,
}: {
  onSubmit: (email: string, password: string) => Promise<string | null>
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [touched, setTouched] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setTouched(true)
    if (!email.trim() || !password) return
    setBusy(true)
    setError(await onSubmit(email.trim(), password))
    setBusy(false)
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      {error && <ErrorState message={error} />}
      <TextField
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={touched && !email.trim() ? 'Enter your email.' : undefined}
      />
      <TextField
        label="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={touched && !password ? 'Enter your password.' : undefined}
      />
      <Button type="submit" loading={busy}>
        Sign in
      </Button>
    </form>
  )
}

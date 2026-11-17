import { CONSENT_VERSION, consentParts, userMessage } from '@alovia/shared'
import { Button, Card, CheckboxField, ErrorState, Markdown } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'

import { api } from '../app/services'

const { body, checkboxes } = consentParts()

/** The app-wide consent (docs/legal/CONSENT_TEXT.md), word for word, both boxes unticked.
 * Doctors and admins accept it once at their first sign-in (owner decision 2026-11-17);
 * the same text and route as the patient app. */
export function ConsentStep() {
  const queryClient = useQueryClient()
  const [age, setAge] = useState(false)
  const [agree, setAgree] = useState(false)
  const accept = useMutation({
    mutationFn: () =>
      api.post('/me/consent', { consent_version: CONSENT_VERSION, age_confirmed_18_plus: true }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['me'] }),
  })
  return (
    <main id="main" className="mx-auto max-w-3xl p-4">
      <h1 className="mb-4">Before you start</h1>
      <Card className="flex flex-col gap-4">
        <Markdown source={body} />
        <CheckboxField
          label={checkboxes[0]}
          checked={age}
          onChange={(e) => setAge(e.target.checked)}
        />
        <CheckboxField
          label={checkboxes[1]}
          checked={agree}
          onChange={(e) => setAgree(e.target.checked)}
        />
        <p className="text-sm">
          Read the <Link to="/privacy">Privacy Policy</Link>, the{' '}
          <Link to="/terms">Terms of Use</Link> and the full <Link to="/consent">consent text</Link>
          .
        </p>
        {accept.isError && <ErrorState message={userMessage(accept.error, 'doctor')} />}
        <Button
          className="self-start"
          disabled={!(age && agree)}
          loading={accept.isPending}
          onClick={() => accept.mutate()}
        >
          Continue
        </Button>
      </Card>
    </main>
  )
}

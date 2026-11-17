import { consentParts } from '@alovia/shared'
import { Button, Card, CheckboxField, Markdown } from '@alovia/ui'
import { useState } from 'react'
import { Link } from 'react-router'

const { body, checkboxes } = consentParts()

/** The app-wide consent (docs/legal/CONSENT_TEXT.md), word for word, with both boxes unticked.
 * Continue is enabled only when both are ticked. Used when consent was not recorded at sign-up. */
export function ConsentForm({ busy, onAccept }: { busy: boolean; onAccept: () => void }) {
  const [age, setAge] = useState(false)
  const [agree, setAgree] = useState(false)
  return (
    <Card className="flex flex-col gap-4">
      <Markdown source={body} />
      <ConsentBoxes age={age} agree={agree} onAge={setAge} onAgree={setAgree} />
      <Button disabled={!(age && agree)} loading={busy} onClick={onAccept}>
        Continue
      </Button>
    </Card>
  )
}

export function ConsentBoxes({
  age,
  agree,
  onAge,
  onAgree,
}: {
  age: boolean
  agree: boolean
  onAge: (v: boolean) => void
  onAgree: (v: boolean) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <CheckboxField
        label={checkboxes[0]}
        checked={age}
        onChange={(e) => onAge(e.target.checked)}
      />
      <CheckboxField
        label={checkboxes[1]}
        checked={agree}
        onChange={(e) => onAgree(e.target.checked)}
      />
      <p className="text-sm">
        Read the <Link to="/privacy">Privacy Policy</Link>, the{' '}
        <Link to="/terms">Terms of Use</Link> and the full <Link to="/consent">consent text</Link>.
      </p>
    </div>
  )
}

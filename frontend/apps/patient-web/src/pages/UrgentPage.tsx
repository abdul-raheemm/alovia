import { ApiError, userMessage, type CheckinInput } from '@alovia/shared'
import { Button, Card, CheckboxField, ErrorState, FieldError } from '@alovia/ui'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

import { cannotReach, offlineWarnings, type Level } from '../app/symptoms'
import { SYMPTOM_BUNDLE } from '../app/symptomBundle.generated'
import { useJourneyHome } from '../app/useJourneyHome'
import { queueCheckin, useSubmitCheckin, useVocabulary } from '../app/useSymptoms'
import { AdviceScreen, AfterEndNotice, NotMonitoredNotice } from '../components/symptoms/Advice'
import { ChoiceGroup } from '../components/symptoms/Fields'

const TITLE = 'I have an urgent symptom' // Journey spec §4.3 urgent button

/** Urgent button (Symptom spec §4.2, UX_FLOWS P6): warning signs only, one tap + Submit, L1/L2
 * advice at once. The list and the advice are bundled, so they never wait for the backend; if
 * it cannot be reached, the L1 advice is shown and the check-in is sent later (DEC-060). */
export function UrgentPage() {
  const vocab = useVocabulary()
  const home = useJourneyHome()
  const submit = useSubmitCheckin()
  const navigate = useNavigate()
  const [checked, setChecked] = useState<Record<string, boolean>>({})
  const [labourDuration, setLabourDuration] = useState<string>()
  const [problem, setProblem] = useState<string | null>(null)
  const [result, setResult] = useState<{
    level: Level
    keys: readonly string[]
    offline: boolean
  } | null>(null)

  const ended = vocab.data ? !vocab.data.logging_open : home.data?.state === 'ended'
  if (ended) return <AfterEndNotice title={TITLE} />
  if (result) {
    return (
      <AdviceScreen
        level={result.level}
        messageKeys={result.keys}
        offline={result.offline}
        onDone={() => navigate('/home')}
      />
    )
  }

  // the backend's week-filtered list when it has loaded; the bundled list until then (§5.2)
  const week = vocab.data?.pregnancy_week ?? home.data?.pregnancy?.completed_weeks ?? null
  const signs = vocab.data
    ? vocab.data.warning.map((w) => ({ id: w.id, label: w.label, labour: w.labour_duration }))
    : offlineWarnings(week).map((w) => ({ id: w.id, label: w.label, labour: w.labourDuration }))
  const fields = submit.error instanceof ApiError ? (submit.error.fields ?? {}) : {}

  function send(e: FormEvent) {
    e.preventDefault()
    const chosen = signs.filter((s) => checked[s.id])
    if (chosen.length === 0) return setProblem('Choose at least one warning sign.')
    if (chosen.some((s) => s.labour) && !labourDuration) return setProblem('labour')
    setProblem(null)
    const body = {
      source: 'urgent_button',
      entries: chosen.map((s) => ({
        symptom: s.id,
        ...(s.labour ? { duration: labourDuration } : {}),
      })),
    } as CheckinInput
    submit.mutate(body, {
      onSuccess: (r) =>
        setResult({ level: r.red_flag_level, keys: r.message_keys, offline: false }),
      onError: (error) => {
        if (!cannotReach(error)) return
        queueCheckin(body) // §1.3: when in doubt, the stronger advice wins
        setResult({ level: 'L1', keys: ['msg_level1_go_now'], offline: true })
      },
    })
  }

  return (
    <form onSubmit={send} noValidate className="flex flex-col gap-4">
      <h1 className="font-sans">{TITLE}</h1>
      <NotMonitoredNotice />
      {submit.isError && !cannotReach(submit.error) && Object.keys(fields).length === 0 && (
        <ErrorState message={userMessage(submit.error, 'patient')} />
      )}
      <fieldset className="flex flex-col gap-1">
        <legend className="mb-2 font-semibold">Warning signs</legend>
        <Card className="flex flex-col gap-1">
          {signs.map((s) => (
            <div key={s.id}>
              <CheckboxField
                label={s.label}
                checked={!!checked[s.id]}
                onChange={(e) => setChecked((c) => ({ ...c, [s.id]: e.target.checked }))}
              />
              {s.labour && checked[s.id] && (
                <div className="ml-8">
                  <ChoiceGroup
                    legend="Duration"
                    options={SYMPTOM_BUNDLE.labourDurations}
                    value={labourDuration}
                    onChange={setLabourDuration}
                    error={problem === 'labour' ? 'Please fill this in.' : undefined}
                  />
                </div>
              )}
            </div>
          ))}
        </Card>
      </fieldset>
      {problem && problem !== 'labour' && <FieldError id="urgent-error" message={problem} />}
      {Object.keys(fields).length > 0 && (
        <FieldError id="urgent-fields" message="Please check your choices and try again." />
      )}
      <Button type="submit" variant="danger" className="self-start" loading={submit.isPending}>
        Submit
      </Button>
    </form>
  )
}

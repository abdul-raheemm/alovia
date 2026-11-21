import { ApiError, userMessage, type CheckinResult, type EntryInput } from '@alovia/shared'
import {
  Button,
  Card,
  CheckboxField,
  ErrorState,
  FieldError,
  PageSkeleton,
  TextAreaField,
  TextField,
} from '@alovia/ui'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'

import { emptyDraft, entryError, missingFields, toEntry, type CommonDraft } from '../app/symptoms'
import { useSubmitCheckin, useVocabulary } from '../app/useSymptoms'
import { AdviceScreen, AfterEndNotice, NotMonitoredNotice } from '../components/symptoms/Advice'
import { ChoiceGroup } from '../components/symptoms/Fields'

/** Log symptoms (Symptom spec §4.1, UX_FLOWS P5): Warning signs at the top, Everyday symptoms
 * below; submit shows the advice for the check-in's level at once. */
export function LogPage() {
  const vocab = useVocabulary()
  const submit = useSubmitCheckin()
  const navigate = useNavigate()
  const [warning, setWarning] = useState<Record<string, boolean>>({})
  const [labourDuration, setLabourDuration] = useState<string>()
  const [drafts, setDrafts] = useState<Record<string, CommonDraft>>({})
  const [missing, setMissing] = useState<Record<string, string[]>>({})
  const [nothing, setNothing] = useState(false)
  const [order, setOrder] = useState<string[]>([])
  const [result, setResult] = useState<CheckinResult | null>(null)

  if (vocab.isPending) return <PageSkeleton />
  if (vocab.isError) {
    return (
      <ErrorState
        message={userMessage(vocab.error, 'patient')}
        onRetry={() => void vocab.refetch()}
      />
    )
  }
  const v = vocab.data
  if (!v.logging_open) return <AfterEndNotice title="Log symptoms" />
  if (result) {
    return (
      <AdviceScreen
        level={result.red_flag_level}
        messageKeys={result.message_keys}
        onDone={() => navigate('/home')}
      />
    )
  }

  const serverFields = submit.error instanceof ApiError ? (submit.error.fields ?? {}) : {}
  const fieldError = (id: string, field: string) =>
    missing[id]?.includes(field)
      ? 'Please fill this in.'
      : entryError(serverFields, order.indexOf(id), field)
  const otherError =
    submit.isError && Object.keys(serverFields).length === 0
      ? userMessage(submit.error, 'patient')
      : null
  const setDraft = (id: string, change: Partial<CommonDraft>) =>
    setDrafts((d) => ({ ...d, [id]: { ...(d[id] ?? emptyDraft()), ...change } }))

  function send(e: FormEvent) {
    e.preventDefault()
    const entries: EntryInput[] = []
    const ids: string[] = []
    const gaps: Record<string, string[]> = {}
    for (const w of v.warning) {
      if (!warning[w.id]) continue
      if (w.labour_duration && !labourDuration) gaps[w.id] = ['duration']
      entries.push({
        symptom: w.id,
        ...(w.labour_duration ? { duration: labourDuration } : {}),
      } as EntryInput)
      ids.push(w.id)
    }
    for (const c of v.common) {
      const d = drafts[c.id]
      if (!d) continue
      const gap = missingFields(c, d)
      if (gap.length) gaps[c.id] = gap
      entries.push(toEntry(c, d))
      ids.push(c.id)
    }
    setNothing(entries.length === 0)
    setMissing(gaps)
    setOrder(ids)
    if (entries.length === 0 || Object.keys(gaps).length > 0) return
    submit.mutate({ source: 'form', entries }, { onSuccess: setResult })
  }

  return (
    <form onSubmit={send} noValidate className="flex flex-col gap-6">
      <h1>Log symptoms</h1>
      <NotMonitoredNotice />
      <p className="text-sm">
        <Link to="/log/history">Your symptom history</Link>
      </p>
      {otherError && <ErrorState message={otherError} />}

      <section aria-labelledby="warning-heading" className="flex flex-col gap-2">
        <h2 id="warning-heading" className="font-sans">
          Warning signs
        </h2>
        <Card className="flex flex-col gap-1">
          {v.warning.map((w) => (
            <div key={w.id}>
              <CheckboxField
                label={w.label}
                checked={!!warning[w.id]}
                onChange={(e) => setWarning((s) => ({ ...s, [w.id]: e.target.checked }))}
              />
              {w.labour_duration && warning[w.id] && (
                <div className="ml-8">
                  <ChoiceGroup
                    legend="Duration"
                    options={v.labour_durations}
                    value={labourDuration}
                    onChange={setLabourDuration}
                    error={fieldError(w.id, 'duration')}
                  />
                </div>
              )}
            </div>
          ))}
        </Card>
      </section>

      <section aria-labelledby="everyday-heading" className="flex flex-col gap-2">
        <h2 id="everyday-heading">Everyday symptoms</h2>
        <div className="flex flex-col gap-3">
          {v.common.map((c) => {
            const d = drafts[c.id]
            return (
              <Card key={c.id} className="flex flex-col gap-3">
                <CheckboxField
                  label={c.label}
                  checked={!!d}
                  onChange={(e) =>
                    setDrafts((all) =>
                      e.target.checked
                        ? { ...all, [c.id]: emptyDraft() }
                        : Object.fromEntries(Object.entries(all).filter(([id]) => id !== c.id)),
                    )
                  }
                />
                {d && (
                  <div className="ml-8 flex flex-col gap-3">
                    {c.text && (
                      <TextField
                        label={c.text.required ? c.text.label : `${c.text.label} (optional)`}
                        value={d.text ?? ''}
                        maxLength={c.text.max_length}
                        onChange={(e) => setDraft(c.id, { text: e.target.value })}
                        error={fieldError(c.id, c.text.field)}
                      />
                    )}
                    {c.choice && (
                      <ChoiceGroup
                        legend={c.label}
                        options={c.choice.options}
                        value={d.choice}
                        onChange={(choice) => setDraft(c.id, { choice })}
                        error={fieldError(c.id, c.choice.field)}
                      />
                    )}
                    {c.severity && (
                      <ChoiceGroup
                        legend="Severity"
                        options={v.severities}
                        value={d.severity}
                        onChange={(severity) => setDraft(c.id, { severity })}
                        error={fieldError(c.id, 'severity')}
                      />
                    )}
                    {c.duration && (
                      <ChoiceGroup
                        legend="Duration"
                        options={v.durations}
                        value={d.duration}
                        onChange={(duration) => setDraft(c.id, { duration })}
                        error={fieldError(c.id, 'duration')}
                      />
                    )}
                    {c.body_area && (
                      <ChoiceGroup
                        legend={c.body_area.required ? 'Body area' : 'Body area (optional)'}
                        options={c.body_area.choices.map((a): [string, string] => [
                          a,
                          v.body_areas[a] ?? a,
                        ])}
                        value={d.body_area}
                        onChange={(body_area) => setDraft(c.id, { body_area })}
                        error={fieldError(c.id, 'body_area')}
                      />
                    )}
                    {c.puqe && (
                      <div className="flex flex-col gap-3">
                        {v.puqe_questions.map((q, i) => (
                          <ChoiceGroup
                            key={q.id}
                            legend={q.text}
                            options={Object.entries(q.answers).sort(([a], [b]) => +a - +b)}
                            value={d.puqe[i]?.toString()}
                            onChange={(score) => {
                              const puqe = [...d.puqe]
                              puqe[i] = Number(score)
                              setDraft(c.id, { puqe })
                            }}
                          />
                        ))}
                        <FieldError
                          id={`${c.id}-puqe-error`}
                          message={fieldError(c.id, 'puqe_answers')}
                        />
                        <p className="text-sm text-muted">
                          Questions: {v.puqe_source.title} ({v.puqe_source.publisher})
                        </p>
                      </div>
                    )}
                    {Object.entries(c.flags).map(([flag, label]) => (
                      <CheckboxField
                        key={flag}
                        label={label}
                        checked={!!d.flags[flag]}
                        onChange={(e) =>
                          setDraft(c.id, { flags: { ...d.flags, [flag]: e.target.checked } })
                        }
                      />
                    ))}
                    <TextField
                      label="Time (optional)"
                      type="time"
                      value={d.occurred_at ?? ''}
                      onChange={(e) => setDraft(c.id, { occurred_at: e.target.value })}
                    />
                    <TextAreaField
                      label="Notes (optional)"
                      value={d.notes ?? ''}
                      maxLength={500}
                      onChange={(e) => setDraft(c.id, { notes: e.target.value })}
                    />
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      </section>

      {nothing && <FieldError id="nothing-error" message="Choose at least one symptom." />}
      <Button type="submit" className="self-start" loading={submit.isPending}>
        Submit
      </Button>
    </form>
  )
}

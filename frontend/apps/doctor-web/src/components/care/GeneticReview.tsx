import {
  ApiError,
  chanceLabel,
  CONDITIONS,
  draftFromInputs,
  evidenceFor,
  GENETIC_BUNDLE,
  geneticText,
  missingAnswers,
  outcomeLabel,
  questionFor,
  sectionShown,
  toGeneticInput,
  userMessage,
  type ConditionKey,
  type DoctorAssessment,
  type GeneticDraft,
} from '@alovia/shared'
import { Button, Card, ErrorState, FieldError, PageSkeleton, TextAreaField } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useId, useState } from 'react'

import { formatDateTime } from '../../app/patients'
import { api } from '../../app/services'
import { StickyActions } from '../StickyActions'

type Condition = DoctorAssessment['result']['conditions'][number]
type Outcomes = NonNullable<Condition['outcomes']>

function OutcomeList({ outcomes }: { outcomes: Outcomes }) {
  return (
    <ul>
      {outcomes.map((o) => (
        <li key={o.outcome}>
          {outcomeLabel(o.outcome)}: <strong>{chanceLabel(o.chance)}</strong>
        </li>
      ))}
    </ul>
  )
}

/** The engine's result as stored: numbers, statuses and rule IDs. Nothing is editable (§10.3). */
function ResultView({ a }: { a: DoctorAssessment }) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted">
        {formatDateTime(a.created_at)} · rules {a.rules_version} · priority{' '}
        <strong>{a.priority}</strong>
        {a.risk_indicated ? ' · risk indicated' : ''}
        {a.by_doctor ? ' · corrected by a doctor' : ''}
      </p>
      {a.result.message_keys.map((k) => (
        <p key={k} className="rounded-md bg-primary-soft p-2 text-sm">
          {geneticText(k)}
        </p>
      ))}
      <div className="grid gap-3 lg:grid-cols-3">
        {a.result.conditions.map((c) => (
          <Card key={c.condition} className="flex flex-col gap-2">
            <h4>{GENETIC_BUNDLE.conditions[c.condition as ConditionKey]}</h4>
            <p className="text-sm">
              Status: <strong>{c.status}</strong> · rule {c.rule_id}
            </p>
            {c.outcomes && <OutcomeList outcomes={c.outcomes} />}
            {c.outcomes_if_boy && c.outcomes_if_girl && (
              <div className="grid gap-2 sm:grid-cols-2">
                <div>
                  <p className="font-semibold">If the baby is a boy</p>
                  <OutcomeList outcomes={c.outcomes_if_boy} />
                </div>
                <div>
                  <p className="font-semibold">If the baby is a girl</p>
                  <OutcomeList outcomes={c.outcomes_if_girl} />
                </div>
              </div>
            )}
            {[...(c.warnings ?? []), ...(c.notes ?? [])].map((k) => (
              <p key={k} className="text-sm">
                {geneticText(k)}
              </p>
            ))}
          </Card>
        ))}
      </div>
    </div>
  )
}

function Select({
  label,
  value,
  options,
  onChange,
  error,
}: {
  label: string
  value: string | undefined
  options: [string, string][]
  onChange: (v: string) => void
  error?: string
}) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-semibold">
        {label}
      </label>
      <select
        id={id}
        value={value ?? ''}
        aria-invalid={error ? true : undefined}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
      >
        <option value="">Choose…</option>
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
      <FieldError id={`${id}-error`} message={error} />
    </div>
  )
}

/** Genetic §10.3 Correct inputs: the answers as submitted, editable; the engine re-runs on
 * the server and the result goes straight to reviewed with the note. */
function CorrectForm({
  a,
  onDone,
  onCancel,
}: {
  a: DoctorAssessment
  onDone: () => void
  onCancel: () => void
}) {
  const [draft, setDraft] = useState<GeneticDraft>(() => draftFromInputs(a.inputs))
  const [note, setNote] = useState('')
  const [missing, setMissing] = useState<string[]>([])
  const save = useMutation({
    mutationFn: () =>
      api.post<DoctorAssessment>(`/doctor/genetic/assessments/${a.id}/correct`, {
        inputs: toGeneticInput(draft),
        doctor_note: note.trim(),
      }),
    onSuccess: onDone,
  })
  const server = save.error instanceof ApiError ? (save.error.fields ?? {}) : {}
  const err = (path: string) =>
    missing.includes(path) ? 'Please answer this.' : server[path] ? 'Please check this.' : undefined
  const setSection = (c: ConditionKey, change: Partial<GeneticDraft[ConditionKey]>) =>
    setDraft((d) => ({ ...d, [c]: { ...d[c], ...change } }))
  return (
    <form
      noValidate
      className="max-w-3xl flex flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault()
        const gaps = missingAnswers(draft)
        if (!note.trim()) gaps.push('doctor_note')
        setMissing(gaps)
        if (gaps.length === 0) save.mutate()
      }}
    >
      <h4>Correct inputs</h4>
      {CONDITIONS.map((c) => {
        const s = draft[c]
        return (
          <fieldset key={c} className="flex flex-col gap-3 rounded-md border border-border p-3">
            <legend className="px-1 font-semibold">{GENETIC_BUNDLE.conditions[c]}</legend>
            {c !== 'haemoglobin_group' && (
              <Select
                label={questionFor(GENETIC_BUNDLE.entryQuestion, c)}
                value={s.entry}
                options={Object.entries(GENETIC_BUNDLE.entryAnswers)}
                onChange={(entry) => setSection(c, { entry })}
                error={err(`${c}.entry`)}
              />
            )}
            {sectionShown(c, s) && (
              <div className="grid gap-3 sm:grid-cols-2">
                {(['mother', 'father'] as const).map((who) => (
                  <div key={who} className="flex flex-col gap-2">
                    <Select
                      label={`${who === 'mother' ? 'Mother' : 'Father'}: status`}
                      value={s[who].status}
                      options={Object.entries(GENETIC_BUNDLE.statuses[c][who])}
                      onChange={(status) => setSection(c, { [who]: { status } })}
                      error={err(`${c}.${who}.status`)}
                    />
                    {evidenceFor(c, s[who].status).length > 0 && (
                      <Select
                        label={`${who === 'mother' ? 'Mother' : 'Father'}: evidence`}
                        value={s[who].evidence}
                        options={evidenceFor(c, s[who].status)}
                        onChange={(evidence) => setSection(c, { [who]: { ...s[who], evidence } })}
                        error={err(`${c}.${who}.evidence`)}
                      />
                    )}
                  </div>
                ))}
                <Select
                  label={questionFor(GENETIC_BUNDLE.previousChildQuestion, c)}
                  value={s.previous_child}
                  options={Object.entries(GENETIC_BUNDLE.previousChildAnswers)}
                  onChange={(previous_child) => setSection(c, { previous_child })}
                  error={err(`${c}.previous_child`)}
                />
              </div>
            )}
          </fieldset>
        )
      })}
      <Select
        label={GENETIC_BUNDLE.consanguinityQuestion}
        value={draft.consanguinity}
        options={Object.entries(GENETIC_BUNDLE.consanguinityAnswers)}
        onChange={(consanguinity) => setDraft((d) => ({ ...d, consanguinity }))}
        error={err('consanguinity')}
      />
      <TextAreaField
        label="Doctor's note (required)"
        value={note}
        maxLength={2000}
        error={missing.includes('doctor_note') ? 'Please write a note.' : undefined}
        onChange={(e) => setNote(e.target.value)}
      />
      {save.isError && (
        <p role="alert" className="text-urgent">
          {userMessage(save.error, 'doctor')}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <StickyActions>
          <Button type="submit" loading={save.isPending}>
            Save correction
          </Button>
        </StickyActions>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

/** Genetic §10.3 Confirm with a note, or Correct inputs. A second doctor gets "already
 * reviewed by Dr X" from the server (Dashboard §12). */
function ReviewActions({ a, onChanged }: { a: DoctorAssessment; onChanged: () => void }) {
  const [mode, setMode] = useState<'confirm' | 'correct' | null>(null)
  const [note, setNote] = useState('')
  const [empty, setEmpty] = useState(false)
  const confirm = useMutation({
    mutationFn: () =>
      api.post<DoctorAssessment>(`/doctor/genetic/assessments/${a.id}/review`, {
        doctor_note: note.trim(),
      }),
    onSuccess: onChanged,
  })
  if (mode === 'correct') {
    return <CorrectForm a={a} onDone={onChanged} onCancel={() => setMode(null)} />
  }
  if (mode === 'confirm') {
    return (
      <form
        noValidate
        className="max-w-3xl flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          setEmpty(!note.trim())
          if (note.trim()) confirm.mutate()
        }}
      >
        <TextAreaField
          label="Doctor's note (required; the patient sees it)"
          value={note}
          maxLength={2000}
          error={empty ? 'Please write a note.' : undefined}
          onChange={(e) => setNote(e.target.value)}
        />
        {confirm.isError && (
          <p role="alert" className="text-urgent">
            {userMessage(confirm.error, 'doctor')}
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <StickyActions>
            <Button type="submit" loading={confirm.isPending}>
              Confirm review
            </Button>
          </StickyActions>
          <Button type="button" variant="ghost" onClick={() => setMode(null)}>
            Cancel
          </Button>
        </div>
      </form>
    )
  }
  return (
    <div className="flex flex-wrap gap-3">
      <Button onClick={() => setMode('confirm')}>Confirm with note</Button>
      <Button variant="secondary" onClick={() => setMode('correct')}>
        Correct inputs
      </Button>
    </div>
  )
}

export function AssessmentCard({ a, onChanged }: { a: DoctorAssessment; onChanged: () => void }) {
  return (
    <Card className="flex flex-col gap-4">
      <h3>
        {a.review_status === 'reviewed'
          ? 'Reviewed'
          : a.replaced
            ? 'Replaced by a correction'
            : 'Waiting for review'}
      </h3>
      <ResultView a={a} />
      {a.doctor_note && (
        <p className="rounded-md border border-border p-3">
          <span className="font-semibold">
            Note{a.reviewed_by_name ? ` by ${a.reviewed_by_name}` : ''}:
          </span>{' '}
          {a.doctor_note}
        </p>
      )}
      {a.review_status === 'pending_review' && !a.replaced && (
        <ReviewActions a={a} onChanged={onChanged} />
      )}
    </Card>
  )
}

/** Patient page → Genetic tab: every assessment, newest first (Dashboard §12). */
export function GeneticTab({ patientId }: { patientId: string }) {
  const qc = useQueryClient()
  const list = useQuery({
    queryKey: ['doctor-genetic', patientId],
    queryFn: () => api.get<DoctorAssessment[]>(`/doctor/patients/${patientId}/genetic`),
  })
  if (list.isPending) return <PageSkeleton />
  if (list.isError) {
    return (
      <ErrorState message={userMessage(list.error, 'doctor')} onRetry={() => void list.refetch()} />
    )
  }
  if (list.data.length === 0) {
    return (
      <Card>
        <p>No genetic check yet. The patient fills it in from her app.</p>
      </Card>
    )
  }
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['doctor-genetic'] })
    void qc.invalidateQueries({ queryKey: ['genetic-queue'] })
    void qc.invalidateQueries({ queryKey: ['doctor-patient', patientId] })
  }
  return (
    <div className="flex flex-col gap-4">
      {list.data.map((a) => (
        <AssessmentCard key={a.id} a={a} onChanged={refresh} />
      ))}
    </div>
  )
}

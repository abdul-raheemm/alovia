import { ApiError, userMessage, type PatientDetail } from '@alovia/shared'
import { Button, Card, TextField } from '@alovia/ui'
import { useQueryClient } from '@tanstack/react-query'
import { useId, useState } from 'react'

import { DUE_DATE_SOURCE, formatDay, gaLabel, PREGNANCY_STATUS } from '../../app/patients'
import { api } from '../../app/services'

const END_CHOICES = ['ended_birth', 'ended_loss', 'ended_not_specified'] as const

/** Dashboard §8.3: a clinician-confirmed due date or an ultrasound dating. The Journey date
 * rules (incl. D2) run on the server; the patient gets a "dates updated" notification. */
function DatesForm({ patient, onSaved }: { patient: PatientDetail; onSaved: () => void }) {
  const [option, setOption] = useState<'due_date' | 'ultrasound'>('due_date')
  const [dueDate, setDueDate] = useState('')
  const [scanDate, setScanDate] = useState('')
  const [weeks, setWeeks] = useState('')
  const [days, setDays] = useState('0')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const name = useId()

  async function save() {
    setFormError(null)
    const body =
      option === 'due_date'
        ? { option, due_date: dueDate }
        : { option, scan_date: scanDate, ga_weeks: Number(weeks), ga_days: Number(days) }
    const found: Record<string, string> = {}
    if (option === 'due_date' && !dueDate) found.due_date = 'Choose the due date.'
    if (option === 'ultrasound') {
      if (!scanDate) found.scan_date = 'Choose the scan date.'
      if (!Number.isInteger(Number(weeks)) || weeks === '') found.ga_weeks = 'Enter whole weeks.'
      if (!/^[0-6]$/.test(days)) found.ga_days = 'Enter 0 to 6 days.'
    }
    setErrors(found)
    if (Object.keys(found).length) return
    setBusy(true)
    try {
      await api.put(`/doctor/patients/${patient.id}/dates`, body)
      onSaved()
    } catch (err) {
      if (err instanceof ApiError && err.fields) {
        setErrors(
          Object.fromEntries(Object.keys(err.fields).map((k) => [k, 'Please check this date.'])),
        )
      }
      setFormError(userMessage(err, 'doctor'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      noValidate
      className="flex max-w-xl flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        void save()
      }}
    >
      <fieldset className="flex flex-wrap gap-4">
        <legend className="mb-1 font-semibold">Dating</legend>
        {(
          [
            ['due_date', 'Clinician-confirmed due date'],
            ['ultrasound', 'Ultrasound'],
          ] as const
        ).map(([v, l]) => (
          <label key={v} className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name={name}
              checked={option === v}
              onChange={() => setOption(v)}
              className="size-4 accent-[var(--color-primary)]"
            />
            {l}
          </label>
        ))}
      </fieldset>
      {option === 'due_date' ? (
        <TextField
          label="Due date"
          type="date"
          value={dueDate}
          error={errors.due_date}
          onChange={(e) => setDueDate(e.target.value)}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-3">
          <TextField
            label="Scan date"
            type="date"
            value={scanDate}
            error={errors.scan_date}
            onChange={(e) => setScanDate(e.target.value)}
          />
          <TextField
            label="Weeks at scan"
            inputMode="numeric"
            value={weeks}
            error={errors.ga_weeks}
            onChange={(e) => setWeeks(e.target.value)}
          />
          <TextField
            label="Days at scan"
            inputMode="numeric"
            value={days}
            error={errors.ga_days}
            onChange={(e) => setDays(e.target.value)}
          />
        </div>
      )}
      {formError && (
        <p role="alert" className="text-urgent">
          {formError}
        </p>
      )}
      <Button type="submit" className="self-start" loading={busy}>
        Save dates
      </Button>
    </form>
  )
}

/** Dashboard §17: set "pregnancy ended" with the same three choices as the patient. */
function EndForm({ patient, onSaved }: { patient: PatientDetail; onSaved: () => void }) {
  const [choice, setChoice] = useState<string>('')
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const name = useId()
  if (patient.pregnancy_status !== 'active') return null
  return (
    <form
      noValidate
      className="flex max-w-xl flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        if (!choice) return setError('Choose one.')
        if (!confirming) return setConfirming(true)
        setBusy(true)
        api
          .post(`/doctor/patients/${patient.id}/pregnancy-end`, { status: choice })
          .then(onSaved)
          .catch((err: unknown) => setError(userMessage(err, 'doctor')))
          .finally(() => setBusy(false))
      }}
    >
      <fieldset className="flex flex-col gap-1">
        <legend className="mb-1 font-semibold">How did the pregnancy end?</legend>
        {END_CHOICES.map((c) => (
          <label key={c} className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name={name}
              checked={choice === c}
              onChange={() => {
                setChoice(c)
                setError(null)
                setConfirming(false)
              }}
              className="size-4 accent-[var(--color-primary)]"
            />
            {PREGNANCY_STATUS[c]}
          </label>
        ))}
      </fieldset>
      {confirming && (
        <p role="status">
          The patient's app will stop baby-stage content. Press the button again to confirm.
        </p>
      )}
      {error && (
        <p role="alert" className="text-urgent">
          {error}
        </p>
      )}
      <Button type="submit" variant={confirming ? 'danger' : 'secondary'} loading={busy}>
        {confirming ? 'Confirm: pregnancy ended' : 'Set pregnancy ended'}
      </Button>
    </form>
  )
}

export function PregnancyTab({ patient }: { patient: PatientDetail }) {
  const qc = useQueryClient()
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['doctor-patient', patient.id] })
    void qc.invalidateQueries({ queryKey: ['doctor-patients'] })
  }
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <dl className="grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="text-sm text-muted">Status</dt>
            <dd>{PREGNANCY_STATUS[patient.pregnancy_status]}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Due date</dt>
            <dd>
              {patient.due_date ? formatDay(patient.due_date) : '—'}
              {patient.due_date_source ? ` (${DUE_DATE_SOURCE[patient.due_date_source]})` : ''}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Gestational age</dt>
            <dd>{gaLabel(patient)}</dd>
          </div>
        </dl>
      </Card>
      <section aria-labelledby="dates-heading" className="flex flex-col gap-3">
        <h2 id="dates-heading">Set dates</h2>
        <DatesForm patient={patient} onSaved={refresh} />
      </section>
      {patient.pregnancy_status === 'active' && (
        <section aria-labelledby="end-heading" className="flex flex-col gap-3">
          <h2 id="end-heading">Pregnancy ended</h2>
          <EndForm patient={patient} onSaved={refresh} />
        </section>
      )}
    </div>
  )
}

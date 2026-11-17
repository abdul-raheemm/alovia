import { ApiError, userMessage, type JourneyDatesInput, type JourneyHome } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton, TextField } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'

import { dateRuleText, formatDay, messageText, SOURCE_LABEL } from '../app/journey'
import { HOME_KEY, useJourneyHome } from '../app/useJourneyHome'
import { api } from '../app/services'

type Option = JourneyDatesInput['option']

// Journey spec §5.1: the patient chooses one way to give her dates
const OPTIONS: { value: Option; label: string }[] = [
  { value: 'lmp', label: 'First day of my last period' },
  { value: 'due_date', label: 'Due date from my doctor' },
  { value: 'ultrasound', label: 'Ultrasound scan result' },
]

/** Onboarding and changing pregnancy dates (Journey spec §5, UX_FLOWS P3). */
export function DatesPage() {
  const home = useJourneyHome()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [option, setOption] = useState<Option>('lmp')
  const [values, setValues] = useState({
    lmp_date: '',
    due_date: '',
    scan_date: '',
    ga_weeks: '',
    ga_days: '0',
  })
  const [missing, setMissing] = useState<string[]>([])
  const [confirming, setConfirming] = useState(false)

  const save = useMutation({
    mutationFn: (body: JourneyDatesInput) => api.put<JourneyHome>('/patient/journey/dates', body),
    onSuccess: (data) => {
      queryClient.setQueryData(HOME_KEY, data) // home shows the new dates and any notice
      navigate('/home')
    },
    onError: (error) => {
      // §5.3: replacing a doctor's or scan date with an estimate needs her confirmation
      setConfirming(error instanceof ApiError && !!error.fields?.confirm_override)
    },
  })

  if (home.isPending) return <PageSkeleton />
  if (home.isError) {
    return (
      <ErrorState
        message={userMessage(home.error, 'patient')}
        onRetry={() => void home.refetch()}
      />
    )
  }
  const { dates, messages } = home.data

  function body(confirm_override: boolean): JourneyDatesInput {
    if (option === 'lmp') return { option, lmp_date: values.lmp_date, confirm_override }
    if (option === 'due_date') return { option, due_date: values.due_date, confirm_override }
    return {
      option,
      scan_date: values.scan_date,
      ga_weeks: Number(values.ga_weeks),
      ga_days: Number(values.ga_days),
      confirm_override,
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    const needed =
      option === 'lmp'
        ? ['lmp_date']
        : option === 'due_date'
          ? ['due_date']
          : ['scan_date', 'ga_weeks']
    const empty = needed.filter((name) => !values[name as keyof typeof values])
    setMissing(empty)
    if (empty.length === 0) save.mutate(body(false))
  }

  const fields = save.error instanceof ApiError ? (save.error.fields ?? {}) : {}
  const fieldError = (name: string) =>
    missing.includes(name) ? 'Please fill this in.' : dateRuleText(fields[name])
  const set = (name: keyof typeof values) => (e: { target: { value: string } }) =>
    setValues((v) => ({ ...v, [name]: e.target.value }))
  const otherError =
    save.isError && !confirming && Object.keys(fields).length === 0
      ? userMessage(save.error, 'patient')
      : null

  if (confirming) {
    return (
      <section className="flex flex-col gap-4">
        <h1>Change your pregnancy dates?</h1>
        <Card role="alertdialog" aria-labelledby="confirm-text" className="flex flex-col gap-4">
          <p id="confirm-text">{messageText(messages, 'msg_confirm_override_clinician_date')}</p>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" onClick={() => setConfirming(false)}>
              Keep my current date
            </Button>
            <Button loading={save.isPending} onClick={() => save.mutate(body(true))}>
              Change my dates
            </Button>
          </div>
        </Card>
      </section>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      <h1>Pregnancy dates</h1>
      {dates.due_date && (
        <Card>
          <p>
            Current due date: <strong>{formatDay(dates.due_date)}</strong>
          </p>
          <p className="text-sm text-muted">{SOURCE_LABEL[dates.due_date_source ?? ''] ?? ''}</p>
        </Card>
      )}
      <form onSubmit={submit} noValidate className="flex flex-col gap-4">
        {otherError && <ErrorState message={otherError} />}
        <fieldset className="flex flex-col gap-1">
          <legend className="mb-1 font-semibold">What do you know?</legend>
          {OPTIONS.map(({ value, label }) => (
            <label key={value} className="flex min-h-11 items-center gap-3">
              <input
                type="radio"
                name="option"
                value={value}
                checked={option === value}
                onChange={() => {
                  setOption(value)
                  setMissing([])
                  save.reset()
                }}
                className="size-5 accent-[var(--color-primary)]"
              />
              {label}
            </label>
          ))}
        </fieldset>
        {option === 'lmp' && (
          <TextField
            label="First day of your last period"
            type="date"
            value={values.lmp_date}
            onChange={set('lmp_date')}
            error={fieldError('lmp_date')}
          />
        )}
        {option === 'due_date' && (
          <TextField
            label="Due date given by your doctor"
            type="date"
            value={values.due_date}
            onChange={set('due_date')}
            error={fieldError('due_date')}
          />
        )}
        {option === 'ultrasound' && (
          <>
            <TextField
              label="Date of the scan"
              type="date"
              value={values.scan_date}
              onChange={set('scan_date')}
              error={fieldError('scan_date')}
            />
            <div className="grid grid-cols-2 gap-3">
              <TextField
                label="Weeks at the scan"
                type="number"
                inputMode="numeric"
                min={0}
                max={42}
                value={values.ga_weeks}
                onChange={set('ga_weeks')}
                error={fieldError('ga_weeks')}
              />
              <TextField
                label="Days (0 to 6)"
                type="number"
                inputMode="numeric"
                min={0}
                max={6}
                value={values.ga_days}
                onChange={set('ga_days')}
                error={fieldError('ga_days')}
              />
            </div>
          </>
        )}
        <div className="flex flex-wrap items-center gap-4">
          <Button type="submit" loading={save.isPending}>
            Save dates
          </Button>
          {/* UX_FLOWS P3: skip is allowed; home then shows the onboarding card only */}
          <Link to="/home">{dates.due_date ? 'Cancel' : 'Skip for now'}</Link>
        </div>
      </form>
    </section>
  )
}

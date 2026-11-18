import { userMessage, type JourneyHome, type PregnancyEndInput } from '@alovia/shared'
import { Button, Card, ErrorState } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'

import { api } from '../app/services'
import { HOME_KEY } from '../app/useJourneyHome'

type Status = PregnancyEndInput['status']

// §11.2 step 1: the three choices, worded exactly as in the spec
export const END_CHOICES: { value: Status; label: string }[] = [
  { value: 'ended_birth', label: 'My baby was born' },
  { value: 'ended_loss', label: 'I have lost my pregnancy' },
  { value: 'ended_not_specified', label: 'I prefer not to say' },
]

// §11.1 entry and heading: the spec's wording, approved by the owner (2026-11-18, DEC-054)
export const END_TITLE = 'My pregnancy has ended'

/** Pregnancy-end flow (Journey §11.2, UX_FLOWS P11): choice → "inform my doctor?" (no
 * default) → confirmation. Calm and plain; no animation. */
export function PregnancyEndPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [status, setStatus] = useState<Status | null>(null)
  const [inform, setInform] = useState<boolean | null>(null)
  const [missing, setMissing] = useState(false)

  const save = useMutation({
    mutationFn: (body: PregnancyEndInput) => api.post<JourneyHome>('/patient/pregnancy-end', body),
    onSuccess: async (data) => {
      queryClient.setQueryData(HOME_KEY, data) // home shows the §11.4/11.5 screens
      await queryClient.invalidateQueries({ queryKey: ['notifications'] })
      await queryClient.invalidateQueries({ queryKey: ['journey-calendar'] })
      navigate('/home')
    },
  })

  function next(e: FormEvent) {
    e.preventDefault()
    const answered = step === 1 ? status !== null : inform !== null
    setMissing(!answered)
    if (answered) setStep(step === 1 ? 2 : 3)
  }

  const choiceLabel = END_CHOICES.find((c) => c.value === status)?.label

  return (
    <section className="flex flex-col gap-4">
      <h1>{END_TITLE}</h1>
      {step === 1 && (
        <form onSubmit={next} noValidate className="flex flex-col gap-4">
          <Radios
            legend="Choose one"
            name="status"
            options={END_CHOICES}
            value={status}
            onChange={(v) => setStatus(v)}
            error={missing}
          />
          <Actions back={<Link to="/more">Cancel</Link>} />
        </form>
      )}
      {step === 2 && (
        <form onSubmit={next} noValidate className="flex flex-col gap-4">
          <Radios
            legend="Would you like your doctor to be informed?"
            name="inform"
            options={[
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' },
            ]}
            value={inform === null ? null : inform ? 'yes' : 'no'}
            onChange={(v) => setInform(v === 'yes')}
            error={missing}
          />
          <Actions back={<BackButton onClick={() => setStep(1)} />} />
        </form>
      )}
      {step === 3 && status !== null && inform !== null && (
        <Card className="flex flex-col gap-4">
          <h2>Please confirm</h2>
          <ul className="flex flex-col gap-1">
            <li>{choiceLabel}</li>
            <li>Inform my doctor: {inform ? 'Yes' : 'No'}</li>
          </ul>
          {save.isError && <ErrorState message={userMessage(save.error, 'patient')} />}
          <div className="flex flex-wrap gap-3">
            <Button
              loading={save.isPending}
              onClick={() => save.mutate({ status, inform_doctor: inform })}
            >
              Confirm
            </Button>
            <BackButton onClick={() => setStep(2)} />
          </div>
        </Card>
      )}
    </section>
  )
}

function Radios<T extends string>({
  legend,
  name,
  options,
  value,
  onChange,
  error,
}: {
  legend: string
  name: string
  options: { value: T; label: string }[]
  value: T | null
  onChange: (value: T) => void
  error: boolean
}) {
  return (
    <fieldset
      className="flex flex-col gap-1"
      aria-describedby={error ? `${name}-error` : undefined}
    >
      <legend className="mb-1 font-semibold">{legend}</legend>
      {options.map((o) => (
        <label key={o.value} className="flex min-h-11 items-center gap-3">
          <input
            type="radio"
            name={name}
            value={o.value}
            checked={value === o.value}
            onChange={() => onChange(o.value)}
            className="size-5 accent-[var(--color-primary)]"
          />
          {o.label}
        </label>
      ))}
      {error && (
        <p id={`${name}-error`} className="text-sm text-urgent">
          Please choose one.
        </p>
      )}
    </fieldset>
  )
}

function Actions({ back }: { back: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button type="submit">Continue</Button>
      {back}
    </div>
  )
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <Button type="button" variant="secondary" onClick={onClick}>
      Back
    </Button>
  )
}

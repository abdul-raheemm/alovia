import { ApiError, userMessage, type PatientInput } from '@alovia/shared'
import { Button, TextAreaField, TextField } from '@alovia/ui'
import { useState, type FormEvent } from 'react'

export interface PatientFormValues {
  name: string
  age: string
  notes: string
}

/** Client checks match the backend (PatientIn): name required, age 18+ (DEC-023). */
export function patientErrors(
  v: PatientFormValues,
): Partial<Record<keyof PatientFormValues, string>> {
  const errors: Partial<Record<keyof PatientFormValues, string>> = {}
  if (!v.name.trim()) errors.name = 'Enter the patient’s name.'
  if (v.age.trim()) {
    const n = Number(v.age)
    if (!Number.isInteger(n) || n < 18 || n > 120)
      errors.age = 'Age must be a whole number, 18 or more.'
  }
  return errors
}

export function toPatientInput(v: PatientFormValues): PatientInput {
  return {
    name: v.name.trim(),
    age: v.age.trim() ? Number(v.age) : null,
    notes: v.notes.trim() || null,
  }
}

/** §8.1 create / edit: name, optional age and private notes. */
export function PatientForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial: PatientFormValues
  submitLabel: string
  onSubmit: (input: PatientInput) => Promise<unknown>
  onCancel?: () => void
}) {
  const [values, setValues] = useState(initial)
  const [errors, setErrors] = useState<Partial<Record<keyof PatientFormValues, string>>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const set = (patch: Partial<PatientFormValues>) => setValues((v) => ({ ...v, ...patch }))

  async function submit(e: FormEvent) {
    e.preventDefault()
    const found = patientErrors(values)
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      await onSubmit(toPatientInput(values))
    } catch (err) {
      if (err instanceof ApiError && err.fields) {
        setErrors({ name: err.fields.name, age: err.fields.age, notes: err.fields.notes })
      }
      setFormError(userMessage(err, 'doctor'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form noValidate onSubmit={(e) => void submit(e)} className="flex max-w-xl flex-col gap-4">
      <TextField
        label="Name"
        value={values.name}
        maxLength={100}
        autoComplete="off"
        error={errors.name}
        onChange={(e) => set({ name: e.target.value })}
      />
      <TextField
        label="Age (optional)"
        inputMode="numeric"
        value={values.age}
        error={errors.age}
        onChange={(e) => set({ age: e.target.value })}
      />
      <TextAreaField
        label="Notes (optional, doctors only)"
        value={values.notes}
        maxLength={1000}
        error={errors.notes}
        onChange={(e) => set({ notes: e.target.value })}
      />
      {formError && (
        <p role="alert" className="text-urgent">
          {formError}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" loading={busy}>
          {submitLabel}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}

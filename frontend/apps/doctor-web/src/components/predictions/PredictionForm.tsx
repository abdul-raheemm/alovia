import { ApiError, userMessage, type PredictionResult, type PredictionSchema } from '@alovia/shared'
import { Button, Card, FieldError } from '@alovia/ui'
import { AlertTriangle, Info } from 'lucide-react'
import { useId, useState, type FormEvent } from 'react'

import {
  buildInput,
  defaultUnits,
  messageText,
  outOfRange,
  shortNumber,
  toModelUnit,
} from '../../app/predictions'
import { api } from '../../app/services'

type Field = PredictionSchema['groups'][number]['fields'][number]

function UnitSwitch({
  field,
  value,
  onChange,
}: {
  field: Field
  value: string
  onChange: (unit: string) => void
}) {
  if (!field.unit) return null
  const { name, model_unit, other_unit } = field.unit
  return (
    <fieldset className="flex gap-3 text-sm">
      <legend className="sr-only">Unit for {field.label}</legend>
      {[other_unit, model_unit].map((u) => (
        <label key={u} className="flex min-h-11 items-center gap-1">
          <input
            type="radio"
            name={`unit-${name}`}
            value={u}
            checked={value === u}
            onChange={() => onChange(u)}
            className="size-4 accent-[var(--color-primary)]"
          />
          {u}
        </label>
      ))}
    </fieldset>
  )
}

function NumberField({
  field,
  raw,
  unit,
  schema,
  error,
  hba1cNote,
  onValue,
  onUnit,
}: {
  field: Field
  raw: string
  unit: string
  schema: PredictionSchema
  error?: string
  hba1cNote: boolean
  onValue: (v: string) => void
  onUnit: (u: string) => void
}) {
  const id = useId()
  const describedBy = `${id}-help`
  const n = Number(raw)
  const has = raw.trim() !== '' && Number.isFinite(n)
  const conv = field.unit ? schema.conversions[field.unit.name] : undefined
  const modelValue = has ? toModelUnit(n, unit, field, conv) : null
  const converted = field.unit && has && unit !== field.unit.model_unit
  const outside = modelValue !== null && outOfRange(field, modelValue)
  const hba1c = field.unit?.name === 'hba1c'
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-semibold">
        {field.label}
      </label>
      <div className="flex flex-wrap items-center gap-3">
        <input
          id={id}
          inputMode="decimal"
          value={raw}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          onChange={(e) => onValue(e.target.value)}
          className="min-h-11 w-36 rounded-sm border border-border bg-surface px-3 text-base text-text"
        />
        <UnitSwitch field={field} value={unit} onChange={onUnit} />
      </div>
      <div id={describedBy} className="flex flex-col gap-1 text-sm">
        {converted && modelValue !== null && (
          <span className="text-muted">
            {shortNumber(n)} {unit} = {shortNumber(modelValue)} {field.unit?.model_unit}
          </span>
        )}
        {outside && (
          <span className="flex items-center gap-1 text-caution">
            <AlertTriangle aria-hidden="true" className="size-4 shrink-0" />
            {messageText(schema.messages, 'warn_outside_training_range')}
          </span>
        )}
        {hba1c && hba1cNote && (
          <span className="flex items-center gap-1">
            <Info aria-hidden="true" className="size-4 shrink-0" />
            {messageText(schema.messages, 'note_hba1c_haemoglobin_variant')}
          </span>
        )}
      </div>
      <FieldError id={`${id}-error`} message={error} />
    </div>
  )
}

/** §9.1-9.4 form: inputs from the model's feature list in config sections; unit switches
 * with a conversion preview; range warnings before and after submit (the prediction still
 * runs). Nobody can type a prediction or a probability (§1.3). */
export function PredictionForm({
  schema,
  patientId,
  hba1cNote,
  onDone,
}: {
  schema: PredictionSchema
  patientId: string
  hba1cNote: boolean
  onDone: (result: PredictionResult) => void
}) {
  const [raw, setRaw] = useState<Record<string, string>>({})
  const [units, setUnits] = useState(() => defaultUnits(schema))
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    const built = buildInput(schema, raw, units)
    if ('errors' in built) {
      setErrors(built.errors)
      setFormError('Please fill in every value.')
      return
    }
    setErrors({})
    setBusy(true)
    try {
      onDone(
        await api.post<PredictionResult>(
          `/doctor/patients/${patientId}/predictions/${schema.model}`,
          built.body,
        ),
      )
      setRaw({})
    } catch (err) {
      if (err instanceof ApiError && err.fields) {
        setErrors(
          Object.fromEntries(
            Object.entries(err.fields).map(([k, v]) => [k.replace(/^values\./, ''), v]),
          ),
        )
      }
      setFormError(userMessage(err, 'doctor'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form noValidate onSubmit={(e) => void submit(e)} className="flex flex-col gap-4">
      {schema.groups.map((g) => (
        <Card key={g.label}>
          <fieldset className="flex flex-col gap-4">
            <legend className="mb-2 text-lg font-semibold">{g.label}</legend>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {g.fields.map((f) => (
                <NumberField
                  key={f.feature}
                  field={f}
                  raw={raw[f.feature] ?? ''}
                  unit={f.unit ? (units[f.unit.name] ?? f.unit.default) : ''}
                  schema={schema}
                  error={errors[f.feature]}
                  hba1cNote={hba1cNote}
                  onValue={(v) => setRaw((old) => ({ ...old, [f.feature]: v }))}
                  onUnit={(u) => {
                    const name = f.unit?.name
                    if (name) setUnits((old) => ({ ...old, [name]: u }))
                  }}
                />
              ))}
            </div>
          </fieldset>
        </Card>
      ))}
      {formError && (
        <p role="alert" className="text-urgent">
          {formError}
        </p>
      )}
      <Button type="submit" loading={busy} className="self-start">
        Run prediction
      </Button>
    </form>
  )
}

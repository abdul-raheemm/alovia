import type { PredictionInput, PredictionSchema } from '@alovia/shared'

/** DEC-041: texts without doctor-approved wording show this, never agent-written text. */
export const PENDING_TEXT = '[Text pending doctor approval]'

export function messageText(messages: Record<string, string | null>, key: string): string {
  return messages[key] ?? PENDING_TEXT
}

type Field = PredictionSchema['groups'][number]['fields'][number]
type Conversion = PredictionSchema['conversions'][string]

/** §9.3 model = entered × multiply ÷ divide + add (the backend does the same; this is the
 * preview "7.0 % = 53 mmol/mol" shown before submit). */
export function toModelUnit(value: number, unit: string, field: Field, conv?: Conversion): number {
  if (!field.unit || !conv || unit === field.unit.model_unit) return value
  return (value * conv.multiply) / conv.divide + conv.add
}

/** Rounded for display only; the exact value is sent and stored. */
export function shortNumber(n: number): string {
  return Number.isInteger(n) ? String(n) : String(Number(n.toFixed(2)))
}

export function outOfRange(field: Field, modelValue: number): boolean {
  return modelValue < field.range.min || modelValue > field.range.max
}

export function defaultUnits(schema: PredictionSchema): Record<string, string> {
  const units: Record<string, string> = {}
  for (const g of schema.groups)
    for (const f of g.fields) if (f.unit) units[f.unit.name] = f.unit.default
  return units
}

/** Client check before submit: every input is a number. Returns the body or field errors. */
export function buildInput(
  schema: PredictionSchema,
  raw: Record<string, string>,
  units: Record<string, string>,
): { body: PredictionInput } | { errors: Record<string, string> } {
  const values: Record<string, number> = {}
  const errors: Record<string, string> = {}
  for (const g of schema.groups) {
    for (const f of g.fields) {
      const text = (raw[f.feature] ?? '').trim()
      const n = Number(text)
      if (text === '' || !Number.isFinite(n)) errors[f.feature] = 'Enter a number.'
      else values[f.feature] = n
    }
  }
  return Object.keys(errors).length ? { errors } : { body: { values, units } }
}

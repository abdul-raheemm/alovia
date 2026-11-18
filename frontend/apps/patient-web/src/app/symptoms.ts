/** Pure helpers for the symptom screens (Symptom spec §4, §11; DEC-060, DEC-061). */
import { ApiError, type EntryInput, type SymptomVocabulary } from '@alovia/shared'

import { PENDING_TEXT } from './journey'
import { SYMPTOM_BUNDLE } from './symptomBundle.generated'

export type Level = 'L0' | 'L1' | 'L2'
type CommonSymptom = SymptomVocabulary['common'][number]

/** The spec's own level names (D3, UX_FLOWS P5), used as headings (DEC-061). */
export const LEVEL_HEADING: Record<Level, string> = {
  L1: 'Go to hospital now',
  L2: 'Contact your doctor today',
  L0: 'Saved',
}

/** Advice text from the bundled messages; pending until a doctor approves it (DEC-041). */
export function adviceText(key: string): string {
  return (SYMPTOM_BUNDLE.messages as Record<string, string | null>)[key] ?? PENDING_TEXT
}

export type HelplineKey = keyof typeof SYMPTOM_BUNDLE.helplines

/** Warning signs offered without the backend: from their week on, or all when the week is
 * unknown (§5.2, §1.3). */
export function offlineWarnings(week: number | null) {
  return SYMPTOM_BUNDLE.warning.filter(
    (w) => w.fromWeek === null || week === null || week >= w.fromWeek,
  )
}

/** The backend could not be reached or failed: the urgent page then shows the L1 advice
 * (DEC-060). Errors the backend explains itself (4xx) are shown as they are. */
export function cannotReach(error: unknown): boolean {
  return error instanceof ApiError && (error.status === 0 || error.status >= 500)
}

/** Field message for a V1/V2 code returned for `entries.<index>.<field>` (§6). */
export function entryError(
  fields: Record<string, string> | null | undefined,
  index: number,
  field: string,
): string | undefined {
  const code = fields?.[`entries.${index}.${field}`]
  if (code === undefined) return undefined
  return code === 'V1' ? 'Please fill this in.' : 'Please check this value.'
}

/** What the patient filled in for one everyday symptom. */
export interface CommonDraft {
  severity?: string
  duration?: string
  body_area?: string
  flags: Record<string, boolean>
  puqe: (number | undefined)[]
  text?: string
  choice?: string
  occurred_at?: string
  notes?: string
}

export const emptyDraft = (): CommonDraft => ({
  flags: {},
  puqe: [undefined, undefined, undefined],
})

/** The required details still missing for one everyday symptom (checked again by the backend). */
export function missingFields(spec: CommonSymptom, d: CommonDraft): string[] {
  const missing = []
  if (spec.severity && !d.severity) missing.push('severity')
  if (spec.duration && !d.duration) missing.push('duration')
  if (spec.body_area?.required && !d.body_area) missing.push('body_area')
  if (spec.text?.required && !d.text?.trim()) missing.push(spec.text.field)
  if (spec.choice && !d.choice) missing.push(spec.choice.field)
  if (spec.puqe && d.puqe.some((a) => a === undefined)) missing.push('puqe_answers')
  return missing
}

/** One API entry from a draft: only the details this symptom asks for (§5.1). */
export function toEntry(spec: CommonSymptom, d: CommonDraft): EntryInput {
  const entry: Record<string, unknown> = { symptom: spec.id }
  if (spec.severity) entry.severity = d.severity
  if (spec.duration) entry.duration = d.duration
  if (spec.body_area && d.body_area) entry.body_area = d.body_area
  for (const flag of Object.keys(spec.flags)) if (d.flags[flag]) entry[flag] = true
  if (spec.puqe) entry.puqe_answers = d.puqe
  if (spec.text && d.text?.trim()) entry[spec.text.field] = d.text.trim()
  if (spec.choice) entry[spec.choice.field] = d.choice
  if (d.occurred_at) entry.occurred_at = d.occurred_at
  if (d.notes?.trim()) entry.notes = d.notes.trim()
  return entry as EntryInput
}

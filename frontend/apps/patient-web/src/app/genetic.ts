/** Pure helpers for the genetic screens (Genetic spec §4.1, §5, §8, §11). */
import type { GeneticInput } from '@alovia/shared'

import { GENETIC_BUNDLE } from './geneticBundle.generated'
import { PENDING_TEXT } from './journey'

export type ConditionKey = 'haemoglobin_group' | 'haemophilia' | 'marfan'
export const CONDITIONS: ConditionKey[] = ['haemoglobin_group', 'haemophilia', 'marfan']

/** A message from the rule files; pending until a doctor approves it (DEC-041). */
export function geneticText(key: string): string {
  return (GENETIC_BUNDLE.messages as Record<string, string | null>)[key] ?? PENDING_TEXT
}

/** §5.5 / §5.6 questions with the condition's name filled in (the spec's own wording). */
export function questionFor(template: string, condition: ConditionKey): string {
  return template.replace('{condition}', GENETIC_BUNDLE.questionNames[condition])
}

/** §5.4: the evidence choices allowed with this condition and status (none for unknown). */
export function evidenceFor(
  condition: ConditionKey,
  status: string | undefined,
): [string, string][] {
  if (!status || status === 'unknown') return []
  return Object.entries(GENETIC_BUNDLE.evidence)
    .filter(
      ([, e]) =>
        (e.conditions as readonly string[]).includes(condition) &&
        (e.haemoglobinStatuses === null ||
          (e.haemoglobinStatuses as readonly string[]).includes(status)),
    )
    .map(([id, e]) => [id, e.label])
}

export interface ParentDraft {
  status?: string
  evidence?: string
}
export interface SectionDraft {
  entry?: string
  mother: ParentDraft
  father: ParentDraft
  previous_child?: string
}
export type GeneticDraft = Record<ConditionKey, SectionDraft> & { consanguinity?: string }

/** D14: the father's answers start as `unknown`; DEC-069: no default for his haemophilia
 * status (unknown is not allowed there). Nothing else is pre-selected. */
export const emptyGeneticDraft = (): GeneticDraft => ({
  haemoglobin_group: { mother: {}, father: { status: 'unknown' } },
  haemophilia: { mother: {}, father: {} },
  marfan: { mother: {}, father: { status: 'unknown' } },
})

/** Whether a section's parent questions are asked (§5.5: haemoglobin always). */
export function sectionShown(condition: ConditionKey, draft: SectionDraft): boolean {
  return condition === 'haemoglobin_group' || (!!draft.entry && draft.entry !== 'no')
}

/** The answers still missing, as the API's field paths (checked again by the backend, §6.1). */
export function missingAnswers(draft: GeneticDraft): string[] {
  const missing: string[] = []
  for (const c of CONDITIONS) {
    const s = draft[c]
    if (c !== 'haemoglobin_group' && !s.entry) missing.push(`${c}.entry`)
    if (!sectionShown(c, s)) continue
    for (const who of ['mother', 'father'] as const) {
      const p = s[who]
      if (!p.status) missing.push(`${c}.${who}.status`)
      else if (p.status !== 'unknown' && !p.evidence) missing.push(`${c}.${who}.evidence`)
    }
    if (!s.previous_child) missing.push(`${c}.previous_child`)
  }
  if (!draft.consanguinity) missing.push('consanguinity')
  return missing
}

/** The request body: only what was asked (§5.5: nothing after an entry answer of "no"). */
export function toGeneticInput(draft: GeneticDraft): GeneticInput {
  const parent = (p: ParentDraft) =>
    p.status === 'unknown' ? { status: 'unknown' } : { status: p.status, evidence: p.evidence }
  const section = (c: ConditionKey) => {
    const s = draft[c]
    const head = c === 'haemoglobin_group' ? {} : { entry: s.entry }
    if (!sectionShown(c, s)) return head
    return {
      ...head,
      mother: parent(s.mother),
      father: parent(s.father),
      previous_child: s.previous_child,
    }
  }
  return {
    haemoglobin_group: section('haemoglobin_group'),
    haemophilia: section('haemophilia'),
    marfan: section('marfan'),
    consanguinity: draft.consanguinity,
  } as GeneticInput
}

/** Journey §10.4 "Genetic check" card labels (DEC-073). */
export const GENETIC_CHECK_LABEL: Record<string, string> = {
  reviewed: 'Reviewed by your doctor',
  sent_to_doctor: 'Sent to your doctor',
  needs_testing: 'Needs testing',
  pending_review: "Waiting for your doctor's review",
}

/** §7 display: "1 in 2 (50%)", "not expected" — never 0%. */
export function chanceLabel(chance: string): string {
  return (GENETIC_BUNDLE.chances as Record<string, string>)[chance] ?? chance
}

export function outcomeLabel(outcome: string): string {
  return (GENETIC_BUNDLE.outcomes as Record<string, string>)[outcome] ?? outcome
}

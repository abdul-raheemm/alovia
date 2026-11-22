import type { PatientRow } from '@alovia/shared'
import {
  Circle,
  CircleAlert,
  Dna,
  HeartPulse,
  Stethoscope,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react'

import { geneticLabel } from '../app/patients'

/** A status badge: module icon plus the value as text (colour is never the only signal).
 * Only symptom levels use the reserved L1 / L2 colours; the other modules stay neutral (DEC-116). */
export function Badge({
  Icon,
  text,
  tone,
}: {
  Icon: LucideIcon
  text: string
  tone?: 'urgent' | 'caution'
}) {
  return (
    <span
      className={
        tone === 'urgent'
          ? 'inline-flex items-center gap-1 rounded-md bg-urgent/10 px-2 py-0.5 text-sm font-semibold text-urgent'
          : tone === 'caution'
            ? 'inline-flex items-center gap-1 rounded-md bg-caution/10 px-2 py-0.5 text-sm font-semibold text-caution'
            : 'inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-sm'
      }
    >
      <Icon aria-hidden="true" className="size-4 shrink-0" />
      {text}
    </span>
  )
}

export function SymptomBadge({ level, prefix = '' }: { level: string; prefix?: string }) {
  if (level === 'L1') return <Badge Icon={TriangleAlert} text={`${prefix}L1`} tone="urgent" />
  if (level === 'L2') return <Badge Icon={CircleAlert} text={`${prefix}L2`} tone="caution" />
  return <Badge Icon={Circle} text={`${prefix}${level}`} />
}

/** One badge per module that has a result; never one combined status (CLAUDE.md §8). */
export function ModuleBadges({
  row,
}: {
  row: Pick<PatientRow, 'fetal' | 'maternal' | 'genetic' | 'symptom'>
}) {
  return (
    <span className="flex flex-wrap gap-1">
      {row.fetal && <Badge Icon={HeartPulse} text={`Fetal ${row.fetal.predicted_class}`} />}
      {row.maternal && (
        <Badge Icon={Stethoscope} text={`Maternal ${row.maternal.predicted_class}`} />
      )}
      {row.genetic && <Badge Icon={Dna} text={`Genetic: ${geneticLabel(row.genetic)}`} />}
      {row.symptom && <SymptomBadge level={row.symptom.level} prefix="Symptoms " />}
    </span>
  )
}

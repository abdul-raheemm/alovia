import {
  chanceLabel,
  GENETIC_BUNDLE,
  geneticText,
  outcomeLabel,
  type ConditionKey,
  type GeneticAssessment,
} from '@alovia/shared'
import { Card } from '@alovia/ui'
import { Stethoscope } from 'lucide-react'

import { formatDay } from '../../app/journey'

type Condition = GeneticAssessment['conditions'][number]
type Outcomes = Condition['outcomes']

function OutcomeList({ outcomes }: { outcomes: Outcomes }) {
  return (
    <ul className="flex flex-col gap-1">
      {(outcomes ?? []).map((o) => (
        <li key={o.outcome}>
          {outcomeLabel(o.outcome)}: <strong>{chanceLabel(o.chance)}</strong>
        </li>
      ))}
    </ul>
  )
}

function ConditionCard({ c, showNumbers }: { c: Condition; showNumbers: boolean }) {
  const texts = [...(c.message_keys ?? []), ...(c.warnings ?? []), ...(c.notes ?? [])]
  return (
    <Card className="flex flex-col gap-3">
      <h3>{GENETIC_BUNDLE.conditions[c.condition as ConditionKey]}</h3>
      {showNumbers && c.status === 'calculated' && c.outcomes && (
        <OutcomeList outcomes={c.outcomes} />
      )}
      {showNumbers && c.status === 'calculated' && c.outcomes_if_boy && (
        // §11.3 PCPNDT: both together, never one alone; the baby's sex is never asked
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <h4 className="font-semibold">If the baby is a boy</h4>
            <OutcomeList outcomes={c.outcomes_if_boy} />
          </div>
          <div>
            <h4 className="font-semibold">If the baby is a girl</h4>
            <OutcomeList outcomes={c.outcomes_if_girl} />
          </div>
        </div>
      )}
      {texts.map((key) => (
        <p key={key} className="text-sm">
          {geneticText(key)}
        </p>
      ))}
    </Card>
  )
}

/** Result screen (Genetic spec §4.1 step 8, §8, §10.4, §11): numbers only when shown, next
 * steps otherwise, the fixed disclaimer always, and the doctor's note visually apart. */
export function GeneticResult({ result }: { result: GeneticAssessment }) {
  return (
    <section aria-labelledby="result-heading" className="flex flex-col gap-4">
      <h2 id="result-heading">Your result — {formatDay(result.created_at.slice(0, 10))}</h2>
      <p role="note" className="rounded-md border border-border bg-surface p-3 font-semibold">
        {geneticText(result.disclaimer_key)}
      </p>
      {result.message_keys.map((key) => (
        <p key={key} className="rounded-md bg-primary-soft p-3">
          {geneticText(key)}
        </p>
      ))}
      {result.conditions.map((c) => (
        <ConditionCard key={c.condition} c={c} showNumbers={result.show_numbers_to_patient} />
      ))}
      {result.doctor_note && (
        // §11.1: doctor-confirmed information looks different from the educational result
        <Card className="flex flex-col gap-2 border-2 border-primary">
          <p className="flex items-center gap-2 font-semibold text-primary">
            <Stethoscope aria-hidden="true" className="size-5" />
            From your doctor
            {result.reviewed_at && (
              <span className="font-normal text-muted">
                — {formatDay(result.reviewed_at.slice(0, 10))}
              </span>
            )}
          </p>
          <p className="whitespace-pre-line">{result.doctor_note}</p>
        </Card>
      )}
    </section>
  )
}

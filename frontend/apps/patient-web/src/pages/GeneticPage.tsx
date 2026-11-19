import { userMessage, type GeneticAssessment } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

import { formatDay } from '../app/journey'
import { api } from '../app/services'
import { GeneticForm } from '../components/genetic/GeneticForm'
import { GeneticResult } from '../components/genetic/GeneticResult'

/** Genetic risk (Genetic spec §4.1, UX_FLOWS P9): the latest result with its next steps, a
 * new check, and earlier checks. */
export function GeneticPage() {
  const list = useQuery({
    queryKey: ['genetic-assessments'],
    queryFn: () => api.get<GeneticAssessment[]>('/patient/genetic/assessments'),
  })
  const [mode, setMode] = useState<'view' | 'form'>('view')
  const [selected, setSelected] = useState<string | null>(null)
  // the result the server just returned: shown at once, before the history list refreshes
  const [submitted, setSubmitted] = useState<GeneticAssessment | null>(null)

  if (list.isPending) return <PageSkeleton />
  if (list.isError) {
    return (
      <ErrorState
        message={userMessage(list.error, 'patient')}
        onRetry={() => void list.refetch()}
      />
    )
  }
  const all = list.data
  const shown =
    all.find((a) => a.assessment_id === selected) ??
    (submitted?.assessment_id === selected ? submitted : undefined) ??
    all[0]

  return (
    <section className="flex flex-col gap-6">
      <h1>Genetic risk</h1>
      {mode === 'form' || !shown ? (
        <GeneticForm
          onDone={(result) => {
            setSubmitted(result)
            setSelected(result.assessment_id)
            setMode('view')
          }}
        />
      ) : (
        <>
          <GeneticResult result={shown} />
          <Button variant="secondary" className="self-start" onClick={() => setMode('form')}>
            Start a new check
          </Button>
          {all.length > 1 && (
            <section aria-labelledby="earlier-heading" className="flex flex-col gap-2">
              <h2 id="earlier-heading">Earlier checks</h2>
              <Card>
                <ul className="flex flex-col gap-2">
                  {all.map((a) => (
                    <li key={a.assessment_id}>
                      <button
                        type="button"
                        className="min-h-11 text-left text-primary underline"
                        aria-current={a.assessment_id === shown.assessment_id ? 'true' : undefined}
                        onClick={() => setSelected(a.assessment_id)}
                      >
                        {formatDay(a.created_at.slice(0, 10))} —{' '}
                        {a.review_status === 'reviewed'
                          ? 'Reviewed by your doctor'
                          : "Waiting for your doctor's review"}
                      </button>
                    </li>
                  ))}
                </ul>
              </Card>
            </section>
          )}
        </>
      )}
    </section>
  )
}

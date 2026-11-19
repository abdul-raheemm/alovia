import {
  userMessage,
  type PatientDetail,
  type PredictionResult,
  type PredictionSchema,
  type Trends,
} from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { formatDateTime } from '../../app/patients'
import { api } from '../../app/services'
import { PredictionForm } from './PredictionForm'
import { PredictionResultCard } from './PredictionResultCard'
import { TrendCharts } from './TrendCharts'

/** Fetal or Maternal tab (§9-11, UX_FLOWS D4-D5): enter values, see the result with its
 * explanation and limitations, share it, look back at earlier results and trends. */
export function PredictionTab({
  model,
  patient,
}: {
  model: 'fetal' | 'maternal'
  patient: PatientDetail
}) {
  const qc = useQueryClient()
  const [mode, setMode] = useState<'results' | 'form'>('results')
  const [selected, setSelected] = useState<string | null>(null)
  const schema = useQuery({
    queryKey: ['prediction-schema', model],
    queryFn: () => api.get<PredictionSchema>(`/doctor/predictions/schema/${model}`),
    staleTime: Infinity,
  })
  const history = useQuery({
    queryKey: ['predictions', patient.id, model],
    queryFn: () =>
      api.get<PredictionResult[]>(`/doctor/patients/${patient.id}/predictions?model=${model}`),
  })
  const trends = useQuery({
    queryKey: ['predictions', patient.id, 'trends'],
    queryFn: () => api.get<Trends>(`/doctor/patients/${patient.id}/trends`),
  })

  const failed = [schema, history].find((q) => q.isError)
  if (failed) {
    return (
      <ErrorState
        message={userMessage(failed.error, 'doctor')}
        onRetry={() => void failed.refetch()}
      />
    )
  }
  if (!schema.data || !history.data) return <PageSkeleton />
  const labels = Object.fromEntries(
    schema.data.groups.flatMap((g) => g.fields.map((f) => [f.feature, f.label])),
  )
  const results = history.data
  const shown = results.find((r) => r.id === selected) ?? results[0]
  const title = model === 'fetal' ? 'CTG' : 'vitals'

  return (
    <div className="flex flex-col gap-6">
      {mode === 'form' || !shown ? (
        <section aria-labelledby="enter-heading" className="flex flex-col gap-3">
          <h2 id="enter-heading">Enter {title}</h2>
          <PredictionForm
            schema={schema.data}
            patientId={patient.id}
            hba1cNote={model === 'maternal' && patient.hba1c_note}
            onDone={(r) => {
              qc.setQueryData<PredictionResult[]>(['predictions', patient.id, model], (old) => [
                r,
                ...(old ?? []),
              ])
              void qc.invalidateQueries({ queryKey: ['predictions', patient.id] })
              void qc.invalidateQueries({ queryKey: ['doctor-patient', patient.id] })
              setSelected(r.id)
              setMode('results')
            }}
          />
          {shown && (
            <Button variant="ghost" className="self-start" onClick={() => setMode('results')}>
              Back to results
            </Button>
          )}
        </section>
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2>Result</h2>
            <Button onClick={() => setMode('form')}>Enter new {title}</Button>
          </div>
          <PredictionResultCard
            result={shown}
            messages={schema.data.messages}
            limitationKeys={schema.data.limitation_keys}
            featureLabels={labels}
          />
          {results.length > 1 && (
            <section aria-labelledby="earlier-heading" className="flex flex-col gap-2">
              <h2 id="earlier-heading">Earlier results</h2>
              <Card>
                <ul className="flex flex-col gap-1">
                  {results.map((r) => (
                    <li key={r.id}>
                      <button
                        type="button"
                        className="min-h-11 text-left text-primary underline"
                        aria-current={r.id === shown.id ? 'true' : undefined}
                        onClick={() => setSelected(r.id)}
                      >
                        {formatDateTime(r.created_at)} — {r.predicted_class}
                        {r.share ? ' (shared)' : ''}
                      </button>
                    </li>
                  ))}
                </ul>
              </Card>
            </section>
          )}
          <section aria-labelledby="trends-heading" className="flex flex-col gap-2">
            <h2 id="trends-heading">Trends</h2>
            {trends.data ? (
              <TrendCharts model={model} trends={trends.data} featureLabels={labels} />
            ) : trends.isError ? (
              <ErrorState
                message={userMessage(trends.error, 'doctor')}
                onRetry={() => void trends.refetch()}
              />
            ) : (
              <PageSkeleton />
            )}
          </section>
        </>
      )}
    </div>
  )
}

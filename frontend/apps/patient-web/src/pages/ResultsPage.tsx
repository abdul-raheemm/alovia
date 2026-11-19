import { userMessage, type SharedResult } from '@alovia/shared'
import { Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import { Stethoscope } from 'lucide-react'

import { formatDay, PENDING_TEXT } from '../app/journey'
import { api } from '../app/services'

const KIND = { fetal: 'Baby (CTG) result', maternal: 'Your health check result' } as const

/** More → My results (UX_FLOWS P10, Dashboard §10): only results her doctor shared, as the
 * doctor-approved text and the doctor's message. Never probabilities or scores. */
export function ResultsPage() {
  const results = useQuery({
    queryKey: ['my-results'],
    queryFn: () => api.get<SharedResult[]>('/patient/results'),
  })
  if (results.isPending) return <PageSkeleton />
  if (results.isError) {
    return (
      <ErrorState
        message={userMessage(results.error, 'patient')}
        onRetry={() => void results.refetch()}
      />
    )
  }
  return (
    <section className="flex flex-col gap-4">
      <h1>My results</h1>
      {results.data.length === 0 ? (
        <Card>
          <p className="text-muted">No results shared yet. Your doctor shares results here.</p>
        </Card>
      ) : (
        <ul className="flex flex-col gap-3">
          {results.data.map((r) => (
            <li key={r.id}>
              <Card className="flex flex-col gap-2">
                <h2 className="text-lg">{KIND[r.result_type]}</h2>
                <p className="text-sm text-muted">
                  From {formatDay(r.result_date.slice(0, 10))}, shared{' '}
                  {formatDay(r.shared_at.slice(0, 10))}
                </p>
                <p>{r.template_text ?? PENDING_TEXT}</p>
                {r.doctor_message && (
                  <div className="flex flex-col gap-1 rounded-md bg-primary-soft p-3">
                    <p className="flex items-center gap-2 font-semibold text-primary">
                      <Stethoscope aria-hidden="true" className="size-4" />
                      {r.doctor_name ? `Message from ${r.doctor_name}` : 'Message from your doctor'}
                    </p>
                    <p className="whitespace-pre-line">{r.doctor_message}</p>
                  </div>
                )}
              </Card>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

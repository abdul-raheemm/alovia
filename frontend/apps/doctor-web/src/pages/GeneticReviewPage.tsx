import { userMessage, type DoctorAssessment } from '@alovia/shared'
import { Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'

import { formatDateTime } from '../app/patients'
import { api } from '../app/services'

/** Genetic review queue (Genetic §10.1, UX_FLOWS D7): pending assessments of the doctor's
 * patients, high priority first, then oldest first (the server's order). */
export function GeneticReviewPage() {
  const queue = useQuery({
    queryKey: ['genetic-queue'],
    queryFn: () => api.get<DoctorAssessment[]>('/doctor/genetic/review-queue'),
  })
  return (
    <section className="flex flex-col gap-4">
      <h1>Genetic review</h1>
      {queue.isPending ? (
        <PageSkeleton />
      ) : queue.isError ? (
        <ErrorState
          message={userMessage(queue.error, 'doctor')}
          onRetry={() => void queue.refetch()}
        />
      ) : queue.data.length === 0 ? (
        <Card>
          <p>No assessments are waiting for review.</p>
        </Card>
      ) : (
        <Card className="py-2">
          <ul className="divide-y divide-border">
            {queue.data.map((a) => (
              <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <Link to={`/patients/${a.patient_id}/genetic`} className="font-semibold">
                  {a.patient_name}
                </Link>
                <span>
                  {a.priority === 'high' ? (
                    <strong>High priority</strong>
                  ) : (
                    <span className="text-muted">Normal priority</span>
                  )}{' '}
                  · {formatDateTime(a.created_at)}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  )
}

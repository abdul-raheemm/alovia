import { userMessage } from '@alovia/shared'
import { Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { Stethoscope } from 'lucide-react'

import { formatDay } from '../app/journey'
import { useDoctorNotes } from '../app/useNotifications'

/** Doctor notes tab (Journey §10.3, UX_FLOWS P10): notes her doctors shared, newest first.
 * Read-only. TODO(Phase 5): link a genetic-assessment note (related_ref) to its assessment —
 * the doctor writes it in the genetic review (Genetic spec §10.3). */
export function DoctorNotesPage() {
  const notes = useDoctorNotes()
  if (notes.isPending) return <PageSkeleton />
  if (notes.isError) {
    return (
      <ErrorState
        message={userMessage(notes.error, 'patient')}
        onRetry={() => void notes.refetch()}
      />
    )
  }
  return (
    <section className="flex flex-col gap-4">
      <h1>Doctor notes</h1>
      {notes.data.length === 0 ? (
        <Card>
          <p className="text-muted">No notes from your doctor yet.</p>
        </Card>
      ) : (
        <ul className="flex flex-col gap-3">
          {notes.data.map((note) => (
            <li key={note.id}>
              <Card className="flex flex-col gap-2">
                <p className="flex items-center gap-2 text-sm text-muted">
                  <Stethoscope aria-hidden="true" className="size-4 text-primary" />
                  {note.doctor_name} — {formatDay(note.created_on)}
                </p>
                <p className="whitespace-pre-line">{note.body}</p>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

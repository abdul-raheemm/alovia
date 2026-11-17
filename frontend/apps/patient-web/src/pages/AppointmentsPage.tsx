import { userMessage, type Appointment } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { api } from '../app/services'
import { refreshAppointments, useAppointments } from '../app/useAppointments'
import { AppointmentCard, AppointmentForm } from '../components/journey/Appointments'

/** Appointments tab (Journey §9.3, UX_FLOWS P8): upcoming / past, add, edit and delete her own.
 * Doctor-added ones show "Added by your doctor" and have no edit or delete. */
export function AppointmentsPage() {
  const list = useAppointments()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<Appointment | 'new' | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const remove = useMutation({
    mutationFn: (id: string) => api.delete<null>(`/patient/appointments/${id}`),
    onSuccess: async () => {
      setDeleting(null)
      await refreshAppointments(queryClient)
    },
  })

  if (editing) {
    return (
      <section className="flex flex-col gap-4">
        <h1>{editing === 'new' ? 'Add an appointment' : 'Edit appointment'}</h1>
        <AppointmentForm
          initial={editing === 'new' ? undefined : editing}
          onDone={() => setEditing(null)}
        />
      </section>
    )
  }

  if (list.isPending) return <PageSkeleton />
  if (list.isError) {
    return (
      <ErrorState
        message={userMessage(list.error, 'patient')}
        onRetry={() => void list.refetch()}
      />
    )
  }

  const actions = (a: Appointment) =>
    deleting === a.id ? (
      <div
        role="alertdialog"
        aria-label="Delete this appointment?"
        className="mt-2 flex flex-col gap-2"
      >
        <p className="font-semibold">Delete this appointment?</p>
        <div className="flex flex-wrap gap-3">
          <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate(a.id)}>
            Delete
          </Button>
          <Button variant="secondary" onClick={() => setDeleting(null)}>
            Keep it
          </Button>
        </div>
      </div>
    ) : (
      <div className="mt-2 flex flex-wrap gap-3">
        <Button variant="secondary" onClick={() => setEditing(a)} aria-label={`Edit ${a.title}`}>
          Edit
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            remove.reset()
            setDeleting(a.id)
          }}
          aria-label={`Delete ${a.title}`}
        >
          Delete
        </Button>
      </div>
    )

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1>Appointments</h1>
        <Button onClick={() => setEditing('new')}>Add an appointment</Button>
      </div>
      {remove.isError && <ErrorState message={userMessage(remove.error, 'patient')} />}
      <AppointmentList title="Upcoming" items={list.data.upcoming} actions={actions} />
      <AppointmentList title="Past" items={list.data.past} actions={actions} />
    </section>
  )
}

function AppointmentList({
  title,
  items,
  actions,
}: {
  title: string
  items: Appointment[]
  actions: (a: Appointment) => ReactNode
}) {
  const id = `appointments-${title.toLowerCase()}`
  return (
    <section aria-labelledby={id} className="flex flex-col gap-3">
      <h2 id={id}>{title}</h2>
      {items.length === 0 ? (
        <Card>
          <p className="text-muted">No {title.toLowerCase()} appointments.</p>
        </Card>
      ) : (
        <ul className="flex flex-col gap-3">
          {items.map((a) => (
            <li key={a.id}>
              <AppointmentCard appointment={a} actions={actions(a)} />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

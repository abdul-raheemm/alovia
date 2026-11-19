import {
  ApiError,
  userMessage,
  type Appointment,
  type AppointmentInput,
  type AppointmentList,
} from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton, TextAreaField, TextField } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { formatDay } from '../../app/patients'
import { api } from '../../app/services'

const when = (a: Appointment) => `${formatDay(a.date)}${a.time ? `, ${a.time.slice(0, 5)}` : ''}`

/** Date, optional time, title (max 100), note (max 500) — the Journey §9.3 limits. */
function AppointmentForm({
  initial,
  onSave,
  onCancel,
}: {
  initial?: Appointment
  onSave: (body: AppointmentInput) => Promise<unknown>
  onCancel?: () => void
}) {
  const [date, setDate] = useState(initial?.date ?? '')
  const [time, setTime] = useState(initial?.time?.slice(0, 5) ?? '')
  const [title, setTitle] = useState(initial?.title ?? '')
  const [note, setNote] = useState(initial?.note ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  return (
    <form
      noValidate
      className="flex max-w-xl flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        const found: Record<string, string> = {}
        if (!date) found.date = 'Choose a date.'
        if (!title.trim()) found.title = 'Enter a title.'
        setErrors(found)
        setFormError(null)
        if (Object.keys(found).length) return
        setBusy(true)
        onSave({ date, time: time || null, title: title.trim(), note: note.trim() || null })
          .catch((err: unknown) => {
            if (err instanceof ApiError && err.fields) setErrors(err.fields)
            setFormError(userMessage(err, 'doctor'))
          })
          .finally(() => setBusy(false))
      }}
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label="Date"
          type="date"
          value={date}
          error={errors.date}
          onChange={(e) => setDate(e.target.value)}
        />
        <TextField
          label="Time (optional)"
          type="time"
          value={time}
          error={errors.time}
          onChange={(e) => setTime(e.target.value)}
        />
      </div>
      <TextField
        label="Title"
        value={title}
        maxLength={100}
        error={errors.title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <TextAreaField
        label="Note (optional)"
        value={note}
        maxLength={500}
        error={errors.note}
        onChange={(e) => setNote(e.target.value)}
      />
      {formError && (
        <p role="alert" className="text-urgent">
          {formError}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button type="submit" loading={busy}>
          {initial ? 'Save changes' : 'Add appointment'}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}

/** Dashboard §16: doctors add appointments to the patient's calendar and edit or delete only
 * doctor-added ones; the patient's own are shown read-only. */
export function AppointmentsTab({ patientId }: { patientId: string }) {
  const qc = useQueryClient()
  const key = ['doctor-appointments', patientId]
  const list = useQuery({
    queryKey: key,
    queryFn: () => api.get<AppointmentList>(`/doctor/patients/${patientId}/appointments`),
  })
  const [editing, setEditing] = useState<string | null>(null)
  const refresh = () => void qc.invalidateQueries({ queryKey: key })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/doctor/appointments/${id}`),
    onSuccess: refresh,
  })

  const row = (a: Appointment) => (
    <li key={a.id}>
      <Card className="flex flex-col gap-2">
        {editing === a.id ? (
          <AppointmentForm
            initial={a}
            onCancel={() => setEditing(null)}
            onSave={async (body) => {
              await api.put(`/doctor/appointments/${a.id}`, body)
              setEditing(null)
              refresh()
            }}
          />
        ) : (
          <>
            <p className="font-semibold">{a.title}</p>
            <p className="text-sm text-muted">
              {when(a)} · {a.source === 'doctor' ? 'Added by a doctor' : 'Added by the patient'}
            </p>
            {a.note && <p className="whitespace-pre-line">{a.note}</p>}
            {a.can_edit && (
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => setEditing(a.id)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  loading={remove.isPending && remove.variables === a.id}
                  onClick={() => remove.mutate(a.id)}
                >
                  Delete
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </li>
  )

  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="add-appt-heading" className="flex flex-col gap-3">
        <h2 id="add-appt-heading">Add appointment</h2>
        <AppointmentForm
          key={list.dataUpdatedAt}
          onSave={async (body) => {
            await api.post(`/doctor/patients/${patientId}/appointments`, body)
            refresh()
          }}
        />
      </section>
      {list.isPending ? (
        <PageSkeleton />
      ) : list.isError ? (
        <ErrorState
          message={userMessage(list.error, 'doctor')}
          onRetry={() => void list.refetch()}
        />
      ) : (
        <>
          {remove.isError && (
            <p role="alert" className="text-urgent">
              {userMessage(remove.error, 'doctor')}
            </p>
          )}
          <section aria-labelledby="upcoming-heading" className="flex flex-col gap-3">
            <h2 id="upcoming-heading">Upcoming</h2>
            {list.data.upcoming.length ? (
              <ul className="flex flex-col gap-3">{list.data.upcoming.map(row)}</ul>
            ) : (
              <p className="text-muted">No upcoming appointments.</p>
            )}
          </section>
          {list.data.past.length > 0 && (
            <section aria-labelledby="past-heading" className="flex flex-col gap-3">
              <h2 id="past-heading">Past</h2>
              <ul className="flex flex-col gap-3">{list.data.past.map(row)}</ul>
            </section>
          )}
        </>
      )}
    </div>
  )
}

import { ApiError, userMessage, type Appointment, type AppointmentInput } from '@alovia/shared'
import { Button, Card, ErrorState, TextAreaField, TextField } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Stethoscope } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'

import { appointmentWhen } from '../../app/journey'
import { api } from '../../app/services'
import { refreshAppointments } from '../../app/useAppointments'

/** Journey §9.3 limits (the backend checks them too). */
const TITLE_MAX = 100
const NOTE_MAX = 500

/** "Added by your doctor" (§9.3): doctor-added appointments are read-only for her. */
export function DoctorAddedLabel() {
  return (
    <p className="flex items-center gap-1 text-sm font-semibold text-primary">
      <Stethoscope aria-hidden="true" className="size-4" />
      Added by your doctor
    </p>
  )
}

/** One appointment: title, day and time, note, and who added it. `actions` only for her own. */
export function AppointmentCard({
  appointment,
  actions,
}: {
  appointment: Appointment
  actions?: ReactNode
}) {
  return (
    <Card className="flex flex-col gap-1">
      <h3>{appointment.title}</h3>
      <p>{appointmentWhen(appointment)}</p>
      {appointment.note && <p className="text-sm whitespace-pre-line">{appointment.note}</p>}
      {appointment.source === 'doctor' && <DoctorAddedLabel />}
      {appointment.can_edit && actions}
    </Card>
  )
}

/** Add or edit her own appointment (§9.3, UX_FLOWS P8): date, optional time, title, note. */
export function AppointmentForm({
  initial,
  onDone,
}: {
  initial?: Appointment
  onDone: () => void
}) {
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    date: initial?.date ?? '',
    time: initial?.time?.slice(0, 5) ?? '', // "HH:MM:SS" -> the time input's "HH:MM"
    title: initial?.title ?? '',
    note: initial?.note ?? '',
  })
  const [missing, setMissing] = useState<string[]>([])

  const save = useMutation({
    mutationFn: (body: AppointmentInput) =>
      initial
        ? api.put<Appointment>(`/patient/appointments/${initial.id}`, body)
        : api.post<Appointment>('/patient/appointments', body),
    onSuccess: async () => {
      await refreshAppointments(queryClient)
      onDone()
    },
  })

  function submit(e: FormEvent) {
    e.preventDefault()
    const empty = (['date', 'title'] as const).filter((name) => !values[name].trim())
    setMissing(empty)
    if (empty.length > 0) return
    save.mutate({
      date: values.date,
      time: values.time || null,
      title: values.title,
      note: values.note || null,
    })
  }

  const fields = save.error instanceof ApiError ? (save.error.fields ?? {}) : {}
  const fieldError = (name: string) =>
    missing.includes(name)
      ? 'Please fill this in.'
      : fields[name]
        ? 'Please check this value.'
        : undefined
  const otherError =
    save.isError && Object.keys(fields).length === 0 ? userMessage(save.error, 'patient') : null
  const set = (name: keyof typeof values) => (e: { target: { value: string } }) =>
    setValues((v) => ({ ...v, [name]: e.target.value }))

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      {otherError && <ErrorState message={otherError} />}
      <TextField
        label="Date"
        type="date"
        value={values.date}
        onChange={set('date')}
        error={fieldError('date')}
        required
      />
      <TextField
        label="Time (optional)"
        type="time"
        value={values.time}
        onChange={set('time')}
        error={fieldError('time')}
      />
      <TextField
        label="Title"
        value={values.title}
        onChange={set('title')}
        maxLength={TITLE_MAX}
        error={fieldError('title')}
        required
      />
      <TextAreaField
        label="Note (optional)"
        value={values.note}
        onChange={set('note')}
        maxLength={NOTE_MAX}
        error={fieldError('note')}
      />
      <div className="flex flex-wrap gap-3">
        <Button type="submit" loading={save.isPending}>
          Save
        </Button>
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

import {
  ApiError,
  userMessage,
  type AdminDoctor,
  type AssignmentPatient,
  type AuditEntry,
} from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton, TextField } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'

import { formatDateTime } from '../app/patients'
import { api } from '../app/services'

/** UX A1: invite a doctor by email; Supabase sends the email, its link opens Set password. */
function InviteForm() {
  const qc = useQueryClient()
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [specialty, setSpecialty] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [sent, setSent] = useState<string | null>(null)
  const invite = useMutation({
    mutationFn: () =>
      api.post<AdminDoctor>('/admin/doctors', {
        email: email.trim(),
        name: name.trim(),
        specialty: specialty.trim() || null,
      }),
    onSuccess: (d) => {
      setSent(d.email)
      setEmail('')
      setName('')
      setSpecialty('')
      void qc.invalidateQueries({ queryKey: ['admin-doctors'] })
    },
    onError: (err) => {
      if (err instanceof ApiError && err.fields) {
        setErrors(Object.fromEntries(Object.keys(err.fields).map((k) => [k, 'Please check this.'])))
      }
    },
  })
  function submit(e: FormEvent) {
    e.preventDefault()
    const found: Record<string, string> = {}
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) found.email = 'Enter a valid email.'
    if (!name.trim()) found.name = 'Enter the name.'
    setErrors(found)
    setSent(null)
    if (Object.keys(found).length === 0) invite.mutate()
  }
  return (
    <form noValidate onSubmit={submit} className="flex max-w-xl flex-col gap-3">
      <TextField
        label="Email"
        type="email"
        value={email}
        error={errors.email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <div className="grid gap-3 sm:grid-cols-2">
        <TextField
          label="Name"
          value={name}
          maxLength={100}
          error={errors.name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextField
          label="Specialty (optional)"
          value={specialty}
          maxLength={100}
          onChange={(e) => setSpecialty(e.target.value)}
        />
      </div>
      {invite.isError && (
        <p role="alert" className="text-urgent">
          {userMessage(invite.error, 'doctor')}
        </p>
      )}
      {sent && <p role="status">Invite sent to {sent}.</p>}
      <Button type="submit" className="self-start" loading={invite.isPending}>
        Send invite
      </Button>
    </form>
  )
}

function DoctorRow({ d }: { d: AdminDoctor }) {
  const qc = useQueryClient()
  const toggle = useMutation({
    mutationFn: () =>
      api.put<AdminDoctor>(`/admin/doctors/${d.id}`, {
        name: d.name,
        specialty: d.specialty,
        is_active: !d.is_active,
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['admin-doctors'] }),
  })
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-3">
      <div>
        <p className="font-semibold">
          {d.name}
          {d.specialty ? ` · ${d.specialty}` : ''}
        </p>
        <p className="text-sm text-muted">
          {d.email} · {d.patient_count} patients · {d.is_active ? 'Active' : 'Deactivated'}
        </p>
        {toggle.isError && (
          <p role="alert" className="text-sm text-urgent">
            {userMessage(toggle.error, 'doctor')}
          </p>
        )}
      </div>
      <Button
        variant={d.is_active ? 'ghost' : 'secondary'}
        loading={toggle.isPending}
        onClick={() => toggle.mutate()}
        aria-label={`${d.is_active ? 'Deactivate' : 'Reactivate'} ${d.name}`}
      >
        {d.is_active ? 'Deactivate' : 'Reactivate'}
      </Button>
    </li>
  )
}

function DoctorsSection({ doctors }: { doctors: AdminDoctor[] }) {
  return (
    <section aria-labelledby="doctors-heading" className="flex flex-col gap-3">
      <h2 id="doctors-heading">Doctors</h2>
      <InviteForm />
      <Card className="py-2">
        {doctors.length === 0 ? (
          <p className="py-3">No doctors yet.</p>
        ) : (
          <ul className="divide-y divide-border">
            {doctors.map((d) => (
              <DoctorRow key={d.id} d={d} />
            ))}
          </ul>
        )}
      </Card>
    </section>
  )
}

/** UX A2: search a patient, add or remove doctors, set the primary one; removing the last
 * doctor is refused by the server (§21). */
function AssignmentCard({ p, doctors }: { p: AssignmentPatient; doctors: AdminDoctor[] }) {
  const qc = useQueryClient()
  const selectId = useId()
  const [pick, setPick] = useState('')
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['admin-assignments'] })
    void qc.invalidateQueries({ queryKey: ['admin-doctors'] })
  }
  const change = useMutation({
    mutationFn: (a: { kind: 'add' | 'primary' | 'remove'; doctorId: string }) =>
      a.kind === 'remove'
        ? api.delete(`/admin/assignments?patient_id=${p.patient_id}&doctor_id=${a.doctorId}`)
        : api.post('/admin/assignments', {
            patient_id: p.patient_id,
            doctor_id: a.doctorId,
            is_primary: a.kind === 'primary',
          }),
    onSuccess: () => {
      setPick('')
      refresh()
    },
  })
  const assigned = new Set(p.doctors.map((d) => d.doctor_id))
  const addable = doctors.filter((d) => d.is_active && !assigned.has(d.id))
  return (
    <Card className="flex flex-col gap-3">
      <h3>{p.patient_name}</h3>
      <ul className="flex flex-col gap-2">
        {p.doctors.map((d) => (
          <li key={d.doctor_id} className="flex flex-wrap items-center justify-between gap-2">
            <span>
              {d.name}
              {d.is_primary ? ' (primary)' : ''}
              {d.is_active ? '' : ' · deactivated'}
            </span>
            <span className="flex flex-wrap gap-2">
              {!d.is_primary && (
                <Button
                  variant="ghost"
                  onClick={() => change.mutate({ kind: 'primary', doctorId: d.doctor_id })}
                  aria-label={`Make ${d.name} primary for ${p.patient_name}`}
                >
                  Make primary
                </Button>
              )}
              <Button
                variant="ghost"
                onClick={() => change.mutate({ kind: 'remove', doctorId: d.doctor_id })}
                aria-label={`Remove ${d.name} from ${p.patient_name}`}
              >
                Remove
              </Button>
            </span>
          </li>
        ))}
      </ul>
      {addable.length > 0 && (
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1">
            <label htmlFor={selectId} className="text-sm font-semibold">
              Add a doctor
            </label>
            <select
              id={selectId}
              value={pick}
              onChange={(e) => setPick(e.target.value)}
              className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
            >
              <option value="">Choose…</option>
              {addable.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <Button
            variant="secondary"
            disabled={!pick}
            onClick={() => change.mutate({ kind: 'add', doctorId: pick })}
          >
            Add
          </Button>
        </div>
      )}
      {change.isError && (
        <p role="alert" className="text-urgent">
          {userMessage(change.error, 'doctor')}
        </p>
      )}
    </Card>
  )
}

function AssignmentsSection({ doctors }: { doctors: AdminDoctor[] }) {
  const [q, setQ] = useState('')
  const patients = useQuery({
    queryKey: ['admin-assignments', q],
    queryFn: () =>
      api.get<AssignmentPatient[]>(`/admin/assignments?q=${encodeURIComponent(q.trim())}`),
  })
  return (
    <section aria-labelledby="assign-heading" className="flex flex-col gap-3">
      <h2 id="assign-heading">Assignments</h2>
      <TextField
        label="Search patients by name"
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {patients.isPending ? (
        <PageSkeleton />
      ) : patients.isError ? (
        <ErrorState
          message={userMessage(patients.error, 'doctor')}
          onRetry={() => void patients.refetch()}
        />
      ) : patients.data.length === 0 ? (
        <p className="text-muted">No patients found.</p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {patients.data.map((p) => (
            <AssignmentCard key={p.patient_id} p={p} doctors={doctors} />
          ))}
        </div>
      )}
    </section>
  )
}

/** UX A3: all entries, filtered by user, action and date; never clinical values (§20). */
export function AuditTable({ entries, caption }: { entries: AuditEntry[]; caption: string }) {
  if (entries.length === 0) return <p className="text-muted">No entries.</p>
  return (
    <div
      className="overflow-x-auto"
      role="region"
      aria-label={caption}
      // WCAG 2.1.1: keyboard users must be able to scroll the wide table
      // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
      tabIndex={0}
    >
      <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {['When', 'Who', 'Action', 'Record', 'Patient'].map((h) => (
              <th key={h} scope="col" className="border-b border-border px-2 py-2">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id} className="border-b border-border last:border-0">
              <td className="px-2 py-2">{formatDateTime(e.created_at)}</td>
              <td className="px-2 py-2">
                {e.actor_name ?? e.actor_email ?? '—'}
                {e.actor_role ? ` (${e.actor_role})` : ''}
              </td>
              <th scope="row" className="px-2 py-2 font-normal">
                {e.action}
              </th>
              <td className="px-2 py-2">{e.entity_type}</td>
              <td className="px-2 py-2">{e.patient_name ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AuditSection() {
  const actionId = useId()
  const [actor, setActor] = useState('')
  const [action, setAction] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const params = new URLSearchParams()
  if (actor.trim()) params.set('actor', actor.trim())
  if (action) params.set('action', action)
  if (from) params.set('day_from', from)
  if (to) params.set('day_to', to)
  const actions = useQuery({
    queryKey: ['audit-actions'],
    queryFn: () => api.get<string[]>('/admin/audit/actions'),
  })
  const log = useQuery({
    queryKey: ['admin-audit', params.toString()],
    queryFn: () => api.get<AuditEntry[]>(`/admin/audit?${params.toString()}`),
  })
  return (
    <section aria-labelledby="audit-heading" className="flex flex-col gap-3">
      <h2 id="audit-heading">Activity log</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <TextField
          label="User (email or name)"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
        />
        <div className="flex flex-col gap-1">
          <label htmlFor={actionId} className="font-semibold">
            Action
          </label>
          <select
            id={actionId}
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
          >
            <option value="">Any</option>
            {(actions.data ?? []).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <TextField
          label="From"
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
        <TextField label="To" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
      </div>
      {log.isPending ? (
        <PageSkeleton />
      ) : log.isError ? (
        <ErrorState message={userMessage(log.error, 'doctor')} onRetry={() => void log.refetch()} />
      ) : (
        <Card>
          <AuditTable entries={log.data} caption="Activity log entries" />
          <p className="mt-2 text-sm text-muted">Newest 200 entries matching the filters.</p>
        </Card>
      )}
    </section>
  )
}

/** Admin (Dashboard §21; admin role only): Doctors, Assignments, Activity log. */
export function AdminPage() {
  const doctors = useQuery({
    queryKey: ['admin-doctors'],
    queryFn: () => api.get<AdminDoctor[]>('/admin/doctors'),
  })
  return (
    <section className="flex flex-col gap-8">
      <h1>Admin</h1>
      {doctors.isPending ? (
        <PageSkeleton />
      ) : doctors.isError ? (
        <ErrorState
          message={userMessage(doctors.error, 'doctor')}
          onRetry={() => void doctors.refetch()}
        />
      ) : (
        <>
          <DoctorsSection doctors={doctors.data} />
          <AssignmentsSection doctors={doctors.data} />
        </>
      )}
      <AuditSection />
    </section>
  )
}

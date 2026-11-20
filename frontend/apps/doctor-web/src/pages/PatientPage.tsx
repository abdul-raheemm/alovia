import { userMessage, type InviteLink, type PatientDetail } from '@alovia/shared'
import { Button, Card, cn, ErrorState, PageSkeleton } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Copy, Link2 } from 'lucide-react'
import { useId, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'

import {
  DUE_DATE_SOURCE,
  formatDate,
  formatDateTime,
  formatDay,
  gaLabel,
  geneticLabel,
  PREGNANCY_STATUS,
  TABS,
  type TabId,
} from '../app/patients'
import { api } from '../app/services'
import { AppointmentsTab } from '../components/care/AppointmentsTab'
import { GeneticTab } from '../components/care/GeneticReview'
import { NotesTab } from '../components/care/NotesTab'
import { PregnancyTab } from '../components/care/PregnancyTab'
import { RecordsTab } from '../components/care/RecordsTab'
import { SymptomsTab } from '../components/care/SymptomsTab'
import { PatientForm } from '../components/PatientForm'
import { PredictionTab } from '../components/predictions/PredictionTab'

function Box({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card className="flex flex-col gap-1">
      <h3 className="text-base">{title}</h3>
      {children}
    </Card>
  )
}

function LatestLine({ label, at }: { label?: string; at?: string }) {
  if (!label || !at) return <p className="text-muted">No result yet</p>
  return (
    <p>
      <span className="text-lg font-semibold">{label}</span>{' '}
      <span className="text-sm text-muted">({formatDate(at)})</span>
    </p>
  )
}

/** §8.2 / UX_FLOWS D3: the link is shown once, with Copy; a new link replaces an unused one. */
function InvitePanel({ patient }: { patient: PatientDetail }) {
  const linkId = useId()
  const [copied, setCopied] = useState(false)
  const invite = useMutation({
    mutationFn: () => api.post<InviteLink>(`/doctor/patients/${patient.id}/invite`, {}),
    onSuccess: () => setCopied(false),
  })
  if (patient.linked) return <p>{patient.name} has joined Alovia.</p>
  return (
    <div className="flex flex-col gap-3">
      <p>
        {patient.name} has not joined yet. Send an invite link outside the app (WhatsApp, SMS or
        email). A new link replaces an unused earlier one.
      </p>
      <Button
        variant="secondary"
        className="self-start"
        loading={invite.isPending}
        onClick={() => invite.mutate()}
      >
        <Link2 aria-hidden="true" className="size-5" />
        {invite.data ? 'Create a new invite link' : 'Invite patient'}
      </Button>
      {invite.isError && (
        <p role="alert" className="text-urgent">
          {userMessage(invite.error, 'doctor')}
        </p>
      )}
      {invite.data && (
        <div className="flex flex-col gap-2">
          <label htmlFor={linkId} className="font-semibold">
            Invite link
          </label>
          <div className="flex flex-wrap gap-2">
            <input
              id={linkId}
              readOnly
              value={invite.data.link}
              onFocus={(e) => e.target.select()}
              className="min-h-11 min-w-0 flex-1 rounded-sm border border-border bg-surface px-3 text-base text-text"
            />
            <Button
              variant="secondary"
              onClick={() =>
                void navigator.clipboard.writeText(invite.data.link).then(() => setCopied(true))
              }
            >
              <Copy aria-hidden="true" className="size-5" />
              Copy
            </Button>
          </div>
          <p role="status" className="text-sm text-muted">
            {copied ? 'Copied. ' : ''}Expires on {formatDateTime(invite.data.expires_at)}.
          </p>
        </div>
      )}
    </div>
  )
}

/** §5.1 Overview tab: each result in its own box, never combined. The AI-1 summary is
 * Phase 6. Quick actions open the tabs that later tasks fill. */
function Overview({ patient }: { patient: PatientDetail }) {
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const quick: [TabId, string][] = [
    ['fetal', 'Enter CTG'],
    ['maternal', 'Enter vitals'],
    ['notes', 'Add note'],
    ['appointments', 'Add appointment'],
    ['records', 'Upload record'],
  ]
  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="details-heading" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="details-heading">Details</h2>
          {!editing && (
            <Button variant="ghost" onClick={() => setEditing(true)}>
              Edit details
            </Button>
          )}
        </div>
        {editing ? (
          <PatientForm
            initial={{
              name: patient.name,
              age: patient.age?.toString() ?? '',
              notes: patient.notes ?? '',
            }}
            submitLabel="Save changes"
            onCancel={() => setEditing(false)}
            onSubmit={async (input) => {
              await api.put<PatientDetail>(`/doctor/patients/${patient.id}`, input)
              await qc.invalidateQueries({ queryKey: ['doctor-patient', patient.id] })
              void qc.invalidateQueries({ queryKey: ['doctor-patients'] })
              setEditing(false)
            }}
          />
        ) : (
          <Card>
            <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
              {[
                ['Age', patient.age?.toString() ?? '—'],
                ['Gestational age', gaLabel(patient)],
                [
                  'Due date',
                  patient.due_date
                    ? `${formatDay(patient.due_date)}${patient.due_date_source ? ` (${DUE_DATE_SOURCE[patient.due_date_source]})` : ''}`
                    : '—',
                ],
                ['Pregnancy status', PREGNANCY_STATUS[patient.pregnancy_status]],
                [
                  'Assigned doctors',
                  patient.doctors
                    .map((d) => (d.is_primary ? `${d.name} (primary)` : d.name))
                    .join(', '),
                ],
                ['Notes (doctors only)', patient.notes ?? '—'],
              ].map(([term, value]) => (
                <div key={term}>
                  <dt className="text-sm text-muted">{term}</dt>
                  <dd className="whitespace-pre-line">{value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        )}
      </section>

      <section aria-labelledby="latest-heading" className="flex flex-col gap-3">
        <h2 id="latest-heading">Latest results</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Box title="Fetal">
            <LatestLine label={patient.fetal?.predicted_class} at={patient.fetal?.created_at} />
          </Box>
          <Box title="Maternal">
            <LatestLine
              label={patient.maternal?.predicted_class}
              at={patient.maternal?.created_at}
            />
          </Box>
          <Box title="Genetic">
            <p className="font-semibold">{geneticLabel(patient.genetic)}</p>
          </Box>
          <Box title="Symptoms (latest level)">
            <LatestLine label={patient.symptom?.level} at={patient.symptom?.created_at} />
          </Box>
        </div>
      </section>

      <section aria-labelledby="invite-heading" className="flex flex-col gap-3">
        <h2 id="invite-heading">Patient app</h2>
        <Card>
          <InvitePanel patient={patient} />
        </Card>
      </section>

      <section aria-labelledby="actions-heading" className="flex flex-col gap-3">
        <h2 id="actions-heading">Quick actions</h2>
        <ul className="flex flex-wrap gap-3">
          {quick.map(([tab, label]) => (
            <li key={tab}>
              <Button asChild variant="secondary">
                <Link to={`/patients/${patient.id}/${tab}`}>{label}</Link>
              </Button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

/** Patient detail (§5): tabs as links, so each tab has its own address (inbox items open the
 * related tab). */
export function PatientPage() {
  const { id = '', tab = 'overview' } = useParams()
  const patient = useQuery({
    queryKey: ['doctor-patient', id],
    queryFn: () => api.get<PatientDetail>(`/doctor/patients/${id}`),
  })
  const current = TABS.find((t) => t.id === tab) ?? TABS[0]

  if (patient.isPending) return <PageSkeleton />
  if (patient.isError) {
    return (
      <ErrorState
        message={userMessage(patient.error, 'doctor')}
        onRetry={() => void patient.refetch()}
      />
    )
  }
  return (
    <section className="flex flex-col gap-4">
      <p>
        <Link to="/patients">All patients</Link>
      </p>
      <h1>{patient.data.name}</h1>
      <nav aria-label="Patient sections" className="overflow-x-auto">
        <ul className="flex gap-1 border-b border-border">
          {TABS.map((t) => (
            <li key={t.id}>
              <Link
                to={`/patients/${id}/${t.id}`}
                aria-current={t.id === current.id ? 'page' : undefined}
                className={cn(
                  'flex min-h-11 items-center whitespace-nowrap px-3 no-underline',
                  t.id === current.id
                    ? 'border-b-2 border-primary font-semibold text-primary'
                    : 'text-text',
                )}
              >
                {t.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      {current.id === 'overview' ? (
        <Overview patient={patient.data} />
      ) : current.id === 'fetal' || current.id === 'maternal' ? (
        <PredictionTab key={current.id} model={current.id} patient={patient.data} />
      ) : current.id === 'genetic' ? (
        <GeneticTab patientId={id} />
      ) : current.id === 'symptoms' ? (
        <SymptomsTab patientId={id} />
      ) : current.id === 'notes' ? (
        <NotesTab patientId={id} />
      ) : current.id === 'appointments' ? (
        <AppointmentsTab patientId={id} />
      ) : current.id === 'pregnancy' ? (
        <PregnancyTab patient={patient.data} />
      ) : (
        <RecordsTab patientId={id} />
      )}
    </section>
  )
}

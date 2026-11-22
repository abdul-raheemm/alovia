import type { PatientDetail } from '@alovia/shared'
import { Button, Card } from '@alovia/ui'
import { useQueryClient } from '@tanstack/react-query'
import { UserPlus } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import { api } from '../app/services'
import { Inbox, useInbox } from '../components/Inbox'
import { PatientForm } from '../components/PatientForm'
import { PatientList, usePatients } from '../components/PatientList'

function NewPatientLink() {
  return (
    <Button asChild>
      <Link to="/patients/new">
        <UserPlus aria-hidden="true" className="size-5" />
        New patient
      </Link>
    </Button>
  )
}

/** One summary number (FRONTEND_REDESIGN §8.2): big tabular numeral, small label, no chart. */
function Tile({ label, value }: { label: string; value: number | undefined }) {
  return (
    <Card className="flex flex-col gap-1">
      <dt className="text-sm text-muted">{label}</dt>
      <dd className="text-3xl font-semibold tabular-nums">{value ?? '—'}</dd>
    </Card>
  )
}

/** Doctor home (Dashboard §5, UX_FLOWS D2, FRONTEND_REDESIGN §8.2): needs attention first, then
 * the summary tiles and a patient list preview. "Today's appointments" and recent activity have
 * no API yet and are left out (owner, 2026-11-22, DEC-116). */
export function HomePage() {
  const patients = usePatients()
  const unseen = useInbox()
  return (
    <section className="flex flex-col gap-6">
      <h1>Home</h1>
      <Inbox />
      <dl aria-label="Summary" className="grid grid-cols-2 gap-3 md:max-w-md">
        <Tile label="Patients" value={patients.data?.length} />
        <Tile label="Unseen alerts" value={unseen.data?.length} />
      </dl>
      <section aria-labelledby="patients-heading" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="patients-heading">Patients</h2>
          <NewPatientLink />
        </div>
        <PatientList preview={5} />
      </section>
    </section>
  )
}

export function PatientsPage() {
  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1>Patients</h1>
        <NewPatientLink />
      </div>
      <PatientList />
    </section>
  )
}

/** §8.1 / UX_FLOWS D3: create the record, then invite from the patient's page. */
export function NewPatientPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  return (
    <section className="flex flex-col gap-6">
      <h1>New patient</h1>
      <p className="text-muted">Use test data only (research prototype).</p>
      <PatientForm
        initial={{ name: '', age: '', notes: '' }}
        submitLabel="Save"
        onCancel={() => void navigate('/patients')}
        onSubmit={async (input) => {
          const created = await api.post<PatientDetail>('/doctor/patients', input)
          void qc.invalidateQueries({ queryKey: ['doctor-patients'] })
          void navigate(`/patients/${created.id}`)
        }}
      />
    </section>
  )
}

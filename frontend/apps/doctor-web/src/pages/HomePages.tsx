import type { PatientDetail } from '@alovia/shared'
import { Button } from '@alovia/ui'
import { useQueryClient } from '@tanstack/react-query'
import { UserPlus } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import { api } from '../app/services'
import { Inbox } from '../components/Inbox'
import { PatientForm } from '../components/PatientForm'
import { PatientList } from '../components/PatientList'

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

/** Doctor home (§5, UX_FLOWS D2): needs-attention inbox on top, then the patient list. */
export function HomePage() {
  return (
    <section className="flex flex-col gap-6">
      <h1>Home</h1>
      <Inbox />
      <section aria-labelledby="patients-heading" className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="patients-heading">Patients</h2>
          <NewPatientLink />
        </div>
        <PatientList />
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

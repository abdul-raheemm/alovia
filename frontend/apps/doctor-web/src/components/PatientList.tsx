import { userMessage, type PatientRow } from '@alovia/shared'
import { Card, CheckboxField, ErrorState, PageSkeleton, TextField } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import { useId, useState } from 'react'
import { Link } from 'react-router'

import {
  filterPatients,
  formatDate,
  formatDay,
  gaLabel,
  geneticLabel,
  NO_FILTERS,
  PREGNANCY_STATUS,
  type Filters,
} from '../app/patients'
import { api } from '../app/services'

export function usePatients() {
  return useQuery({
    queryKey: ['doctor-patients'],
    queryFn: () => api.get<PatientRow[]>('/doctor/patients'),
  })
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[] | Record<string, string>
  onChange: (value: string) => void
}) {
  const id = useId()
  const entries = Array.isArray(options) ? options.map((o) => [o, o]) : Object.entries(options)
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-semibold">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
      >
        <option value="">Any</option>
        {entries.map(([v, text]) => (
          <option key={v} value={v}>
            {text}
          </option>
        ))}
      </select>
    </div>
  )
}

function Latest({ value }: { value: { label: string; at: string } | null }) {
  if (!value) return <span className="text-muted">—</span>
  return (
    <>
      <span className="font-semibold">{value.label}</span>
      <span className="block text-sm text-muted">{formatDate(value.at)}</span>
    </>
  )
}

/** §6 patient list: the server's default order, search by name, filters by status columns.
 * Class labels are always written out; colour is never the only signal. */
export function PatientList() {
  const patients = usePatients()
  const [f, setF] = useState<Filters>(NO_FILTERS)
  const set = (patch: Partial<Filters>) => setF((old) => ({ ...old, ...patch }))

  if (patients.isPending) return <PageSkeleton />
  if (patients.isError) {
    return (
      <ErrorState
        message={userMessage(patients.error, 'doctor')}
        onRetry={() => void patients.refetch()}
      />
    )
  }
  if (patients.data.length === 0) {
    return (
      <Card>
        <p>No patients yet. Create a patient record to get started.</p>
      </Card>
    )
  }
  const rows = filterPatients(patients.data, f)
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <TextField
          label="Search by name"
          type="search"
          value={f.search}
          onChange={(e) => set({ search: e.target.value })}
        />
        <Select
          label="Pregnancy status"
          value={f.status}
          options={PREGNANCY_STATUS}
          onChange={(status) => set({ status })}
        />
        <Select
          label="Latest fetal class"
          value={f.fetal}
          options={['Normal', 'Suspect', 'Pathological']}
          onChange={(fetal) => set({ fetal })}
        />
        <Select
          label="Latest maternal class"
          value={f.maternal}
          options={['Low', 'Mid', 'High']}
          onChange={(maternal) => set({ maternal })}
        />
        <Select
          label="Genetic status"
          value={f.genetic}
          options={['None', 'Pending review', 'Pending review (high priority)', 'Reviewed']}
          onChange={(genetic) => set({ genetic })}
        />
        <Select
          label="Latest symptom level"
          value={f.symptom}
          options={['L0', 'L1', 'L2']}
          onChange={(symptom) => set({ symptom })}
        />
        <div className="self-end">
          <CheckboxField
            label="Only patients with unseen items"
            checked={f.unseenOnly}
            onChange={(e) => set({ unseenOnly: e.target.checked })}
          />
        </div>
      </div>
      <p role="status" className="text-sm text-muted">
        {rows.length} of {patients.data.length} patients
      </p>
      {/* the table scrolls inside its own box on small screens, never the page */}
      <div
        className="overflow-x-auto rounded-lg border border-border"
        role="region"
        aria-label="Patient list"
        // WCAG 2.1.1: keyboard users must be able to scroll the wide table (axe scrollable-region-focusable)
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
        tabIndex={0}
      >
        <table className="w-full min-w-[60rem] border-collapse text-left">
          <thead className="bg-surface text-sm">
            <tr>
              {[
                'Name',
                'Gestational age',
                'Due date',
                'Fetal',
                'Maternal',
                'Genetic',
                'Symptoms',
                'Unseen',
                'Pregnancy',
              ].map((h) => (
                <th key={h} scope="col" className="border-b border-border px-3 py-2">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-border align-top last:border-0">
                <th scope="row" className="px-3 py-2 font-normal">
                  <Link to={`/patients/${r.id}`} className="font-semibold">
                    {r.name}
                  </Link>
                  {!r.linked && <span className="block text-sm text-muted">Not joined yet</span>}
                </th>
                <td className="px-3 py-2">{gaLabel(r)}</td>
                <td className="px-3 py-2">{r.due_date ? formatDay(r.due_date) : '—'}</td>
                <td className="px-3 py-2">
                  <Latest
                    value={r.fetal && { label: r.fetal.predicted_class, at: r.fetal.created_at }}
                  />
                </td>
                <td className="px-3 py-2">
                  <Latest
                    value={
                      r.maternal && {
                        label: r.maternal.predicted_class,
                        at: r.maternal.created_at,
                      }
                    }
                  />
                </td>
                <td className="px-3 py-2">{geneticLabel(r.genetic)}</td>
                <td className="px-3 py-2">
                  <Latest
                    value={r.symptom && { label: r.symptom.level, at: r.symptom.created_at }}
                  />
                </td>
                <td className="px-3 py-2">
                  {r.unseen_count > 0 ? (
                    <span className="font-semibold">{r.unseen_count}</span>
                  ) : (
                    <span className="text-muted">0</span>
                  )}
                </td>
                <td className="px-3 py-2">{PREGNANCY_STATUS[r.pregnancy_status]}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="p-4">No patients match these filters.</p>}
      </div>
    </div>
  )
}

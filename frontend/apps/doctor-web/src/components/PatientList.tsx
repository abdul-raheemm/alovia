import { userMessage, type PatientRow } from '@alovia/shared'
import {
  Button,
  Card,
  CheckboxField,
  ErrorState,
  Sheet,
  TableRowSkeleton,
  TextField,
} from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronRight,
  Circle,
  CircleAlert,
  Dna,
  HeartPulse,
  SlidersHorizontal,
  Stethoscope,
  TriangleAlert,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useId, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'

import {
  filterPatients,
  formatDate,
  formatDay,
  gaLabel,
  geneticLabel,
  NO_FILTERS,
  pageOf,
  PREGNANCY_STATUS,
  sortPatients,
  type Filters,
  type Sort,
  type SortKey,
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

/** A status badge: module icon plus the value as text (colour is never the only signal).
 * Symptom levels use the reserved L1 / L2 colours; the other modules stay neutral. */
function Badge({
  Icon,
  text,
  tone,
}: {
  Icon: LucideIcon
  text: string
  tone?: 'urgent' | 'caution'
}) {
  return (
    <span
      className={
        tone === 'urgent'
          ? 'inline-flex items-center gap-1 rounded-md bg-urgent/10 px-2 py-0.5 text-sm font-semibold text-urgent'
          : tone === 'caution'
            ? 'inline-flex items-center gap-1 rounded-md bg-caution/10 px-2 py-0.5 text-sm font-semibold text-caution'
            : 'inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-sm'
      }
    >
      <Icon aria-hidden="true" className="size-4 shrink-0" />
      {text}
    </span>
  )
}

function SymptomBadge({ level }: { level: string }) {
  if (level === 'L1') return <Badge Icon={TriangleAlert} text="L1" tone="urgent" />
  if (level === 'L2') return <Badge Icon={CircleAlert} text="L2" tone="caution" />
  return <Badge Icon={Circle} text={level} />
}

function Latest({ value, badge }: { value: { at: string } | null; badge: ReactNode }) {
  if (!value) return <span className="text-muted">—</span>
  return (
    <span className="flex flex-col items-start gap-0.5">
      {badge}
      <span className="text-sm whitespace-nowrap text-muted tabular-nums">
        {formatDate(value.at)}
      </span>
    </span>
  )
}

const FILTER_LABEL: Record<Exclude<keyof Filters, 'search'>, string> = {
  status: 'Pregnancy',
  fetal: 'Fetal',
  maternal: 'Maternal',
  genetic: 'Genetic',
  symptom: 'Symptoms',
  unseenOnly: 'Unseen items',
}

function FilterFields({ f, set }: { f: Filters; set: (patch: Partial<Filters>) => void }) {
  return (
    <>
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
    </>
  )
}

const COLUMNS: { label: string; sort?: SortKey; className?: string }[] = [
  { label: 'Patient', sort: 'name' },
  { label: 'Gestational age', sort: 'ga' },
  { label: 'Due date', sort: 'due_date', className: 'max-2xl:hidden' },
  { label: 'Fetal' },
  { label: 'Maternal' },
  { label: 'Genetic' },
  { label: 'Last check-in', sort: 'last_checkin' },
  { label: 'Unseen', sort: 'unseen' },
  { label: 'Pregnancy', className: 'max-2xl:hidden' },
]

/** Patient list (Dashboard §6, FRONTEND_REDESIGN §8.3): the server's default order, sortable
 * columns, 25 per page, filters with removable chips, a search (also from the top bar's "?q=").
 * Phones get cards; arrow keys move between rows and Enter opens the patient.
 * `preview` = the first rows only, without filters (doctor home). */
export function PatientList({ preview }: { preview?: number }) {
  const patients = usePatients()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const q = params.get('q') ?? ''
  const [f, setF] = useState<Filters>({ ...NO_FILTERS, search: q })
  const [sort, setSort] = useState<Sort | null>(null)
  const [page, setPage] = useState(0)
  const [filtersOpen, setFiltersOpen] = useState(false)
  // a new search from the top bar (?q=) replaces the name search (React: adjust state in render)
  const [lastQ, setLastQ] = useState(q)
  if (q !== lastQ) {
    setLastQ(q)
    setF((old) => ({ ...old, search: q }))
  }
  const set = (patch: Partial<Filters>) => {
    setF((old) => ({ ...old, ...patch }))
    setPage(0)
  }

  if (patients.isPending) {
    return (
      <div role="status" aria-label="Loading" className="flex flex-col gap-2">
        {Array.from({ length: preview ?? 6 }, (_, i) => (
          <TableRowSkeleton key={i} />
        ))}
      </div>
    )
  }
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

  const filtered = preview ? patients.data : sortPatients(filterPatients(patients.data, f), sort)
  const shown = preview
    ? { rows: filtered.slice(0, preview), page: 0, pages: 1 }
    : pageOf(filtered, page)
  const active = (Object.keys(FILTER_LABEL) as (keyof typeof FILTER_LABEL)[]).filter((k) => f[k])
  const open = (r: PatientRow) => void navigate(`/patients/${r.id}`)
  // arrow keys move between rows, Enter opens the patient (§8.3)
  const onRowKey = (e: KeyboardEvent<HTMLTableRowElement>, r: PatientRow) => {
    const row = e.currentTarget
    if (e.key === 'ArrowDown') (row.nextElementSibling as HTMLElement | null)?.focus()
    else if (e.key === 'ArrowUp') (row.previousElementSibling as HTMLElement | null)?.focus()
    else if (e.key === 'Enter' && e.target === row) open(r)
    else return
    e.preventDefault()
  }
  const sortBy = (key: SortKey) =>
    setSort((s) =>
      s?.key !== key ? { key, dir: 'asc' } : s.dir === 'asc' ? { key, dir: 'desc' } : null,
    )

  return (
    <div className="flex flex-col gap-4">
      {!preview && (
        <>
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-0 flex-1 sm:max-w-sm">
              <TextField
                label="Search by name"
                type="search"
                value={f.search}
                onChange={(e) => set({ search: e.target.value })}
              />
            </div>
            <Button
              type="button"
              variant="secondary"
              className="md:hidden"
              onClick={() => setFiltersOpen(true)}
            >
              <SlidersHorizontal aria-hidden="true" className="size-5" />
              Filters{active.length > 0 ? ` (${active.length})` : ''}
            </Button>
          </div>
          <div className="hidden gap-3 md:grid md:grid-cols-3 xl:grid-cols-6">
            <FilterFields f={f} set={set} />
          </div>
          {active.length > 0 && (
            <ul aria-label="Active filters" className="flex flex-wrap items-center gap-2">
              {active.map((k) => (
                <li key={k}>
                  <button
                    type="button"
                    onClick={() => set({ [k]: k === 'unseenOnly' ? false : '' })}
                    className="inline-flex min-h-9 items-center gap-1 rounded-full bg-primary-soft py-1 pr-2 pl-3 text-sm font-semibold text-primary"
                  >
                    {FILTER_LABEL[k]}
                    {k !== 'unseenOnly' &&
                      `: ${k === 'status' ? PREGNANCY_STATUS[f.status] : f[k]}`}
                    <X aria-hidden="true" className="size-4" />
                    <span className="sr-only">(remove filter)</span>
                  </button>
                </li>
              ))}
              <li>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => set({ ...NO_FILTERS, search: f.search })}
                >
                  Clear all
                </Button>
              </li>
            </ul>
          )}
          <p role="status" className="text-sm text-muted">
            {filtered.length} of {patients.data.length} patients
          </p>
        </>
      )}

      {/* phones: cards (DESIGN_SYSTEM §15) */}
      <ul aria-label="Patient list" className="flex flex-col gap-2 md:hidden">
        {shown.rows.map((r) => (
          <li key={r.id}>
            <Link
              to={`/patients/${r.id}`}
              className="flex min-h-14 items-center gap-3 rounded-lg border border-border bg-surface p-3 no-underline"
            >
              <span className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="font-semibold text-text">{r.name}</span>
                <span className="text-sm text-muted tabular-nums">
                  {gaLabel(r)}
                  {!r.linked && ' · Not joined yet'}
                  {r.unseen_count > 0 && ` · ${r.unseen_count} unseen`}
                </span>
                <span className="flex flex-wrap gap-1">
                  {r.fetal && <Badge Icon={HeartPulse} text={`Fetal ${r.fetal.predicted_class}`} />}
                  {r.maternal && (
                    <Badge Icon={Stethoscope} text={`Maternal ${r.maternal.predicted_class}`} />
                  )}
                  {r.symptom && <SymptomBadge level={r.symptom.level} />}
                </span>
              </span>
              <ChevronRight aria-hidden="true" className="size-5 shrink-0 text-muted" />
            </Link>
          </li>
        ))}
      </ul>

      {/* tablets and laptops: a dense table with a sticky header */}
      <div
        className="hidden max-h-[70vh] overflow-auto rounded-lg border border-border md:block"
        role="region"
        aria-label="Patient list"
        // WCAG 2.1.1: keyboard users must be able to scroll the table (axe scrollable-region-focusable)
        // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
        tabIndex={0}
      >
        <table className="w-full border-collapse text-left">
          <thead className="text-sm">
            <tr>
              {COLUMNS.map((c) => (
                <th
                  key={c.label}
                  scope="col"
                  aria-sort={
                    sort && c.sort === sort.key
                      ? sort.dir === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                  className={`sticky top-0 z-10 border-b border-border bg-surface px-3 py-2 font-semibold ${c.className ?? ''}`}
                >
                  {c.sort && !preview ? (
                    <button
                      type="button"
                      onClick={() => sortBy(c.sort as SortKey)}
                      className="inline-flex min-h-9 items-center gap-1"
                    >
                      {c.label}
                      {sort?.key !== c.sort ? (
                        <ArrowUpDown aria-hidden="true" className="size-4 text-muted" />
                      ) : sort.dir === 'asc' ? (
                        <ArrowUp aria-hidden="true" className="size-4" />
                      ) : (
                        <ArrowDown aria-hidden="true" className="size-4" />
                      )}
                    </button>
                  ) : (
                    c.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.rows.map((r) => (
              <tr
                key={r.id}
                tabIndex={0}
                onClick={() => open(r)}
                onKeyDown={(e) => onRowKey(e, r)}
                className="h-12 cursor-pointer border-b border-border last:border-0 hover:bg-primary-soft/50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary"
              >
                <th scope="row" className="px-3 py-2 font-normal">
                  <Link
                    to={`/patients/${r.id}`}
                    className="font-semibold whitespace-nowrap"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {r.name}
                  </Link>
                  <span className="block text-xs text-muted tabular-nums">
                    ID {r.id.slice(0, 8)}
                    {!r.linked && ' · Not joined yet'}
                  </span>
                </th>
                <td className="px-3 py-2 tabular-nums">{gaLabel(r)}</td>
                <td className="px-3 py-2 tabular-nums max-2xl:hidden">
                  {r.due_date ? formatDay(r.due_date) : '—'}
                </td>
                <td className="px-3 py-2">
                  <Latest
                    value={r.fetal && { at: r.fetal.created_at }}
                    badge={r.fetal && <Badge Icon={HeartPulse} text={r.fetal.predicted_class} />}
                  />
                </td>
                <td className="px-3 py-2">
                  <Latest
                    value={r.maternal && { at: r.maternal.created_at }}
                    badge={
                      r.maternal && <Badge Icon={Stethoscope} text={r.maternal.predicted_class} />
                    }
                  />
                </td>
                <td className="px-3 py-2">
                  {r.genetic ? (
                    <Badge Icon={Dna} text={geneticLabel(r.genetic)} />
                  ) : (
                    <span className="text-muted">None</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <Latest
                    value={r.symptom && { at: r.symptom.created_at }}
                    badge={r.symptom && <SymptomBadge level={r.symptom.level} />}
                  />
                </td>
                <td className="px-3 py-2 tabular-nums">
                  {r.unseen_count > 0 ? (
                    <span className="font-semibold">{r.unseen_count}</span>
                  ) : (
                    <span className="text-muted">0</span>
                  )}
                </td>
                <td className="px-3 py-2 max-2xl:hidden">{PREGNANCY_STATUS[r.pregnancy_status]}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {shown.rows.length === 0 && <p className="p-4">No patients match these filters.</p>}
      </div>
      {!preview && shown.rows.length === 0 && (
        <p className="md:hidden">No patients match these filters.</p>
      )}

      {preview ? (
        <p className="text-sm">
          <Link to="/patients">All patients ({patients.data.length})</Link>
        </p>
      ) : (
        shown.pages > 1 && (
          <nav aria-label="Pages" className="flex items-center justify-between gap-3">
            <Button
              type="button"
              variant="secondary"
              disabled={shown.page === 0}
              onClick={() => setPage(shown.page - 1)}
            >
              Previous
            </Button>
            <span className="text-sm tabular-nums">
              Page {shown.page + 1} of {shown.pages}
            </span>
            <Button
              type="button"
              variant="secondary"
              disabled={shown.page >= shown.pages - 1}
              onClick={() => setPage(shown.page + 1)}
            >
              Next
            </Button>
          </nav>
        )
      )}

      <Sheet
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        labelledBy="filters-title"
        className="md:hidden"
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-border p-3">
            <h2 id="filters-title" className="text-xl">
              Filters
            </h2>
            <button
              type="button"
              aria-label="Close filters"
              onClick={() => setFiltersOpen(false)}
              className="flex size-11 items-center justify-center rounded-full hover:bg-primary-soft"
            >
              <X aria-hidden="true" className="size-5" />
            </button>
          </div>
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
            <FilterFields f={f} set={set} />
          </div>
          <div className="border-t border-border p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
            <Button type="button" className="w-full" onClick={() => setFiltersOpen(false)}>
              Show {filtered.length} patients
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  )
}

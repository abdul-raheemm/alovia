import { userMessage, type DoctorSymptoms } from '@alovia/shared'
import { Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts'

import { formatDateTime } from '../../app/patients'
import { api } from '../../app/services'
import { tableClass, useTableView } from '../ChartTable'

type Points = DoctorSymptoms['charts']['symptoms'][number]['points']

/** Entries of one symptom per pregnancy week (one series, one colour), with a text table. */
function SymptomChart({ label, points }: { label: string; points: Points }) {
  const [asTable, tableToggle] = useTableView()
  const counts = new Map<string, number>()
  for (const p of points) {
    const key = p.pregnancy_week === null ? 'no week' : `wk ${p.pregnancy_week}`
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  const data = [...counts].map(([week, n]) => ({ week, n }))
  return (
    <Card className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h4>{label}</h4>
        {tableToggle}
      </div>
      {!asTable && (
        <div aria-hidden="true" className="h-36 w-full">
          <ResponsiveContainer>
            <BarChart accessibilityLayer={false} data={data} margin={{ top: 8, right: 8, left: 0 }}>
              <CartesianGrid stroke="var(--color-border)" vertical={false} />
              <XAxis
                interval="preserveStartEnd"
                minTickGap={16}
                dataKey="week"
                tick={{ fill: 'var(--color-muted)', fontSize: 12 }}
              />
              <YAxis
                allowDecimals={false}
                width={32}
                tick={{ fill: 'var(--color-muted)', fontSize: 12 }}
              />
              <Bar
                dataKey="n"
                fill="var(--color-secondary)"
                radius={[4, 4, 0, 0]}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <table className={tableClass(asTable)}>
        <caption>{label}: entries per pregnancy week</caption>
        <tbody>
          {data.map((d) => (
            <tr key={d.week}>
              <th scope="row">{d.week}</th>
              <td>{d.n}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}

/** PUQE score over time with the bands from the rule file shaded and named. */
function PuqeChart({ data }: { data: DoctorSymptoms }) {
  const [asTable, tableToggle] = useTableView()
  const points = data.charts.puqe.map((p) => ({ ...p, x: p.local_date }))
  if (points.length === 0) return null
  return (
    <Card className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h4>PUQE score</h4>
        {tableToggle}
      </div>
      <p className="text-sm text-muted">
        Bands: {data.puqe_bands.map((b) => `${b.band} ${b.min}–${b.max}`).join(', ')}
      </p>
      {!asTable && (
        <div aria-hidden="true" className="h-40 w-full">
          <ResponsiveContainer>
            <LineChart
              accessibilityLayer={false}
              data={points}
              margin={{ top: 8, right: 16, left: 0 }}
            >
              {data.puqe_bands.map((b, i) => (
                <ReferenceArea
                  key={b.band}
                  y1={b.min}
                  y2={b.max}
                  fill="var(--color-primary)"
                  fillOpacity={0.06 + i * 0.06}
                />
              ))}
              <CartesianGrid stroke="var(--color-border)" vertical={false} />
              <XAxis
                interval="preserveStartEnd"
                minTickGap={16}
                dataKey="x"
                tick={{ fill: 'var(--color-muted)', fontSize: 12 }}
              />
              <YAxis
                domain={[3, 15]}
                width={32}
                tick={{ fill: 'var(--color-muted)', fontSize: 12 }}
              />
              <Line
                dataKey="score"
                stroke="var(--color-secondary)"
                strokeWidth={2}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <table className={tableClass(asTable)}>
        <caption>PUQE scores</caption>
        <tbody>
          {points.map((p, i) => (
            <tr key={i}>
              <th scope="row">{p.local_date}</th>
              <td>
                {p.score} ({p.band})
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}

/** Symptom §12 / Dashboard §13: timeline with levels and rule IDs, pattern badges with the
 * symptom named, notes in full, charts. Read-only. */
export function SymptomsTab({ patientId }: { patientId: string }) {
  const q = useQuery({
    queryKey: ['doctor-symptoms', patientId],
    queryFn: () => api.get<DoctorSymptoms>(`/doctor/patients/${patientId}/symptoms`),
  })
  if (q.isPending) return <PageSkeleton />
  if (q.isError) {
    return <ErrorState message={userMessage(q.error, 'doctor')} onRetry={() => void q.refetch()} />
  }
  const d = q.data
  const label = (id: string) => d.labels[id] ?? id
  if (d.checkins.length === 0) {
    return (
      <Card>
        <p>No symptom check-ins yet.</p>
      </Card>
    )
  }
  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="timeline-heading" className="flex flex-col gap-2">
        <h2 id="timeline-heading">Check-ins</h2>
        <ol className="flex flex-col gap-3">
          {d.checkins.map((c) => (
            <li key={c.checkin_id}>
              <Card className="flex flex-col gap-2">
                <p className="flex flex-wrap items-baseline gap-x-3">
                  <strong>Level {c.red_flag_level}</strong>
                  <span className="text-sm text-muted">
                    {formatDateTime(c.created_at)}
                    {c.pregnancy_week !== null ? ` · week ${c.pregnancy_week}` : ''}
                    {c.source === 'urgent_button' ? ' · urgent button' : ''}
                  </span>
                </p>
                {c.matched_rules.length > 0 && (
                  <p className="text-sm">Rules: {c.matched_rules.join(', ')}</p>
                )}
                {c.pattern_changes.length > 0 && (
                  <ul className="flex flex-wrap gap-2" aria-label="Pattern changes">
                    {c.pattern_changes.map((p) => (
                      <li
                        key={`${p.code}-${p.symptom ?? ''}`}
                        className="rounded-sm border border-caution px-2 text-sm"
                      >
                        {p.code}
                        {p.symptom ? `: ${label(p.symptom)}` : ''}
                      </li>
                    ))}
                  </ul>
                )}
                <ul className="flex flex-col gap-1">
                  {c.entries.map((e, i) => {
                    const detail = [e.severity, e.duration, e.body_area].filter(Boolean)
                    return (
                      <li key={i}>
                        <span className="font-semibold">{label(e.symptom)}</span>
                        {detail.length > 0 && ` — ${detail.join(', ')}`}
                        {e.notes && (
                          <span className="block whitespace-pre-line text-sm">Note: {e.notes}</span>
                        )}
                      </li>
                    )
                  })}
                </ul>
              </Card>
            </li>
          ))}
        </ol>
      </section>
      <section aria-labelledby="charts-heading" className="flex flex-col gap-2">
        <h2 id="charts-heading">Charts</h2>
        <PuqeChart data={d} />
        <div className="grid gap-3 lg:grid-cols-2">
          {d.charts.symptoms.map((s) => (
            <SymptomChart key={s.symptom} label={s.label} points={s.points} />
          ))}
        </div>
      </section>
    </div>
  )
}

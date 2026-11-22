import { userMessage, type SymptomCharts } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { ChartColumn } from 'lucide-react'
import { Link } from 'react-router'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatDay } from '../app/journey'
import { byWeek, SEVERITY_KEYS, type SeverityKey, type WeekRow } from '../app/symptoms'
import { useSymptomCharts } from '../app/useSymptoms'

// one hue, light -> dark (an ordered magnitude); validated for both themes (index.css)
const SEVERITY_STYLE: Record<SeverityKey, { label: string; color: string }> = {
  mild: { label: 'Mild', color: 'var(--chart-mild)' },
  moderate: { label: 'Moderate', color: 'var(--chart-moderate)' },
  severe: { label: 'Severe', color: 'var(--chart-severe)' },
  logged: { label: 'Logged (no severity)', color: 'var(--chart-logged)' },
}
const AXIS = { fontSize: 12, fill: 'var(--color-muted)' }
const TOOLTIP = {
  contentStyle: {
    background: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    color: 'var(--color-text)',
  },
}

/** Symptom history (Symptom spec §4.3): per symptom, how often and how severe by pregnancy
 * week (durations in the table), and the PUQE score over time. Her own data only. */
export function SymptomHistoryPage() {
  const charts = useSymptomCharts()
  if (charts.isPending) return <PageSkeleton />
  if (charts.isError) {
    return (
      <ErrorState
        message={userMessage(charts.error, 'patient')}
        onRetry={() => void charts.refetch()}
      />
    )
  }
  const { symptoms, puqe } = charts.data
  return (
    <section className="flex flex-col gap-6">
      <h1>Symptom history</h1>
      {symptoms.length === 0 ? (
        // empty state (FRONTEND_REDESIGN open item 6, DEC-118): existing words only
        <Card className="flex flex-col items-center gap-3 py-8 text-center">
          <span className="flex size-14 items-center justify-center rounded-full bg-primary-soft text-primary">
            <ChartColumn aria-hidden="true" className="size-7" />
          </span>
          <p className="text-muted">Nothing logged yet.</p>
          <Button asChild>
            <Link to="/log">Log a symptom</Link>
          </Button>
        </Card>
      ) : (
        symptoms.map((s) => (
          <SymptomChart key={s.symptom} label={s.label} rows={byWeek(s.points)} />
        ))
      )}
      {puqe.length > 0 && <PuqeChart points={puqe} />}
    </section>
  )
}

function SymptomChart({ label, rows }: { label: string; rows: WeekRow[] }) {
  const used = SEVERITY_KEYS.filter((k) => rows.some((r) => r[k] > 0))
  return (
    <Card className="flex flex-col gap-3">
      <h2>{label}</h2>
      <div className="h-48 w-full">
        <ResponsiveContainer>
          <BarChart data={rows} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke="var(--color-border)" />
            <XAxis dataKey="week" tick={AXIS} tickLine={false} axisLine={false} />
            <YAxis allowDecimals={false} tick={AXIS} tickLine={false} axisLine={false} />
            <Tooltip {...TOOLTIP} cursor={{ fill: 'var(--color-primary-soft)' }} />
            {used.length > 1 && (
              <Legend
                wrapperStyle={{ fontSize: 12 }}
                formatter={(value: string) => (
                  <span style={{ color: 'var(--color-text)' }}>{value}</span>
                )}
              />
            )}
            {used.map((k, i) => (
              <Bar
                key={k}
                dataKey={k}
                name={SEVERITY_STYLE[k].label}
                stackId="count"
                fill={SEVERITY_STYLE[k].color}
                stroke="var(--color-surface)"
                strokeWidth={2}
                maxBarSize={28}
                radius={i === used.length - 1 ? [4, 4, 0, 0] : 0}
                isAnimationActive={false}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
      <details>
        <summary className="cursor-pointer text-sm">Show as a table</summary>
        <table className="mt-2 w-full text-left text-sm">
          <thead>
            <tr>
              <th scope="col">Week</th>
              <th scope="col">Times logged</th>
              <th scope="col">Severity</th>
              <th scope="col">Duration</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.week}>
                <th scope="row" className="font-normal">
                  {r.week}
                </th>
                <td>{r.total}</td>
                <td>
                  {used
                    .filter((k) => r[k] > 0)
                    .map((k) => `${SEVERITY_STYLE[k].label}: ${r[k]}`)
                    .join(', ')}
                </td>
                <td>
                  {Object.entries(r.durations)
                    .map(([d, n]) => `${d.replaceAll('_', ' ')}: ${n}`)
                    .join(', ') || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </Card>
  )
}

function PuqeChart({ points }: { points: SymptomCharts['puqe'] }) {
  const data = points.map((p) => ({
    ...p,
    day: formatDay(p.local_date),
    short: new Date(`${p.local_date}T00:00:00Z`).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      timeZone: 'UTC',
    }),
  }))
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="font-sans">Nausea and vomiting score (PUQE-24)</h2>
      <div className="h-48 w-full">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke="var(--color-border)" />
            <XAxis
              dataKey="short"
              tick={AXIS}
              tickLine={false}
              axisLine={false}
              padding={{ left: 16, right: 16 }}
            />
            <YAxis
              domain={[3, 15]}
              ticks={[3, 6, 9, 12, 15]}
              tick={AXIS}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip {...TOOLTIP} />
            <Line
              type="monotone"
              dataKey="score"
              name="Score"
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={{
                r: 4,
                fill: 'var(--color-primary)',
                stroke: 'var(--color-surface)',
                strokeWidth: 2,
              }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <details>
        <summary className="cursor-pointer text-sm">Show as a table</summary>
        <table className="mt-2 w-full text-left text-sm">
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Week</th>
              <th scope="col">Score</th>
              <th scope="col">Band</th>
            </tr>
          </thead>
          <tbody>
            {data.map((p, i) => (
              <tr key={`${p.local_date}-${i}`}>
                <th scope="row" className="font-normal">
                  {p.day}
                </th>
                <td>{p.pregnancy_week ?? '—'}</td>
                <td>{p.score}</td>
                <td>{p.band}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </Card>
  )
}

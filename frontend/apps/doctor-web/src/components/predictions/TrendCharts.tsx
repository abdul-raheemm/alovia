import type { Trends } from '@alovia/shared'
import { Card } from '@alovia/ui'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatDate } from '../../app/patients'
import { shortNumber } from '../../app/predictions'

type Point = Trends['maternal'][number]

/** §11: point colour = the reading's predicted class, an ordered one-hue ramp (--class-1..3,
 * index.css); the class is also in the tooltip and the table, so colour is never alone. */
const CLASS_ORDER: Record<string, string[]> = {
  fetal: ['Normal', 'Suspect', 'Pathological'],
  maternal: ['Low', 'Mid', 'High'],
}
const classColour = (model: string, c: string) =>
  `var(--class-${(CLASS_ORDER[model]?.indexOf(c) ?? 0) + 1})`

const xLabel = (p: Point) =>
  `${formatDate(p.created_at)}${p.ga_week !== null ? ` · wk ${p.ga_week}` : ''}`

function Dot(model: string) {
  return function ClassDot(props: { cx?: number; cy?: number; payload?: Point }) {
    const { cx, cy, payload } = props
    if (cx === undefined || cy === undefined || !payload) return <g />
    return (
      <circle
        cx={cx}
        cy={cy}
        r={5}
        fill={classColour(model, payload.predicted_class)}
        stroke="var(--color-surface)"
        strokeWidth={2}
      />
    )
  }
}

function Chart({
  model,
  title,
  points,
  series,
}: {
  model: string
  title: string
  points: Point[]
  series: { feature: string; name: string; dashed?: boolean }[]
}) {
  const data = points.map((p) => ({ ...p.values, x: xLabel(p), cls: p.predicted_class, p }))
  return (
    <Card className="flex flex-col gap-2">
      <h4>{title}</h4>
      <div aria-hidden="true" className="h-48 w-full">
        <ResponsiveContainer>
          <LineChart
            accessibilityLayer={false}
            data={data}
            margin={{ top: 8, right: 16, bottom: 8, left: 0 }}
          >
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="x" tick={{ fill: 'var(--color-muted)', fontSize: 12 }} />
            <YAxis tick={{ fill: 'var(--color-muted)', fontSize: 12 }} width={48} />
            <Tooltip
              contentStyle={{
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                color: 'var(--color-text)',
              }}
              formatter={(v: unknown, name: unknown) => [shortNumber(Number(v)), String(name)]}
              labelFormatter={(
                label: unknown,
                payload: readonly { payload?: { cls?: string } }[],
              ) => `${String(label)} · ${payload[0]?.payload?.cls ?? ''}`}
            />
            {series.length > 1 && <Legend />}
            {series.map((s) => (
              <Line
                key={s.feature}
                dataKey={s.feature}
                name={s.name}
                stroke="var(--color-muted)"
                strokeWidth={2}
                strokeDasharray={s.dashed ? '6 4' : undefined}
                dot={Dot(model)}
                activeDot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>{title}</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            {series.map((s) => (
              <th key={s.feature} scope="col">
                {s.name}
              </th>
            ))}
            <th scope="col">Class</th>
          </tr>
        </thead>
        <tbody>
          {points.map((p) => (
            <tr key={p.result_id}>
              <th scope="row">{xLabel(p)}</th>
              {series.map((s) => (
                <td key={s.feature}>{shortNumber(p.values[s.feature] ?? 0)}</td>
              ))}
              <td>{p.predicted_class}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}

/** §11 trends in model units; no arrows, scores or interpretations. Systolic and diastolic
 * blood pressure share one chart (solid and dashed line, with a legend). */
export function TrendCharts({
  model,
  trends,
  featureLabels,
}: {
  model: 'fetal' | 'maternal'
  trends: Trends
  featureLabels: Record<string, string>
}) {
  const points = trends[model]
  if (points.length < 2) {
    return <p className="text-muted">Trends appear after two or more results.</p>
  }
  const label = (f: string) => featureLabels[f] ?? f
  const features = model === 'fetal' ? trends.fetal_features : trends.maternal_features
  const bp = features.filter((f) => /Blood Pressure/.test(f))
  const charts: { title: string; series: { feature: string; name: string; dashed?: boolean }[] }[] =
    []
  if (bp.length === 2) {
    charts.push({
      title: 'Blood pressure (mm Hg)',
      series: bp.map((f, i) => ({ feature: f, name: label(f), dashed: i === 1 })),
    })
  }
  for (const f of features) {
    if (!bp.includes(f) && f !== 'Age')
      charts.push({ title: label(f), series: [{ feature: f, name: label(f) }] })
  }
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted">
        Values in model units. Point colour shows the predicted class of that reading (lighter to
        darker: {CLASS_ORDER[model]?.join(', ')}); the class is also in each point's tooltip.
      </p>
      <div className="grid gap-3 lg:grid-cols-2">
        {charts.map((c) => (
          <Chart key={c.title} model={model} title={c.title} points={points} series={c.series} />
        ))}
      </div>
    </div>
  )
}

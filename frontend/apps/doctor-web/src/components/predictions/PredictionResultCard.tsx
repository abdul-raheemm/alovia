import { userMessage, type PredictionResult } from '@alovia/shared'
import { Button, Card, TextAreaField } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Info, Send } from 'lucide-react'
import { useState } from 'react'
import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts'

import { formatDateTime } from '../../app/patients'
import { messageText, shortNumber } from '../../app/predictions'
import { api } from '../../app/services'

const percent = (p: number) => `${Math.round(p * 100)}%`

/** §9.7 class probabilities: one series, so one colour; every bar carries its value. */
function Probabilities({ result }: { result: PredictionResult }) {
  const data = Object.entries(result.class_probabilities).map(([label, p]) => ({ label, p }))
  return (
    <figure className="flex flex-col gap-2">
      <figcaption className="font-semibold">Class probabilities</figcaption>
      <div aria-hidden="true" className="h-32 w-full">
        <ResponsiveContainer>
          <BarChart
            accessibilityLayer={false}
            data={data}
            layout="vertical"
            margin={{ left: 8, right: 48 }}
          >
            <XAxis type="number" domain={[0, 1]} hide />
            <YAxis
              type="category"
              dataKey="label"
              width={96}
              tick={{ fill: 'var(--color-text)', fontSize: 14 }}
              axisLine={false}
              tickLine={false}
            />
            <Bar dataKey="p" fill="var(--color-secondary)" radius={[0, 4, 4, 0]} barSize={16}>
              <LabelList
                dataKey="p"
                position="right"
                formatter={(v: unknown) => percent(Number(v))}
                style={{ fill: 'var(--color-text)', fontSize: 14 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {/* the same numbers as text, for screen readers and print */}
      <ul className="sr-only">
        {data.map((d) => (
          <li key={d.label}>
            {d.label}: {percent(d.p)}
          </li>
        ))}
      </ul>
    </figure>
  )
}

/** §10: preview of the patient view, optional message, confirm; cannot be undone. */
function ShareSection({
  result,
  messages,
  onShared,
}: {
  result: PredictionResult
  messages: Record<string, string | null>
  onShared: (r: PredictionResult) => void
}) {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const share = useMutation({
    mutationFn: () =>
      api.post<PredictionResult>(`/doctor/predictions/${result.model}/${result.id}/share`, {
        doctor_message: message.trim() || null,
      }),
    onSuccess: (r) => {
      setOpen(false)
      onShared(r)
    },
  })
  if (result.share) {
    return (
      <div className="flex flex-col gap-1 rounded-md bg-primary-soft p-3">
        <p className="font-semibold">
          Shared with the patient on {formatDateTime(result.share.shared_at)}
          {result.share.shared_by_name ? ` by ${result.share.shared_by_name}` : ''}
        </p>
        {result.share.doctor_message && (
          <p className="whitespace-pre-line">Message: {result.share.doctor_message}</p>
        )}
      </div>
    )
  }
  if (!open) {
    return (
      <Button variant="secondary" className="self-start" onClick={() => setOpen(true)}>
        <Send aria-hidden="true" className="size-5" />
        Share with patient
      </Button>
    )
  }
  const template = `result_template_${result.model}_${result.predicted_class.toLowerCase()}`
  return (
    <section aria-labelledby={`share-${result.id}`} className="flex flex-col gap-3">
      <h4 id={`share-${result.id}`}>What the patient will see</h4>
      <p className="rounded-md border border-border p-3">{messageText(messages, template)}</p>
      <p className="text-sm text-muted">
        The patient never sees probabilities, confidence or contributing factors. A share cannot be
        undone; a later note can add context.
      </p>
      <TextAreaField
        label="Message to the patient (optional)"
        value={message}
        maxLength={1000}
        onChange={(e) => setMessage(e.target.value)}
      />
      {share.isError && (
        <p role="alert" className="text-urgent">
          {userMessage(share.error, 'doctor')}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button loading={share.isPending} onClick={() => share.mutate()}>
          Confirm and share
        </Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
    </section>
  )
}

/** §9.7 one prediction with its explanation, warnings and limitations (§9.6), then sharing.
 * Decision support only; nothing here is editable (§1.3). */
export function PredictionResultCard({
  result,
  messages,
  limitationKeys,
  featureLabels,
}: {
  result: PredictionResult
  messages: Record<string, string | null>
  limitationKeys: string[]
  featureLabels: Record<string, string>
}) {
  const qc = useQueryClient()
  const label = (f: string) => featureLabels[f] ?? f
  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3>
          Predicted class: <span className="text-primary">{result.predicted_class}</span>
        </h3>
        <p>
          Confidence <span className="font-semibold">{percent(result.confidence)}</span>
        </p>
      </div>
      <p className="text-sm text-muted">
        AI decision support · {formatDateTime(result.created_at)} · entered by{' '}
        {result.entered_by_name ?? 'a doctor'} · model {result.model_version ?? 'unknown'}
      </p>
      <Probabilities result={result} />
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <caption className="mb-2 text-left font-semibold">Top contributing factors</caption>
          <thead className="text-sm">
            <tr>
              <th scope="col" className="border-b border-border py-2 pr-3">
                Feature
              </th>
              <th scope="col" className="border-b border-border py-2 pr-3">
                Impact
              </th>
              <th scope="col" className="border-b border-border py-2">
                Direction
              </th>
            </tr>
          </thead>
          <tbody>
            {result.top_contributing_factors.map((f) => (
              <tr key={f.feature} className="border-b border-border last:border-0">
                <th scope="row" className="py-2 pr-3 font-normal">
                  {label(f.feature)}
                </th>
                <td className="py-2 pr-3 tabular-nums">{shortNumber(f.impact)}</td>
                <td className="py-2">{f.direction}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {result.range_warnings.length > 0 && (
        <div className="flex gap-2 rounded-md border border-caution p-3">
          <AlertTriangle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-caution" />
          <div>
            <p className="font-semibold">{messageText(messages, 'warn_outside_training_range')}</p>
            <p>{result.range_warnings.map(label).join(', ')}</p>
          </div>
        </div>
      )}
      {result.hba1c_note && (
        <p className="flex gap-2">
          <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
          {messageText(messages, 'note_hba1c_haemoglobin_variant')}
        </p>
      )}
      <section aria-label="Model limitations" className="flex flex-col gap-1 text-sm">
        <h4 className="text-base">Limitations</h4>
        <ul className="list-disc pl-5">
          {limitationKeys.map((k) => (
            <li key={k}>{messageText(messages, k)}</li>
          ))}
        </ul>
      </section>
      <ShareSection
        result={result}
        messages={messages}
        onShared={() => void qc.invalidateQueries({ queryKey: ['predictions'] })}
      />
    </Card>
  )
}

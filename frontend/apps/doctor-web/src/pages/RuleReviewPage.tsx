import { userMessage, type RuleModule, type RuleRow } from '@alovia/shared'
import { Button, Card, CheckboxField, cn, ErrorState, PageSkeleton } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { useId, useState } from 'react'

import { config } from '../app/config'
import { formatDateTime } from '../app/patients'
import { api, authClient } from '../app/services'

const LABEL: Record<RuleModule['module'], string> = {
  genetic: 'Genetic risk',
  symptom: 'Symptom tracking',
  journey: 'Pregnancy journey',
}

/** §19 Export: the Markdown file is downloaded; the owner saves it into docs (DEC-080). */
async function downloadExport(module: string): Promise<void> {
  const token = (await authClient.auth.getSession()).data.session?.access_token
  const res = await fetch(`${config.apiBaseUrl}/doctor/rules/${module}/export`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error('export failed')
  const url = URL.createObjectURL(await res.blob())
  const a = document.createElement('a')
  a.href = url
  a.download = `rule_review_signoff_${module}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function RowEditor({ module, row }: { module: string; row: RuleRow }) {
  const qc = useQueryClient()
  const id = useId()
  const [checked, setChecked] = useState(row.checked ?? false)
  const [comment, setComment] = useState(row.comment ?? '')
  const save = useMutation({
    mutationFn: () =>
      api.post<RuleRow>(`/doctor/rules/${module}/signoff`, {
        key: row.key,
        checked,
        comment: comment.trim() || null,
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['rules'] }),
  })
  return (
    <li>
      <Card className="flex flex-col gap-2">
        <p className="text-sm text-muted">
          {row.key} · {row.section}
        </p>
        <p className="font-semibold">{row.what_to_check}</p>
        <p className="whitespace-pre-line">{row.current_value}</p>
        <p className="text-sm text-muted">Source: {row.source}</p>
        <p className="text-sm">
          {row.checked === null
            ? 'Not signed yet'
            : `${row.checked ? 'Checked' : 'Not checked'} by ${row.doctor_name ?? 'a doctor'}${
                row.signed_at ? ` on ${formatDateTime(row.signed_at)}` : ''
              }`}
        </p>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <CheckboxField
            label="Checked"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
          <div className="flex flex-1 flex-col gap-1">
            <label htmlFor={id} className="text-sm font-semibold">
              Comment (optional)
            </label>
            <input
              id={id}
              value={comment}
              maxLength={2000}
              onChange={(e) => setComment(e.target.value)}
              className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
            />
          </div>
          <Button
            variant="secondary"
            loading={save.isPending}
            onClick={() => save.mutate()}
            aria-label={`Save sign-off for ${row.key}`}
          >
            Save
          </Button>
        </div>
        {save.isError && (
          <p role="alert" className="text-urgent">
            {userMessage(save.error, 'doctor')}
          </p>
        )}
      </Card>
    </li>
  )
}

/** Rule review (Dashboard §19, UX_FLOWS D9): every rule row with its source; any doctor
 * ticks "checked" and comments for the current rules version; Export downloads the
 * sign-off file. */
export function RuleReviewPage() {
  const rules = useQuery({
    queryKey: ['rules'],
    queryFn: () => api.get<RuleModule[]>('/doctor/rules'),
  })
  const [module, setModule] = useState<RuleModule['module']>('genetic')
  const [openOnly, setOpenOnly] = useState(false)
  const [exportError, setExportError] = useState(false)

  if (rules.isPending) return <PageSkeleton />
  if (rules.isError) {
    return (
      <ErrorState
        message={userMessage(rules.error, 'doctor')}
        onRetry={() => void rules.refetch()}
      />
    )
  }
  const current = rules.data.find((m) => m.module === module) ?? rules.data[0]
  if (!current) return null
  const rows = openOnly ? current.rows.filter((r) => !r.checked) : current.rows
  return (
    <section className="flex flex-col gap-4">
      <h1>Rule review</h1>
      <nav aria-label="Rule modules">
        <ul className="flex flex-wrap gap-2">
          {rules.data.map((m) => (
            <li key={m.module}>
              <button
                type="button"
                aria-pressed={m.module === current.module}
                onClick={() => setModule(m.module)}
                className={cn(
                  'min-h-11 rounded-md border px-3',
                  m.module === current.module
                    ? 'border-primary bg-primary-soft font-semibold text-primary'
                    : 'border-border',
                )}
              >
                {LABEL[m.module]} ({m.checked}/{m.total})
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p>
          Rules version <code>{current.rules_version}</code> · {current.checked} of {current.total}{' '}
          checked
        </p>
        <Button
          variant="secondary"
          onClick={() => {
            setExportError(false)
            downloadExport(current.module).catch(() => setExportError(true))
          }}
        >
          <Download aria-hidden="true" className="size-5" />
          Export sign-off
        </Button>
      </div>
      {exportError && (
        <p role="alert" className="text-urgent">
          The export could not be downloaded. Please try again.
        </p>
      )}
      <CheckboxField
        label="Show only rows not checked yet"
        checked={openOnly}
        onChange={(e) => setOpenOnly(e.target.checked)}
      />
      <ul className="flex flex-col gap-3">
        {rows.map((r) => (
          <RowEditor key={`${current.module}-${r.key}`} module={current.module} row={r} />
        ))}
      </ul>
      {rows.length === 0 && (
        <Card>
          <p>Every row is checked.</p>
        </Card>
      )}
    </section>
  )
}

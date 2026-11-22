import {
  ApiError,
  useAuth,
  userMessage,
  type CheckinResult,
  type EntryInput,
  type SymptomVocabulary,
} from '@alovia/shared'
import {
  Button,
  Card,
  CheckboxField,
  ChipRowSkeleton,
  ErrorState,
  FieldError,
  Sheet,
  TextAreaField,
  TextField,
} from '@alovia/ui'
import {
  BatteryLow,
  Bone,
  Brain,
  CircleDot,
  Heart,
  Plus,
  Smile,
  TriangleAlert,
  Utensils,
  UtensilsCrossed,
  Waves,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'

import { clearDraft, loadDraft, saveDraft } from '../app/logDraft'
import {
  adviceText,
  cannotReach,
  emptyDraft,
  entryError,
  missingFields,
  toEntry,
  type CommonDraft,
} from '../app/symptoms'
import { useSubmitCheckin, useVocabulary } from '../app/useSymptoms'
import { AdviceScreen, AfterEndNotice, NotMonitoredNotice } from '../components/symptoms/Advice'
import { ChipChoiceGroup, SymptomChip } from '../components/symptoms/Fields'

type Vocabulary = SymptomVocabulary

// Decorative chip icons for the everyday symptoms (Symptom spec §5.1 ids); unknown ids get none.
const ICONS: Record<string, LucideIcon> = {
  nausea_vomiting: Waves,
  fatigue: BatteryLow,
  headache: Brain,
  abdominal_discomfort: CircleDot,
  back_pain: Bone,
  breast_tenderness: Heart,
  food_craving: Utensils,
  appetite_change: UtensilsCrossed,
  mood_change: Smile,
  other: Plus,
}

/** Log symptoms (Symptom spec §4.1, UX_FLOWS P5) as a sheet (FRONTEND_REDESIGN §7.5): phone full
 * screen with an X and no bottom bar, laptop a right-hand panel. The address stays /log. */
export function LogPage() {
  const vocab = useVocabulary()
  const navigate = useNavigate()
  const location = useLocation()
  // back to where the patient came from; straight to Home when /log was opened directly
  const close = () => (location.key === 'default' ? navigate('/home') : navigate(-1))
  return (
    <Sheet open onClose={() => void close()} labelledBy="log-title">
      {vocab.isPending ? (
        <SheetFrame onClose={close}>
          <div role="status" aria-label="Loading" className="flex flex-col gap-4">
            <ChipRowSkeleton />
            <ChipRowSkeleton />
          </div>
        </SheetFrame>
      ) : vocab.isError ? (
        <SheetFrame onClose={close}>
          <ErrorState
            message={userMessage(vocab.error, 'patient')}
            onRetry={() => void vocab.refetch()}
          />
        </SheetFrame>
      ) : !vocab.data.logging_open ? (
        <SheetFrame onClose={close}>
          <AfterEndNotice />
        </SheetFrame>
      ) : (
        <LogForm v={vocab.data} onClose={close} />
      )}
    </Sheet>
  )
}

/** Fixed header (X, title, pregnancy week), scrolling body, optional sticky footer. */
function SheetFrame({
  onClose,
  week,
  footer,
  children,
}: {
  onClose: () => void
  week?: number | null
  footer?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-2 border-b border-border bg-surface px-2 pt-[max(0.5rem,env(safe-area-inset-top))] pb-2">
        <button
          type="button"
          aria-label="Close"
          onClick={onClose}
          className="flex size-11 shrink-0 items-center justify-center rounded-full text-text hover:bg-primary-soft"
        >
          <X aria-hidden="true" className="size-6" />
        </button>
        <h1 id="log-title" className="flex-1 text-xl">
          Log symptoms
        </h1>
        {week != null && <span className="pr-3 text-sm text-muted">Week {week}</span>}
      </header>
      <div className="flex flex-1 flex-col gap-6 overflow-y-auto p-4">{children}</div>
      {footer && (
        <div className="border-t border-border bg-surface px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          {footer}
        </div>
      )}
    </div>
  )
}

function LogForm({ v, onClose }: { v: Vocabulary; onClose: () => void }) {
  const { session } = useAuth()
  const userId = session?.user.id ?? ''
  const submit = useSubmitCheckin()
  const navigate = useNavigate()
  // DEC-109: restore unsaved choices from this device within draft_ttl_minutes
  const [restored] = useState(() => loadDraft(userId, v.draft_ttl_minutes))
  const [warning, setWarning] = useState<Record<string, boolean>>(restored?.warning ?? {})
  const [labourDuration, setLabourDuration] = useState(restored?.labourDuration)
  const [drafts, setDrafts] = useState<Record<string, CommonDraft>>(restored?.drafts ?? {})
  const [showRestored, setShowRestored] = useState(restored !== null)
  const [missing, setMissing] = useState<Record<string, string[]>>({})
  const [order, setOrder] = useState<string[]>([])
  const [puqeOpen, setPuqeOpen] = useState(false)
  const [result, setResult] = useState<CheckinResult | null>(null)

  const chosen = Object.values(warning).some(Boolean) || Object.keys(drafts).length > 0
  useEffect(() => {
    if (!userId || result) return
    if (chosen) saveDraft(userId, { warning, labourDuration, drafts })
    else clearDraft(userId)
  }, [userId, result, chosen, warning, labourDuration, drafts])

  if (result) {
    return (
      <SheetFrame onClose={() => navigate('/home')} week={result.pregnancy_week}>
        <AdviceScreen
          level={result.red_flag_level}
          messageKeys={result.message_keys}
          onDone={() => navigate('/home')}
        />
      </SheetFrame>
    )
  }

  const serverFields = submit.error instanceof ApiError ? (submit.error.fields ?? {}) : {}
  const fieldError = (id: string, field: string) =>
    missing[id]?.includes(field)
      ? 'Please fill this in.'
      : entryError(serverFields, order.indexOf(id), field)
  const otherError =
    submit.isError && Object.keys(serverFields).length === 0
      ? // DEC-109: online only; a failed save says so and keeps the draft
        cannotReach(submit.error)
        ? adviceText('msg_not_saved')
        : userMessage(submit.error, 'patient')
      : null
  const setDraft = (id: string, change: Partial<CommonDraft>) =>
    setDrafts((d) => ({ ...d, [id]: { ...(d[id] ?? emptyDraft()), ...change } }))
  const toggleCommon = (id: string, on: boolean) =>
    setDrafts((all) =>
      on
        ? { ...all, [id]: emptyDraft() }
        : Object.fromEntries(Object.entries(all).filter(([key]) => key !== id)),
    )
  const clearAll = () => {
    setWarning({})
    setLabourDuration(undefined)
    setDrafts({})
    setMissing({})
    setShowRestored(false)
  }

  function send(e: FormEvent) {
    e.preventDefault()
    if (!chosen) return // V1: Save stays disabled until a symptom is chosen
    const entries: EntryInput[] = []
    const ids: string[] = []
    const gaps: Record<string, string[]> = {}
    for (const w of v.warning) {
      if (!warning[w.id]) continue
      if (w.labour_duration && !labourDuration) gaps[w.id] = ['duration']
      entries.push({
        symptom: w.id,
        ...(w.labour_duration ? { duration: labourDuration } : {}),
      } as EntryInput)
      ids.push(w.id)
    }
    for (const c of v.common) {
      const d = drafts[c.id]
      if (!d) continue
      const gap = missingFields(c, d)
      if (gap.length) gaps[c.id] = gap
      entries.push(toEntry(c, d))
      ids.push(c.id)
    }
    setMissing(gaps)
    setOrder(ids)
    if (Object.keys(gaps).length > 0) return
    submit.mutate(
      { source: 'form', entries },
      {
        onSuccess: (r) => {
          clearDraft(userId)
          setResult(r)
        },
      },
    )
  }

  const nausea = v.common.find((c) => c.puqe)
  const puqeDraft = nausea ? drafts[nausea.id] : undefined

  return (
    <form onSubmit={send} noValidate className="h-full">
      <SheetFrame
        onClose={onClose}
        week={v.pregnancy_week}
        footer={
          <Button
            type="submit"
            className="w-full"
            loading={submit.isPending}
            aria-disabled={!chosen || undefined}
          >
            Save check-in
          </Button>
        }
      >
        {showRestored && (
          <p role="status" className="flex items-center gap-2 text-sm text-muted">
            Draft restored ·
            <button type="button" onClick={clearAll} className="min-h-11 font-semibold underline">
              Clear
            </button>
          </p>
        )}
        <NotMonitoredNotice />
        <p className="text-sm">
          <Link className="tap" to="/log/history">
            Your symptom history
          </Link>
        </p>
        {otherError && <ErrorState message={otherError} />}

        <section
          aria-labelledby="warning-heading"
          className="flex flex-col gap-3 rounded-lg border border-urgent bg-urgent/10 p-4"
        >
          <h2 id="warning-heading" className="flex items-center gap-2 font-sans text-lg">
            <TriangleAlert aria-hidden="true" className="size-5 shrink-0 text-urgent" />
            Warning signs
          </h2>
          <div className="flex flex-wrap gap-2">
            {v.warning.map((w) => (
              <SymptomChip
                key={w.id}
                label={w.label}
                checked={!!warning[w.id]}
                onChange={(on) => setWarning((s) => ({ ...s, [w.id]: on }))}
              />
            ))}
          </div>
          {v.warning.some((w) => w.labour_duration && warning[w.id]) && (
            <ChipChoiceGroup
              legend="Duration"
              options={v.labour_durations}
              value={labourDuration}
              onChange={setLabourDuration}
              error={fieldError(
                v.warning.find((w) => w.labour_duration)?.id ?? 'labour_pains',
                'duration',
              )}
            />
          )}
        </section>

        <section aria-labelledby="everyday-heading" className="flex flex-col gap-3">
          <h2 id="everyday-heading" className="text-lg">
            Everyday symptoms
          </h2>
          <div className="flex flex-wrap gap-2">
            {v.common.map((c) => (
              <SymptomChip
                key={c.id}
                label={c.label}
                Icon={ICONS[c.id]}
                checked={!!drafts[c.id]}
                onChange={(on) => {
                  toggleCommon(c.id, on)
                  if (on && c.puqe) setPuqeOpen(true)
                }}
              />
            ))}
          </div>
          {v.common.map((c) => {
            const d = drafts[c.id]
            if (!d) return null
            return (
              <Card key={c.id} className="flex flex-col gap-3">
                <h3 className="text-base">{c.label}</h3>
                {c.text && (
                  <TextField
                    label={c.text.required ? c.text.label : `${c.text.label} (optional)`}
                    value={d.text ?? ''}
                    maxLength={c.text.max_length}
                    onChange={(e) => setDraft(c.id, { text: e.target.value })}
                    error={fieldError(c.id, c.text.field)}
                  />
                )}
                {c.choice && (
                  <ChipChoiceGroup
                    legend={c.label}
                    options={c.choice.options}
                    value={d.choice}
                    onChange={(choice) => setDraft(c.id, { choice })}
                    error={fieldError(c.id, c.choice.field)}
                  />
                )}
                {c.severity && (
                  <ChipChoiceGroup
                    legend="Severity"
                    options={v.severities}
                    value={d.severity}
                    onChange={(severity) => setDraft(c.id, { severity })}
                    error={fieldError(c.id, 'severity')}
                  />
                )}
                {c.duration && (
                  <ChipChoiceGroup
                    legend="Duration"
                    options={v.durations}
                    value={d.duration}
                    onChange={(duration) => setDraft(c.id, { duration })}
                    error={fieldError(c.id, 'duration')}
                  />
                )}
                {c.body_area && (
                  <ChipChoiceGroup
                    legend={c.body_area.required ? 'Body area' : 'Body area (optional)'}
                    options={c.body_area.choices.map((a): [string, string] => [
                      a,
                      v.body_areas[a] ?? a,
                    ])}
                    value={d.body_area}
                    onChange={(body_area) => setDraft(c.id, { body_area })}
                    error={fieldError(c.id, 'body_area')}
                  />
                )}
                {c.puqe && (
                  <div className="flex flex-col gap-2">
                    <p>{puqeSummary(v, d)}</p>
                    <Button
                      type="button"
                      variant="secondary"
                      className="self-start"
                      onClick={() => setPuqeOpen(true)}
                    >
                      {d.puqe.some((a) => a === undefined)
                        ? 'Answer the questions'
                        : 'Change answers'}
                    </Button>
                    <FieldError
                      id={`${c.id}-puqe-error`}
                      message={fieldError(c.id, 'puqe_answers')}
                    />
                  </div>
                )}
                {Object.entries(c.flags).map(([flag, label]) => (
                  <CheckboxField
                    key={flag}
                    label={label}
                    checked={!!d.flags[flag]}
                    onChange={(e) =>
                      setDraft(c.id, { flags: { ...d.flags, [flag]: e.target.checked } })
                    }
                  />
                ))}
                <TextField
                  label="Time (optional)"
                  type="time"
                  value={d.occurred_at ?? ''}
                  onChange={(e) => setDraft(c.id, { occurred_at: e.target.value })}
                />
                <TextAreaField
                  label="Notes (optional)"
                  value={d.notes ?? ''}
                  maxLength={500}
                  onChange={(e) => setDraft(c.id, { notes: e.target.value })}
                />
              </Card>
            )
          })}
        </section>
      </SheetFrame>
      {nausea && puqeDraft && (
        <PuqeSheet
          v={v}
          open={puqeOpen}
          title={nausea.label}
          answers={puqeDraft.puqe}
          onChange={(puqe) => setDraft(nausea.id, { puqe })}
          onClose={() => setPuqeOpen(false)}
        />
      )}
    </form>
  )
}

/** PUQE-24 total and its band (§8); bands come from the server. Null until all three are in. */
function puqeScore(v: Vocabulary, answers: (number | undefined)[]) {
  if (answers.length < 3 || answers.some((a) => a === undefined)) return null
  const score = answers.reduce<number>((sum, a) => sum + (a ?? 0), 0)
  const band = v.puqe_bands.find((b) => b.min <= score && score <= b.max)?.band
  return { score, band: band ? (v.severities[band] ?? band) : undefined }
}

function puqeSummary(v: Vocabulary, d: CommonDraft) {
  const s = puqeScore(v, d.puqe)
  if (!s) return `${d.puqe.filter((a) => a !== undefined).length} of 3 questions answered`
  return `Score ${s.score} of 15${s.band ? ` (${s.band})` : ''}`
}

/** The PUQE questions in their own sheet with a live score band (FRONTEND_REDESIGN §7.5). */
function PuqeSheet({
  v,
  open,
  title,
  answers,
  onChange,
  onClose,
}: {
  v: Vocabulary
  open: boolean
  title: string
  answers: (number | undefined)[]
  onChange: (answers: (number | undefined)[]) => void
  onClose: () => void
}) {
  return (
    <Sheet open={open} onClose={onClose} labelledBy="puqe-title">
      <div className="flex h-full flex-col">
        <header className="flex items-center gap-2 border-b border-border bg-surface px-4 pt-[max(0.75rem,env(safe-area-inset-top))] pb-3">
          <h2 id="puqe-title" className="flex-1 font-sans text-xl">
            {title}
          </h2>
        </header>
        <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-4">
          {v.puqe_questions.map((q, i) => (
            <ChipChoiceGroup
              key={q.id}
              legend={q.text}
              options={Object.entries(q.answers).sort(([a], [b]) => +a - +b)}
              value={answers[i]?.toString()}
              onChange={(score) => {
                const next = [...answers]
                next[i] = Number(score)
                onChange(next)
              }}
            />
          ))}
          <p className="text-sm text-muted">
            Questions: {v.puqe_source.title} ({v.puqe_source.publisher})
          </p>
        </div>
        <div className="flex items-center gap-3 border-t border-border bg-surface px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
          <p role="status" className="flex-1 font-semibold tabular-nums">
            {puqeSummary(v, { flags: {}, puqe: answers })}
          </p>
          <Button type="button" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </Sheet>
  )
}

import { ApiError, userMessage, type GeneticAssessment, type GeneticInput } from '@alovia/shared'
import { Button, Card, ErrorState, FieldError } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useId, useState, type FormEvent } from 'react'
import { Link } from 'react-router'

import {
  CONDITIONS,
  emptyGeneticDraft,
  evidenceFor,
  missingAnswers,
  questionFor,
  sectionShown,
  toGeneticInput,
  type ConditionKey,
  type GeneticDraft,
  type ParentDraft,
} from '../../app/genetic'
import { GENETIC_BUNDLE } from '../../app/geneticBundle.generated'
import { HOME_KEY } from '../../app/useJourneyHome'
import { api } from '../../app/services'
import { ChoiceGroup } from '../symptoms/Fields'

/** A native select with its label and error (DESIGN_SYSTEM §9). */
function SelectField({
  label,
  value,
  options,
  onChange,
  error,
}: {
  label: string
  value: string | undefined
  options: [string, string][]
  onChange: (value: string) => void
  error?: string
}) {
  const id = useId()
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="font-semibold">
        {label}
      </label>
      <select
        id={id}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className="min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text"
      >
        <option value="">Choose…</option>
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
      <FieldError id={`${id}-error`} message={error} />
    </div>
  )
}

/** The genetic check form (Genetic spec §4.1, UX_FLOWS P9): consent reminder, haemoglobin
 * section (always), haemophilia and Marfan behind their entry questions, consanguinity. */
export function GeneticForm({ onDone }: { onDone: (result: GeneticAssessment) => void }) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState<GeneticDraft>(emptyGeneticDraft)
  const [missing, setMissing] = useState<string[]>([])
  const submit = useMutation({
    mutationFn: (body: GeneticInput) =>
      api.post<GeneticAssessment>('/patient/genetic/assessments', body),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['genetic-assessments'] })
      void queryClient.invalidateQueries({ queryKey: HOME_KEY }) // the "Genetic check" card
      onDone(result)
    },
  })
  const server = submit.error instanceof ApiError ? (submit.error.fields ?? {}) : {}
  const errorFor = (path: string) =>
    missing.includes(path) || server[path] === 'E1'
      ? 'Please answer this.'
      : server[path]
        ? 'Please check this answer.'
        : undefined
  const otherError =
    submit.isError && Object.keys(server).length === 0 ? userMessage(submit.error, 'patient') : null

  const setSection = (c: ConditionKey, change: Partial<GeneticDraft[ConditionKey]>) =>
    setDraft((d) => ({ ...d, [c]: { ...d[c], ...change } }))
  const setParent = (c: ConditionKey, who: 'mother' | 'father', change: ParentDraft) =>
    setDraft((d) => ({ ...d, [c]: { ...d[c], [who]: change } }))

  function send(e: FormEvent) {
    e.preventDefault()
    const gaps = missingAnswers(draft)
    setMissing(gaps)
    if (gaps.length === 0) submit.mutate(toGeneticInput(draft))
  }

  return (
    <form onSubmit={send} noValidate className="flex flex-col gap-6">
      <Card className="flex flex-col gap-1">
        {/* DEC-072: consent reminder (COMPLIANCE_CHECKLIST item 6) */}
        <p>
          This form also asks about your husband. Your answers about him are covered by the consent
          you accepted.
        </p>
        <p className="text-sm">
          <Link to="/consent">Read the consent text</Link>
        </p>
      </Card>
      {otherError && <ErrorState message={otherError} />}
      {CONDITIONS.map((c) => {
        const s = draft[c]
        return (
          <section key={c} aria-labelledby={`${c}-heading`} className="flex flex-col gap-3">
            <h2 id={`${c}-heading`}>{GENETIC_BUNDLE.conditions[c]}</h2>
            <Card className="flex flex-col gap-4">
              {c !== 'haemoglobin_group' && (
                <ChoiceGroup
                  legend={questionFor(GENETIC_BUNDLE.entryQuestion, c)}
                  options={GENETIC_BUNDLE.entryAnswers}
                  value={s.entry}
                  onChange={(entry) => setSection(c, { entry })}
                  error={errorFor(`${c}.entry`)}
                />
              )}
              {sectionShown(c, s) && (
                <>
                  {(['mother', 'father'] as const).map((who) => {
                    const p = s[who]
                    const evidence = evidenceFor(c, p.status)
                    return (
                      <fieldset key={who} className="flex flex-col gap-3">
                        <legend className="mb-1 font-semibold">
                          {who === 'mother' ? 'You (the mother)' : 'Your husband (the father)'}
                        </legend>
                        <SelectField
                          label="Status"
                          value={p.status}
                          options={Object.entries(GENETIC_BUNDLE.statuses[c][who])}
                          onChange={(status) => setParent(c, who, { status })}
                          error={errorFor(`${c}.${who}.status`)}
                        />
                        {evidence.length > 0 && (
                          <SelectField
                            label="How do you know?"
                            value={p.evidence}
                            options={evidence}
                            onChange={(ev) => setParent(c, who, { ...p, evidence: ev })}
                            error={errorFor(`${c}.${who}.evidence`)}
                          />
                        )}
                      </fieldset>
                    )
                  })}
                  <ChoiceGroup
                    legend={questionFor(GENETIC_BUNDLE.previousChildQuestion, c)}
                    options={GENETIC_BUNDLE.previousChildAnswers}
                    value={s.previous_child}
                    onChange={(previous_child) => setSection(c, { previous_child })}
                    error={errorFor(`${c}.previous_child`)}
                  />
                </>
              )}
            </Card>
          </section>
        )
      })}
      <Card>
        <ChoiceGroup
          legend={GENETIC_BUNDLE.consanguinityQuestion}
          options={GENETIC_BUNDLE.consanguinityAnswers}
          value={draft.consanguinity}
          onChange={(consanguinity) => setDraft((d) => ({ ...d, consanguinity }))}
          error={errorFor('consanguinity')}
        />
      </Card>
      {missing.length > 0 && (
        <FieldError id="genetic-missing" message="Please answer the questions marked above." />
      )}
      <Button type="submit" className="self-start" loading={submit.isPending}>
        Submit
      </Button>
    </form>
  )
}

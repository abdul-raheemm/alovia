import { FieldError } from '@alovia/ui'
import { useId } from 'react'

/** A radio group with a visible legend and its error below (DESIGN_SYSTEM §9). */
export function ChoiceGroup({
  legend,
  options,
  value,
  onChange,
  error,
}: {
  legend: string
  options: Record<string, string> | [string, string][]
  value: string | undefined
  onChange: (value: string) => void
  error?: string
}) {
  const name = useId()
  const errorId = `${name}-error`
  const entries = Array.isArray(options) ? options : Object.entries(options)
  return (
    <fieldset className="flex flex-col gap-1" aria-describedby={error ? errorId : undefined}>
      <legend className="mb-1 font-semibold">{legend}</legend>
      <div className="flex flex-wrap gap-x-4">
        {entries.map(([id, label]) => (
          <label key={id} className="flex min-h-11 items-center gap-2">
            <input
              type="radio"
              name={name}
              value={id}
              checked={value === id}
              onChange={() => onChange(id)}
              className="size-5 accent-[var(--color-primary)]"
            />
            {label}
          </label>
        ))}
      </div>
      <FieldError id={errorId} message={error} />
    </fieldset>
  )
}

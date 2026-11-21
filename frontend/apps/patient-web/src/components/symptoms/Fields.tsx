import { cn, FieldError } from '@alovia/ui'
import { Check, type LucideIcon } from 'lucide-react'
import { useId, type ReactNode } from 'react'

// FRONTEND_REDESIGN §7.5 chip: at least 44 px, soft wash when off; primary fill, on-primary text
// and a check icon when on; slight press. A real checkbox or radio inside, so keyboard and
// screen readers work as for any form field.
const CHIP =
  'relative inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-full border px-4 select-none ' +
  'transition-transform duration-[var(--duration-fast)] ease-[var(--ease-out-strong)] active:scale-[0.97] motion-reduce:transition-none motion-reduce:active:scale-100 ' +
  'has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-primary'
// the real input covers the whole chip (invisible), so a tap anywhere on the chip hits it
const CHIP_INPUT =
  'absolute inset-0 m-0 size-full cursor-pointer appearance-none rounded-full opacity-0'
const CHIP_OFF = 'border-border bg-primary-soft text-text'
const CHIP_ON = 'border-primary bg-primary font-semibold text-on-primary'

function ChipFace({ on, Icon, children }: { on: boolean; Icon?: LucideIcon; children: ReactNode }) {
  const Shown = on ? Check : Icon
  return (
    <>
      {Shown && <Shown aria-hidden="true" className="size-5 shrink-0" />}
      {children}
    </>
  )
}

/** One symptom chip (a styled checkbox). */
export function SymptomChip({
  label,
  checked,
  onChange,
  Icon,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  Icon?: LucideIcon
}) {
  return (
    <label className={cn(CHIP, checked ? CHIP_ON : CHIP_OFF)}>
      <input
        type="checkbox"
        className={CHIP_INPUT}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
      />
      <ChipFace on={checked} Icon={Icon}>
        {label}
      </ChipFace>
    </label>
  )
}

/** A single choice shown as chips (a styled radio group), legend visible, error below. */
export function ChipChoiceGroup({
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
      <div className="flex flex-wrap gap-2">
        {entries.map(([id, label]) => (
          <label key={id} className={cn(CHIP, value === id ? CHIP_ON : CHIP_OFF)}>
            <input
              type="radio"
              name={name}
              value={id}
              checked={value === id}
              onChange={() => onChange(id)}
              className={CHIP_INPUT}
            />
            <ChipFace on={value === id}>{label}</ChipFace>
          </label>
        ))}
      </div>
      <FieldError id={errorId} message={error} />
    </fieldset>
  )
}

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

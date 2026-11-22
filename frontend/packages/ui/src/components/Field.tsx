import { AlertCircle } from 'lucide-react'
import { useId, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from 'react'

import { cn } from '../cn'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

/** Text input with its label always visible above it and the error below (DESIGN_SYSTEM §9). */
export function TextField({ label, error, className, id, ...props }: FieldProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const errorId = `${inputId}-error`
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="font-semibold">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'min-h-11 rounded-sm border border-border bg-surface px-3 text-base text-text',
          error && 'border-urgent',
          className,
        )}
        {...props}
      />
      <FieldError id={errorId} message={error} />
    </div>
  )
}

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string
  error?: string
}

/** Multi-line text with the same label/error layout as TextField. */
export function TextAreaField({ label, error, className, id, ...props }: TextAreaProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const errorId = `${inputId}-error`
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="font-semibold">
        {label}
      </label>
      <textarea
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'min-h-24 rounded-sm border border-border bg-surface px-3 py-2 text-base text-text',
          error && 'border-urgent',
          className,
        )}
        {...props}
      />
      <FieldError id={errorId} message={error} />
    </div>
  )
}

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: ReactNode
  error?: string
}

/** Native checkbox with a 44px touch area and its label beside it. */
export function CheckboxField({ label, error, id, ...props }: CheckboxProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const errorId = `${inputId}-error`
  return (
    <div className="flex flex-col gap-1">
      <div className="flex min-h-11 items-start gap-3">
        <input
          id={inputId}
          type="checkbox"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className="mt-3 size-5 shrink-0 accent-[var(--color-primary)]"
          {...props}
        />
        <label htmlFor={inputId} className="min-h-11 py-2.5">
          {label}
        </label>
      </div>
      <FieldError id={errorId} message={error} />
    </div>
  )
}

export function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null
  return (
    <p id={id} className="flex items-center gap-1 text-sm text-urgent">
      <AlertCircle aria-hidden="true" className="size-4 shrink-0" />
      {message}
    </p>
  )
}

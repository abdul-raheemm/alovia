import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes } from 'react'

import { cn } from '../cn'

// DESIGN_SYSTEM.md §8: 44px touch target, medium radius, clear verb labels
const buttonVariants = cva(
  'inline-flex min-h-11 items-center justify-center gap-2 rounded-md px-4 text-base font-semibold no-underline transition-[color,background-color,transform] duration-[var(--duration-fast)] ease-[var(--ease-out-strong)] active:scale-[0.97] disabled:active:scale-100 aria-disabled:active:scale-100 motion-reduce:active:scale-100 disabled:cursor-not-allowed disabled:opacity-40 aria-disabled:cursor-not-allowed aria-disabled:opacity-40',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-on-primary hover:opacity-90',
        secondary: 'border border-primary bg-surface text-primary hover:bg-primary-soft',
        danger: 'bg-urgent text-white hover:opacity-90 dark:text-bg',
        ghost: 'bg-transparent text-text hover:bg-primary-soft',
      },
    },
    defaultVariants: { variant: 'primary' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  /** Render the child element (e.g. a link) with button styles. */
  asChild?: boolean
  /** Keeps the label, shows a spinner and disables the button. */
  loading?: boolean
}

export function Button({
  className,
  variant,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return (
    <Comp
      className={cn(buttonVariants({ variant }), className)}
      disabled={asChild ? undefined : disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {/* Slot needs exactly one child, so the spinner is only for real buttons */}
      {asChild ? (
        children
      ) : (
        <>
          {loading && <Loader2 aria-hidden="true" className="size-5 animate-spin" />}
          {children}
        </>
      )}
    </Comp>
  )
}

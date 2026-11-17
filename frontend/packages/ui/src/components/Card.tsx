import type { HTMLAttributes } from 'react'

import { cn } from '../cn'

/** Surface card (DESIGN_SYSTEM §10): shadow in light mode, border in dark mode. */
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg border border-transparent bg-surface p-5 shadow-sm dark:border-border',
        className,
      )}
      {...props}
    />
  )
}

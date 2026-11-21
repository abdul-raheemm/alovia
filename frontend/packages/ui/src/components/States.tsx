import { AlertTriangle, Construction } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from './Button'
import { Card } from './Card'
import { CardSkeleton, Skeleton } from './Skeleton'

/** Loading skeleton in the rough shape of a page (UX_FLOWS §0). */
export function PageSkeleton() {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-4 p-4">
      <Skeleton className="h-8 w-1/2 rounded-sm" />
      <CardSkeleton />
      <CardSkeleton />
    </div>
  )
}

/** Error state: plain message, Retry, no technical detail (UX_FLOWS §0, ERROR_HANDLING §1). */
export function ErrorState({
  message,
  onRetry,
  children,
}: {
  message: string
  onRetry?: () => void
  children?: ReactNode
}) {
  return (
    <Card role="alert" className="flex flex-col items-start gap-3">
      <p className="flex items-center gap-2 font-semibold text-urgent">
        <AlertTriangle aria-hidden="true" className="size-5 shrink-0" />
        {message}
      </p>
      {children}
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      )}
    </Card>
  )
}

/** Placeholder for a screen that a later phase builds. Neutral wording only. */
export function PlaceholderPage({ title }: { title: string }) {
  return (
    <section className="flex flex-col gap-4">
      <h1>{title}</h1>
      <Card className="flex items-center gap-3">
        <Construction aria-hidden="true" className="size-6 shrink-0 text-muted" />
        <p className="text-muted">This section is being built.</p>
      </Card>
    </section>
  )
}

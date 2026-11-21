import { cn } from '../cn'

/** One loading shape. Decorative: the wrapping region carries role="status" and the label.
 * The pulse runs only when the user allows motion (FRONTEND_REDESIGN §11 rule 4). */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      data-skeleton=""
      className={cn('rounded-md bg-primary-soft motion-safe:animate-pulse', className)}
    />
  )
}

/** Skeleton set (FRONTEND_REDESIGN §9): ring, card, chip row, calendar month, table row. */
export function RingSkeleton() {
  return <Skeleton className="mx-auto aspect-square w-full max-w-80 rounded-full" />
}

export function CardSkeleton() {
  return <Skeleton className="h-24 rounded-lg" />
}

export function ChipRowSkeleton() {
  return (
    <div className="flex flex-wrap gap-2">
      {['w-24', 'w-32', 'w-20', 'w-28'].map((w) => (
        <Skeleton key={w} className={cn('h-11 rounded-full', w)} />
      ))}
    </div>
  )
}

export function CalendarMonthSkeleton() {
  return (
    <div className="grid grid-cols-7 gap-1">
      {Array.from({ length: 35 }, (_, i) => (
        <Skeleton key={i} className="aspect-square rounded-sm" />
      ))}
    </div>
  )
}

export function TableRowSkeleton() {
  return <Skeleton className="h-11 rounded-sm" />
}

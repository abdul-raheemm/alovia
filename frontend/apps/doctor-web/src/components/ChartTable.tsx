import { Button } from '@alovia/ui'
import { useState, type ReactNode } from 'react'

/** "View as table" for a chart (FRONTEND_REDESIGN §8.4): the table is always there for screen
 * readers; the switch shows it to everyone and hides the drawing. */
export function useTableView(): [boolean, ReactNode] {
  const [asTable, setAsTable] = useState(false)
  const toggle = (
    <Button
      type="button"
      variant="ghost"
      aria-pressed={asTable}
      onClick={() => setAsTable(!asTable)}
      className="text-sm"
    >
      {asTable ? 'View as chart' : 'View as table'}
    </Button>
  )
  return [asTable, toggle]
}

export function tableClass(visible: boolean): string {
  return visible
    ? 'w-full text-left text-sm tabular-nums [&_caption]:sr-only [&_td]:border-t [&_td]:border-border [&_td]:px-2 [&_td]:py-1.5 [&_th]:border-t [&_th]:border-border [&_th]:px-2 [&_th]:py-1.5'
    : 'sr-only'
}

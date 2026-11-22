import { cn } from '../cn'
import { useEffect, useRef, type ReactNode } from 'react'

/** A modal sheet on the native <dialog> (owner choice 2026-11-21: no new dependency). The browser
 * keeps focus inside, makes the page behind inert and closes on Esc. Phone: full screen;
 * laptop: a panel on the right, about 480 px (FRONTEND_REDESIGN §7.5). */
export function Sheet({
  open,
  onClose,
  labelledBy,
  from = 'side',
  className,
  children,
}: {
  open: boolean
  onClose: () => void
  labelledBy: string
  /** the edge it slides in from: 'side' = bottom on phones, right on laptops */
  from?: 'side' | 'bottom' | 'left'
  className?: string
  children: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      aria-labelledby={labelledBy}
      data-sheet={from}
      // Esc: let the owner of the sheet decide (it may keep a draft or go back)
      onCancel={(e) => {
        e.preventDefault()
        onClose()
      }}
      className={cn(
        'm-0 h-dvh max-h-none w-full max-w-none border-0 bg-bg p-0 text-text backdrop:bg-black/40 lg:ml-auto lg:w-[480px] lg:border-l lg:border-border',
        className,
      )}
    >
      {open && children}
    </dialog>
  )
}

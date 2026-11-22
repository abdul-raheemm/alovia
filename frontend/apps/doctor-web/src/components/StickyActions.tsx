import type { ReactNode } from 'react'

/** A form's main button: on phones it sits in a bar stuck to the bottom of the screen while the
 * form is in view (FRONTEND_REDESIGN §8.5); elsewhere it stays where it is. */
export function StickyActions({ children }: { children: ReactNode }) {
  return (
    <div
      data-sticky-actions=""
      className="max-md:sticky max-md:bottom-0 max-md:z-10 max-md:-mx-4 max-md:border-t max-md:border-border max-md:bg-surface max-md:px-4 max-md:pt-3 max-md:pb-[max(0.75rem,env(safe-area-inset-bottom))] max-md:[&>button]:w-full"
    >
      {children}
    </div>
  )
}

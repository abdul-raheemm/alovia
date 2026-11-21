import { useSyncExternalStore } from 'react'

/** True while the media query matches (e.g. the 1024 px laptop layout, DESIGN_SYSTEM §15). */
export function useMediaQuery(query: string): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const list = window.matchMedia(query)
      list.addEventListener('change', onChange)
      return () => list.removeEventListener('change', onChange)
    },
    () => window.matchMedia(query).matches,
    () => false,
  )
}

import { cn, Logo } from '@alovia/ui'
import { Outlet, useLocation } from 'react-router'

import { useJourneyHome } from '../app/useJourneyHome'
import { BottomNav, SideNav } from './PatientNav'
import { UrgentButton } from './UrgentButton'

// until the items arrive (or if they cannot be loaded), keep the two that always exist; the bar
// stays usable while pages load (FRONTEND_REDESIGN §11 rule 13)
const FALLBACK_NAV = [
  { key: 'home', label: 'Home' },
  { key: 'more', label: 'More' },
]

/** Signed-in patient layout: bottom bar on phones, side bar on laptops, urgent button pinned
 * top-right on every screen. The notification bar is on the home screen (Journey §4.2). */
export function PatientShell() {
  const home = useJourneyHome()
  const items = home.data?.nav_items ?? FALLBACK_NAV
  // FRONTEND_REDESIGN §6: redesigned pages get the 1200 px desktop layout; the others keep
  // their reading width until their own redesign step
  const wide = useLocation().pathname === '/home'
  return (
    <div className="min-h-dvh lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">
        Skip to content
      </a>
      <SideNav items={items} />
      <div className="min-w-0 flex-1 pb-[calc(6rem+env(safe-area-inset-bottom))] lg:pb-0">
        <header className="flex items-center justify-between border-b border-border bg-surface px-4 pt-[max(0.75rem,env(safe-area-inset-top))] pb-3">
          <span className="lg:invisible">
            <Logo />
          </span>
          <UrgentButton />
        </header>
        <main id="main" className={cn('mx-auto p-4', wide ? 'max-w-[1200px] lg:p-6' : 'max-w-3xl')}>
          <Outlet />
        </main>
      </div>
      <BottomNav items={items} />
    </div>
  )
}

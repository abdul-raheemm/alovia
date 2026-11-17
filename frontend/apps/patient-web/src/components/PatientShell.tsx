import { cn, Logo } from '@alovia/ui'
import {
  CalendarClock,
  CalendarDays,
  Home,
  Menu,
  NotebookPen,
  PenLine,
  Siren,
  type LucideIcon,
} from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router'

import { useJourneyHome } from '../app/useJourneyHome'

// Where each nav key from rules/journey/config.yaml leads (Journey spec §4.1, DEC-040).
// The items and their labels come from the backend; a key missing here is not shown.
const NAV_ROUTES: Record<string, { to: string; Icon: LucideIcon }> = {
  home: { to: '/home', Icon: Home },
  calendar: { to: '/calendar', Icon: CalendarDays },
  log_symptoms: { to: '/log', Icon: PenLine },
  appointments: { to: '/appointments', Icon: CalendarClock },
  doctor_notes: { to: '/doctor-notes', Icon: NotebookPen },
  more: { to: '/more', Icon: Menu },
}
// until the items arrive (or if they cannot be loaded), keep the two that always exist
const FALLBACK_NAV = [
  { key: 'home', label: 'Home' },
  { key: 'more', label: 'More' },
]

/** Signed-in patient layout: bottom nav on phones, side bar on laptops, urgent button pinned
 * top-right on every screen. The notification bar is on the home screen (Journey §4.2). */
export function PatientShell() {
  const home = useJourneyHome()
  const items = (home.data?.nav_items ?? FALLBACK_NAV).filter((item) => item.key in NAV_ROUTES)
  return (
    <div className="min-h-dvh lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">
        Skip to content
      </a>
      <nav
        aria-label="Main"
        className="fixed inset-x-0 bottom-0 z-10 border-t border-border bg-surface lg:static lg:w-60 lg:border-t-0 lg:border-r"
      >
        <div className="hidden p-4 lg:block">
          <Logo />
        </div>
        <ul className="flex justify-around lg:flex-col lg:gap-1 lg:px-2">
          {items.map(({ key, label }) => {
            const { to, Icon } = NAV_ROUTES[key] as { to: string; Icon: LucideIcon }
            return (
              <li key={key} className="min-w-0 flex-1 lg:flex-none">
                <NavLink
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      'flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-md px-0.5 text-center text-[11px] leading-tight no-underline lg:min-h-11 lg:flex-row lg:justify-start lg:gap-3 lg:px-3 lg:text-left lg:text-base',
                      isActive ? 'font-bold text-primary' : 'text-muted',
                    )
                  }
                >
                  <Icon aria-hidden="true" className="size-6 shrink-0" />
                  {label}
                </NavLink>
              </li>
            )
          })}
        </ul>
      </nav>
      <div className="flex-1 pb-24 lg:pb-0">
        <header className="flex items-center justify-between border-b border-border bg-surface px-4 py-3">
          <span className="lg:invisible">
            <Logo />
          </span>
          <Link
            to="/urgent"
            className="inline-flex min-h-11 items-center gap-2 rounded-full bg-urgent px-4 font-bold text-white no-underline dark:text-bg"
          >
            <Siren aria-hidden="true" className="size-5" />
            Urgent
          </Link>
        </header>
        <main id="main" className="mx-auto max-w-3xl p-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

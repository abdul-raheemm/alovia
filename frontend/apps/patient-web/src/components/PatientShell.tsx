import { cn, Logo } from '@alovia/ui'
import { CalendarDays, CalendarClock, Home, Menu, PenLine, Siren } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router'

// DESIGN_SYSTEM §11: Home, Calendar, Log, Appointments, More
const NAV = [
  { to: '/home', label: 'Home', Icon: Home },
  { to: '/calendar', label: 'Calendar', Icon: CalendarDays },
  { to: '/log', label: 'Log', Icon: PenLine },
  { to: '/appointments', label: 'Appointments', Icon: CalendarClock },
  { to: '/more', label: 'More', Icon: Menu },
]

/** Signed-in patient layout: bottom nav on phones, side bar on laptops, urgent button pinned
 * top-right on every screen. TODO(Phase 2): notification bar under the header. */
export function PatientShell() {
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
          {NAV.map(({ to, label, Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  cn(
                    'flex min-h-14 min-w-14 flex-col items-center justify-center gap-0.5 rounded-md px-2 text-xs no-underline lg:min-h-11 lg:flex-row lg:justify-start lg:gap-3 lg:px-3 lg:text-base',
                    isActive ? 'font-bold text-primary' : 'text-muted',
                  )
                }
              >
                <Icon aria-hidden="true" className="size-6" />
                {label}
              </NavLink>
            </li>
          ))}
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

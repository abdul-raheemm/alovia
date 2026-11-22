import { cn, Logo } from '@alovia/ui'
import { CalendarClock, CalendarDays, Home, Menu, PenLine, type LucideIcon } from 'lucide-react'
import { Link, NavLink } from 'react-router'

// Where each nav key from rules/journey/config.yaml leads (Journey spec §4.1, DEC-040, DEC-112).
// The items and their labels come from the backend; a key missing here is not shown.
const NAV_ROUTES: Record<string, { to: string; Icon: LucideIcon }> = {
  home: { to: '/home', Icon: Home },
  calendar: { to: '/calendar', Icon: CalendarDays },
  log_symptoms: { to: '/log', Icon: PenLine },
  appointments: { to: '/appointments', Icon: CalendarClock },
  more: { to: '/more', Icon: Menu },
}
const LOG_KEY = 'log_symptoms'

export type NavItem = { key: string; label: string }

function routed(items: NavItem[]) {
  return items.flatMap((item) => {
    const route = NAV_ROUTES[item.key]
    return route ? [{ ...item, ...route }] : []
  })
}

/** Phone bottom bar (FRONTEND_REDESIGN §7.4): 64 px plus the safe-area inset, labels always
 * shown, the current tab on a soft pill, Log as the raised filled centre action. */
export function BottomNav({ items }: { items: NavItem[] }) {
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-10 border-t border-border bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden"
    >
      <ul className="flex h-16 items-stretch">
        {routed(items).map(({ key, label, to, Icon }) => (
          <li key={key} className="flex min-w-0 flex-1 justify-center">
            {key === LOG_KEY ? (
              <NavLink
                to={to}
                className={({ isActive }) =>
                  cn(
                    'flex min-w-0 flex-col items-center text-sm leading-tight no-underline',
                    isActive ? 'font-bold text-primary' : 'text-muted',
                  )
                }
              >
                {/* lifted 20 px so its label lines up with the other labels */}
                <span className="-mt-5 flex size-14 shrink-0 items-center justify-center rounded-full bg-primary text-on-primary shadow-md">
                  <Icon aria-hidden="true" className="size-6" />
                </span>
                <span className="max-w-full truncate">{label}</span>
              </NavLink>
            ) : (
              <NavLink
                to={to}
                viewTransition
                className={({ isActive }) =>
                  cn(
                    'my-1 flex min-h-11 min-w-0 max-w-full flex-col items-center justify-center gap-0.5 rounded-2xl px-2 text-sm leading-tight no-underline',
                    isActive ? 'bg-primary-soft font-bold text-primary' : 'text-muted',
                  )
                }
              >
                <Icon aria-hidden="true" className="size-6 shrink-0" />
                <span className="max-w-full truncate">{label}</span>
              </NavLink>
            )}
          </li>
        ))}
      </ul>
    </nav>
  )
}

/** Laptop side bar (1024 px and up): same items, Log as a primary button at the top. */
export function SideNav({ items }: { items: NavItem[] }) {
  const all = routed(items)
  const log = all.find((item) => item.key === LOG_KEY)
  return (
    <nav
      aria-label="Main"
      className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col gap-4 border-r border-border bg-surface p-3 lg:flex"
    >
      <div className="px-2 pt-1">
        <Logo />
      </div>
      {log && (
        <Link
          to={log.to}
          className="flex min-h-11 items-center justify-center gap-2 rounded-full bg-primary px-4 font-bold text-on-primary no-underline shadow-sm"
        >
          <log.Icon aria-hidden="true" className="size-5" />
          {log.label}
        </Link>
      )}
      <ul className="flex flex-col gap-1">
        {all
          .filter((item) => item.key !== LOG_KEY)
          .map(({ key, label, to, Icon }) => (
            <li key={key}>
              <NavLink
                to={to}
                viewTransition
                className={({ isActive }) =>
                  cn(
                    'flex min-h-11 items-center gap-3 rounded-full px-3 no-underline',
                    isActive ? 'bg-primary-soft font-bold text-primary' : 'text-text',
                  )
                }
              >
                <Icon aria-hidden="true" className="size-6 shrink-0" />
                {label}
              </NavLink>
            </li>
          ))}
      </ul>
    </nav>
  )
}

import { useAuth, type Me } from '@alovia/shared'
import { Button, cn, Logo, ThemeSwitch } from '@alovia/ui'
import {
  ClipboardCheck,
  Dna,
  Home,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Shield,
  Users,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useOutletContext } from 'react-router'

// DESIGN_SYSTEM §11: Home, Patients, Genetic review, Rule review, Admin (admin only)
const NAV = [
  { to: '/home', label: 'Home', Icon: Home },
  { to: '/patients', label: 'Patients', Icon: Users },
  { to: '/genetic-review', label: 'Genetic review', Icon: Dna },
  { to: '/rule-review', label: 'Rule review', Icon: ClipboardCheck },
]

/** Signed-in doctor layout: side bar (a menu on small screens) and a top bar with the theme.
 * On laptops the side bar can collapse to icons (FRONTEND_REDESIGN §9 SideNav). */
export function DoctorShell({ me }: { me: Me }) {
  const { client } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const items =
    me.user.role === 'admin' ? [...NAV, { to: '/admin', label: 'Admin', Icon: Shield }] : NAV
  const links = (iconsOnly: boolean) => (
    <ul className="flex flex-col gap-1">
      {items.map(({ to, label, Icon }) => (
        <li key={to}>
          <NavLink
            to={to}
            title={iconsOnly ? label : undefined}
            className={({ isActive }) =>
              cn(
                'flex min-h-11 items-center gap-3 rounded-full px-3 no-underline',
                isActive ? 'bg-primary-soft font-semibold text-primary' : 'text-text',
              )
            }
          >
            <Icon aria-hidden="true" className="size-5 shrink-0" />
            <span className={cn(iconsOnly && 'sr-only')}>{label}</span>
          </NavLink>
        </li>
      ))}
    </ul>
  )
  return (
    <div className="min-h-dvh lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">
        Skip to content
      </a>
      <nav
        aria-label="Main"
        className={cn(
          'sticky top-0 hidden h-dvh shrink-0 flex-col gap-4 border-r border-border bg-surface p-3 lg:flex',
          collapsed ? 'w-17' : 'w-60',
        )}
      >
        {!collapsed && (
          <div className="px-2">
            <Logo />
          </div>
        )}
        {links(collapsed)}
        <button
          type="button"
          aria-expanded={!collapsed}
          aria-label={collapsed ? 'Expand menu' : 'Collapse menu'}
          onClick={() => setCollapsed(!collapsed)}
          className="mt-auto flex min-h-11 items-center gap-3 rounded-full px-3 text-muted hover:bg-primary-soft"
        >
          {collapsed ? (
            <PanelLeftOpen aria-hidden="true" className="size-5 shrink-0" />
          ) : (
            <PanelLeftClose aria-hidden="true" className="size-5 shrink-0" />
          )}
        </button>
      </nav>
      <div className="min-w-0 flex-1">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2">
          <details className="lg:hidden">
            <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2">
              <Menu aria-hidden="true" className="size-5" />
              Menu
            </summary>
            <nav aria-label="Main" className="mt-2">
              {links(false)}
            </nav>
          </details>
          <span className="text-sm text-muted">
            {me.doctor?.name ?? me.user.email} · {me.user.role}
          </span>
          <div className="flex items-center gap-3">
            <ThemeSwitch compact />
            <Button variant="ghost" onClick={() => void client.auth.signOut()}>
              Sign out
            </Button>
          </div>
        </header>
        <main id="main" className="p-4 lg:p-6">
          <Outlet context={me} />
        </main>
      </div>
    </div>
  )
}

export function useMe(): Me {
  return useOutletContext<Me>()
}

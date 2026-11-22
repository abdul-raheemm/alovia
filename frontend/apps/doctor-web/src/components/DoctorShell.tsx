import { useAuth, type Me } from '@alovia/shared'
import { Button, cn, Logo, Sheet, ThemeSwitch } from '@alovia/ui'
import {
  ChevronDown,
  CircleUser,
  ClipboardCheck,
  Dna,
  Home,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Shield,
  Users,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { NavLink, Outlet, useNavigate, useOutletContext } from 'react-router'

// DESIGN_SYSTEM §11: Home, Patients, Genetic review, Rule review, Admin (admin only)
const NAV = [
  { to: '/home', label: 'Home', Icon: Home },
  { to: '/patients', label: 'Patients', Icon: Users },
  { to: '/genetic-review', label: 'Genetic review', Icon: Dna },
  { to: '/rule-review', label: 'Rule review', Icon: ClipboardCheck },
]

/** Signed-in doctor layout (FRONTEND_REDESIGN §8.1, §8.5): side bar 240 px, collapsible to
 * 72 px on laptops and always icons on tablets; on phones a menu button opens it as a sheet.
 * Top bar 56 px: patient search ("/" focuses it), theme, user menu. */
export function DoctorShell({ me }: { me: Me }) {
  const { client } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const items =
    me.user.role === 'admin' ? [...NAV, { to: '/admin', label: 'Admin', Icon: Shield }] : NAV

  const links = (iconsOnly: 'never' | 'below-laptop' | 'always', onPick?: () => void) => (
    <ul className="flex flex-col gap-1">
      {items.map(({ to, label, Icon }) => (
        <li key={to}>
          <NavLink
            to={to}
            onClick={onPick}
            title={iconsOnly === 'never' ? undefined : label}
            className={({ isActive }) =>
              cn(
                'relative flex min-h-11 items-center gap-3 rounded-full px-3 no-underline',
                isActive
                  ? // soft pill plus a 2 px marker on the left (§8.1)
                    'bg-primary-soft font-semibold text-primary before:absolute before:top-2 before:bottom-2 before:-left-3 before:w-0.5 before:rounded-full before:bg-primary'
                  : 'text-text hover:bg-primary-soft',
              )
            }
          >
            <Icon aria-hidden="true" className="size-5 shrink-0" />
            <span
              className={cn(
                iconsOnly === 'always' && 'sr-only',
                iconsOnly === 'below-laptop' && 'max-lg:sr-only',
              )}
            >
              {label}
            </span>
          </NavLink>
        </li>
      ))}
    </ul>
  )

  return (
    <div className="min-h-dvh md:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-2">
        Skip to content
      </a>
      <nav
        aria-label="Main"
        className={cn(
          'sticky top-0 hidden h-dvh w-[72px] shrink-0 flex-col gap-4 border-r border-border bg-surface p-3 md:flex',
          !collapsed && 'lg:w-60',
        )}
      >
        <div className={cn('hidden px-2', !collapsed && 'lg:block')}>
          <Logo />
        </div>
        {links(collapsed ? 'always' : 'below-laptop')}
        <button
          type="button"
          aria-expanded={!collapsed}
          aria-label={collapsed ? 'Expand menu' : 'Collapse menu'}
          onClick={() => setCollapsed(!collapsed)}
          className="mt-auto hidden min-h-11 items-center gap-3 rounded-full px-3 text-muted hover:bg-primary-soft lg:flex"
        >
          {collapsed ? (
            <PanelLeftOpen aria-hidden="true" className="size-5 shrink-0" />
          ) : (
            <PanelLeftClose aria-hidden="true" className="size-5 shrink-0" />
          )}
        </button>
      </nav>
      <div className="min-w-0 flex-1">
        <header className="flex h-14 items-center gap-3 border-b border-border bg-surface px-3 md:px-4">
          <button
            type="button"
            aria-label="Open menu"
            onClick={() => setMenuOpen(true)}
            className="flex size-11 shrink-0 items-center justify-center rounded-full hover:bg-primary-soft md:hidden"
          >
            <Menu aria-hidden="true" className="size-5" />
          </button>
          <PatientSearch />
          {/* on phones the theme switch moves into the user menu, so the search keeps its room */}
          <div className="max-md:hidden">
            <ThemeSwitch compact />
          </div>
          <UserMenu
            name={me.doctor?.name ?? me.user.email}
            role={me.user.role}
            onSignOut={() => void client.auth.signOut()}
          />
        </header>
        <main id="main" className="mx-auto max-w-[1440px] p-4 lg:p-6">
          <Outlet context={me} />
        </main>
      </div>
      <Sheet
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        labelledBy="doctor-menu-title"
        className="mr-auto w-[280px] md:hidden"
      >
        <nav aria-label="Main" className="flex h-full flex-col gap-4 bg-surface p-3">
          <div className="flex items-center justify-between">
            <span id="doctor-menu-title" className="px-2">
              <Logo />
            </span>
            <button
              type="button"
              aria-label="Close menu"
              onClick={() => setMenuOpen(false)}
              className="flex size-11 items-center justify-center rounded-full hover:bg-primary-soft"
            >
              <X aria-hidden="true" className="size-5" />
            </button>
          </div>
          {links('never', () => setMenuOpen(false))}
        </nav>
      </Sheet>
    </div>
  )
}

/** Global patient search (§8.1): "/" focuses it from anywhere except a text field; Enter opens
 * the patient list filtered by the name. */
function PatientSearch() {
  const input = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = (e.target as HTMLElement | null)?.closest('input, textarea, select')
      if (e.key === '/' && !typing) {
        e.preventDefault()
        input.current?.focus()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  function go(e: FormEvent) {
    e.preventDefault()
    const q = input.current?.value.trim() ?? ''
    void navigate(q ? `/patients?q=${encodeURIComponent(q)}` : '/patients')
  }
  return (
    <form role="search" onSubmit={go} className="relative min-w-0 flex-1 md:max-w-sm">
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
      />
      <input
        ref={input}
        type="search"
        aria-label="Search patients"
        placeholder="Search patients ( / )"
        className="h-11 w-full rounded-md border border-border bg-bg pr-3 pl-9 text-base"
      />
    </form>
  )
}

/** Name and role, with Sign out (§8.1 user menu). */
function UserMenu({
  name,
  role,
  onSignOut,
}: {
  name: string
  role: string
  onSignOut: () => void
}) {
  return (
    <details className="relative">
      <summary className="flex min-h-11 cursor-pointer list-none items-center gap-1 rounded-full px-3 hover:bg-primary-soft">
        <CircleUser aria-hidden="true" className="size-5 shrink-0" />
        <span className="max-w-40 truncate text-sm max-md:sr-only">{name}</span>
        <ChevronDown aria-hidden="true" className="size-4" />
      </summary>
      <div className="absolute right-0 z-30 mt-2 flex w-72 flex-col gap-3 rounded-md border border-border bg-surface p-3 shadow-md">
        <p className="text-sm">
          <span className="block font-semibold">{name}</span>
          <span className="text-muted">{role}</span>
        </p>
        <div className="md:hidden">
          <ThemeSwitch compact />
        </div>
        <Button variant="secondary" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    </details>
  )
}

export function useMe(): Me {
  return useOutletContext<Me>()
}

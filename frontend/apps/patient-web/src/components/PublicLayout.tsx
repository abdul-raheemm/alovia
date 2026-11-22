import { LEGAL_DOCS } from '@alovia/shared'
import { Logo } from '@alovia/ui'
import { Link, Outlet } from 'react-router'

/** Pages visible without signing in: landing, invite sign-up, sign-in, legal, about. */
export function PublicLayout() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-3xl flex-col gap-6 px-4 py-6">
      <header>
        <Link to="/" className="no-underline">
          <Logo />
        </Link>
      </header>
      {/* about 70 characters per line (impeccable detect: line-length) */}
      <main id="main" className="max-w-[70ch] flex-1">
        <Outlet />
      </main>
      <LegalFooter />
    </div>
  )
}

export function LegalFooter() {
  return (
    <footer className="border-t border-border pt-4 text-sm">
      <nav aria-label="Legal">
        <ul className="flex flex-wrap gap-x-4 gap-y-2">
          {LEGAL_DOCS.map((doc) => (
            <li key={doc.path}>
              <Link to={doc.path}>{doc.title}</Link>
            </li>
          ))}
          <li>
            <Link to="/about">About</Link>
          </li>
        </ul>
      </nav>
    </footer>
  )
}

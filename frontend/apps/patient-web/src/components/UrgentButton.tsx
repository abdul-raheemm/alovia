import { Siren } from 'lucide-react'
import { Link } from 'react-router'

/** Urgent button, top right on every screen (FRONTEND_REDESIGN §7.4). It opens the warning-sign
 * page, which keeps working without the backend (DEC-060). */
export function UrgentButton() {
  return (
    <Link
      to="/urgent"
      className="inline-flex min-h-11 items-center gap-2 rounded-full bg-urgent px-4 font-bold text-white no-underline dark:text-bg"
    >
      <Siren aria-hidden="true" className="size-5" />
      Urgent
    </Link>
  )
}

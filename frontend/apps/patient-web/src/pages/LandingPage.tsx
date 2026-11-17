import { fullDisclaimer, useAuth } from '@alovia/shared'
import { Button, Card } from '@alovia/ui'
import { Link, Navigate } from 'react-router'

/** Landing page without an invite link (UX_FLOWS P1 step 2): what Alovia is, the medical
 * disclaimer, Sign in, legal links, and no open sign-up (DEC-024). */
export function LandingPage() {
  const { session, loading } = useAuth()
  if (!loading && session) return <Navigate to="/home" replace />
  return (
    <section className="flex flex-col gap-6">
      <h1>Alovia</h1>
      <p>A woman-centric pregnancy companion web app with a doctor dashboard.</p>
      <p className="font-semibold">
        Research prototype (academic capstone, MJCET AI &amp; DS). Not for clinical use. Use test
        data only.
      </p>
      <Card>
        <h2 className="mb-2">Medical disclaimer</h2>
        <p>{fullDisclaimer()}</p>
      </Card>
      <div className="flex flex-col items-start gap-3">
        <Button asChild>
          <Link to="/signin">Sign in</Link>
        </Button>
        <p>New here? Ask your doctor for an invite link.</p>
      </div>
    </section>
  )
}

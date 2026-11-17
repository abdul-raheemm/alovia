import { ApiError, type Me } from '@alovia/shared'

/** What the doctor app does after sign-in: only doctor and admin accounts get in.
 * Accounts are created by admins and the owner (DEC-032); there is no sign-up here.
 * They accept the app-wide consent once, at their first sign-in (owner decision 2026-11-17). */
export type DoctorGateStep = 'loading' | 'error' | 'not-set-up' | 'wrong-app' | 'consent' | 'ready'

export function doctorGateStep(me: Me | undefined, meError: unknown): DoctorGateStep {
  if (meError) {
    return meError instanceof ApiError && meError.code === 'FORBIDDEN' ? 'not-set-up' : 'error'
  }
  if (!me) return 'loading'
  if (me.user.role !== 'doctor' && me.user.role !== 'admin') return 'wrong-app'
  return me.consent.accepted ? 'ready' : 'consent'
}

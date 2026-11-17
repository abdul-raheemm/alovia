import { ApiError, type Me } from '@alovia/shared'

/** What the doctor app does after sign-in: only doctor and admin accounts get in.
 * Accounts are created by admins and the owner (DEC-032); there is no sign-up here.
 * TODO(OPEN): whether doctors and admins must also accept the app-wide consent. */
export type DoctorGateStep = 'loading' | 'error' | 'not-set-up' | 'wrong-app' | 'ready'

export function doctorGateStep(me: Me | undefined, meError: unknown): DoctorGateStep {
  if (meError) {
    return meError instanceof ApiError && meError.code === 'FORBIDDEN' ? 'not-set-up' : 'error'
  }
  if (!me) return 'loading'
  return me.user.role === 'doctor' || me.user.role === 'admin' ? 'ready' : 'wrong-app'
}

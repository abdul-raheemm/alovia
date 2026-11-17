import { ApiError, type Me } from '@alovia/shared'

/** What the patient app does after sign-in, before showing any page (UX_FLOWS P1, DEC-036):
 * no account yet + invite code → link; wrong role → wrong app; consent missing → record it
 * (from the sign-up form if the patient already ticked it, otherwise ask). */
export type GateStep =
  | 'loading'
  | 'error'
  | 'link'
  | 'not-set-up'
  | 'wrong-app'
  | 'consent-auto'
  | 'consent-form'
  | 'ready'

export function patientGateStep(input: {
  me: Me | undefined
  meError: unknown
  pendingCode: string | null
  pendingConsentVersion: string | null
  currentConsentVersion: string
}): GateStep {
  const { me, meError, pendingCode, pendingConsentVersion, currentConsentVersion } = input
  if (meError) {
    if (meError instanceof ApiError && meError.code === 'FORBIDDEN') {
      return pendingCode ? 'link' : 'not-set-up'
    }
    return 'error'
  }
  if (!me) return 'loading'
  if (me.user.role !== 'patient') return 'wrong-app'
  if (!me.consent.accepted) {
    return pendingConsentVersion === currentConsentVersion ? 'consent-auto' : 'consent-form'
  }
  return 'ready'
}

/** Sign-up steps that must survive the email-confirmation round trip (UX_FLOWS P1): the invite
 * code from the link and the consent the patient ticked on the sign-up form. Kept only in this
 * browser (essential storage, DEC-027) and cleared once the backend has recorded them. */
const CODE_KEY = 'alovia-invite-code'
const CONSENT_KEY = 'alovia-pending-consent'

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    // storage blocked: the patient can still follow the link again
  }
}

export const pendingInviteCode = {
  get: () => read(CODE_KEY),
  set: (code: string) => write(CODE_KEY, code),
  clear: () => write(CODE_KEY, null),
}

/** The consent version the patient accepted on the sign-up form (both boxes ticked). */
export const pendingConsentVersion = {
  get: () => read(CONSENT_KEY),
  set: (version: string) => write(CONSENT_KEY, version),
  clear: () => write(CONSENT_KEY, null),
}

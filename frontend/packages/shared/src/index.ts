export { ApiError, NETWORK_ERROR, createApiClient, type ApiClient } from './api'
export { AuthProvider, createAuthClient, useAuth } from './auth'
export type { ConsentStatus, InviteCheck, Me } from './types'
export {
  CONSENT_SOURCE,
  CONSENT_VERSION,
  CREDITS_SOURCE,
  consentParts,
  fullDisclaimer,
  LEGAL_DOCS,
  parseConsentVersion,
  shortDisclaimer,
  type LegalDoc,
} from './legal'
export { userMessage } from './messages'

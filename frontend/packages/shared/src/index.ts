export { ApiError, NETWORK_ERROR, createApiClient, type ApiClient } from './api'
export { AuthProvider, createAuthClient, useAuth } from './auth'
export type {
  Appointment,
  AppointmentInput,
  AppointmentList,
  ConsentStatus,
  DoctorNote,
  InviteCheck,
  JourneyContentItem,
  JourneyDatesInput,
  JourneyCalendar,
  JourneyHome,
  Me,
  Milestone,
  MonthDetail,
  Notification,
} from './types'
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

import type { components } from './api-types'

/** Response of GET /me (generated from the backend's OpenAPI schema). */
export type Me = components['schemas']['MeOut']
export type ConsentStatus = components['schemas']['ConsentStatus']
export type InviteCheck = components['schemas']['InviteCheckOut']

/** GET /patient/journey/home and the reply to PUT /patient/journey/dates. */
export type JourneyHome = components['schemas']['HomeOut']
export type JourneyDatesInput =
  | components['schemas']['LmpDatesIn']
  | components['schemas']['DueDateIn']
  | components['schemas']['UltrasoundDatesIn']

import type { components } from './api-types'

/** Response of GET /me (generated from the backend's OpenAPI schema). */
export type Me = components['schemas']['MeOut']
export type ConsentStatus = components['schemas']['ConsentStatus']
export type InviteCheck = components['schemas']['InviteCheckOut']

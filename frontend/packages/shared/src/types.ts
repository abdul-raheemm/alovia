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

/** GET /patient/journey/months/{month} and the content shapes nested in the home payload. */
export type MonthDetail = components['schemas']['MonthDetailOut']
export type JourneyContentItem = components['schemas']['ContentItem']

/** Appointments (Journey §9.3) and calendar markers (§9.1-9.2). */
export type Appointment = components['schemas']['AppointmentOut']
export type AppointmentInput = components['schemas']['AppointmentIn']
export type AppointmentList = components['schemas']['AppointmentsOut']
export type JourneyCalendar = components['schemas']['CalendarOut']
export type Milestone = components['schemas']['MilestoneOut']

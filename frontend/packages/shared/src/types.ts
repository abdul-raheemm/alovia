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

/** Notification bar (Journey §4.2, §10.1) and shared doctor notes (§10.3). */
export type Notification = components['schemas']['NotificationOut']
export type DoctorNote = components['schemas']['DoctorNoteOut']

/** POST /patient/pregnancy-end body (Journey §11.2). */
export type PregnancyEndInput = components['schemas']['PregnancyEndIn']

/** Symptom tracking (Module 7, API.md §4.3). */
export type SymptomVocabulary = components['schemas']['VocabularyOut']
export type CheckinInput = components['schemas']['CheckinIn']
export type EntryInput = components['schemas']['EntryIn']
export type CheckinResult = components['schemas']['CheckinOut']
export type CheckinHistory = components['schemas']['CheckinHistoryOut']
export type SymptomCharts = components['schemas']['ChartsOut']

/** Genetic risk (Module 3, API.md §4.4). */
export type GeneticAssessment = components['schemas']['AssessmentOut']
export type GeneticInput = components['schemas']['AssessmentIn']

/** Doctor home (Dashboard spec §5-8, API.md §4.6). */
export type PatientRow = components['schemas']['PatientRow']
export type PatientDetail = components['schemas']['PatientDetail']
export type PatientInput = components['schemas']['PatientIn']
export type InviteLink = components['schemas']['InviteOut']
export type InboxItem = components['schemas']['InboxItemOut']

/** Doctor predictions, sharing and trends (Dashboard spec §9-11); patient's shared results. */
export type PredictionSchema = components['schemas']['PredictionSchema']
export type PredictionInput = components['schemas']['PredictionIn']
export type PredictionResult = components['schemas']['ResultOut']
export type Trends = components['schemas']['TrendsOut']
export type SharedResult = components['schemas']['PatientResultOut']

/** Doctor sides of other modules (Dashboard §8.3, §12, §13, §15-17). */
export type DoctorAssessment = components['schemas']['DoctorAssessmentOut']
export type DoctorSymptoms = components['schemas']['DoctorSymptomsOut']
export type NoteRecord = components['schemas']['NoteOut']
export type NoteInput = components['schemas']['NoteIn']

import type { InboxItem, PatientRow } from '@alovia/shared'

/** Patient detail tabs (Dashboard spec §5). */
export const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'fetal', label: 'Fetal' },
  { id: 'maternal', label: 'Maternal' },
  { id: 'genetic', label: 'Genetic' },
  { id: 'symptoms', label: 'Symptoms' },
  { id: 'records', label: 'Records' },
  { id: 'notes', label: 'Notes' },
  { id: 'appointments', label: 'Appointments' },
  { id: 'pregnancy', label: 'Pregnancy' },
] as const
export type TabId = (typeof TABS)[number]['id']

/** Inbox item names (§7.1). `ai_note_flag` is always labelled "AI suggestion" (§7.2). */
export const INBOX_LABEL: Record<InboxItem['type'], string> = {
  symptom_l1: 'Symptom check-in: level L1',
  symptom_l2: 'Symptom check-in: level L2',
  pattern_p1: 'Pattern change P1',
  pattern_p2: 'Pattern change P2',
  pattern_p3: 'Pattern change P3',
  pattern_p4: 'Pattern change P4',
  pattern_p5: 'Pattern change P5',
  genetic_pending: 'New genetic assessment',
  genetic_high_priority: 'Genetic assessment: high priority',
  pregnancy_ended: 'Pregnancy ended',
  record_uploaded: 'Record uploaded',
  ai_note_flag: 'AI suggestion',
  chat_urgent: 'Assistant message matched the urgent list',
}

/** §7.2 "Opening an item opens the related record": the patient tab that shows it. */
export function inboxTab(item: Pick<InboxItem, 'type' | 'ref_table'>): TabId {
  switch (item.ref_table) {
    case 'symptom_checkins':
      return 'symptoms'
    case 'genetic_assessments':
      return 'genetic'
    case 'medical_records':
      return 'records'
    case 'pregnancy_date_history':
      return 'pregnancy'
    default:
      return 'overview'
  }
}

export const PREGNANCY_STATUS: Record<string, string> = {
  active: 'Active',
  ended_birth: 'Ended (birth)',
  ended_loss: 'Ended (loss)',
  ended_not_specified: 'Ended (not specified)',
}

export const DUE_DATE_SOURCE: Record<string, string> = {
  lmp_estimate: 'LMP estimate',
  clinician_confirmed: 'Clinician confirmed',
  ultrasound: 'Ultrasound',
}

export function geneticLabel(g: PatientRow['genetic']): string {
  if (!g) return 'None'
  if (g.review_status === 'reviewed') return 'Reviewed'
  return g.priority === 'high' ? 'Pending review (high priority)' : 'Pending review'
}

export function gaLabel(row: Pick<PatientRow, 'ga_weeks' | 'ga_days'>): string {
  return row.ga_weeks === null ? '—' : `${row.ga_weeks}w ${row.ga_days ?? 0}d`
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
}

/** A date-only value (due date) shown as it is, never shifted by time zone. */
export function formatDay(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(y ?? 0, (m ?? 1) - 1, d ?? 1)).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export interface Filters {
  search: string
  status: string // '' = any
  fetal: string
  maternal: string
  genetic: string
  symptom: string
  unseenOnly: boolean
}

export const NO_FILTERS: Filters = {
  search: '',
  status: '',
  fetal: '',
  maternal: '',
  genetic: '',
  symptom: '',
  unseenOnly: false,
}

/** §6 search by name and filters by status columns; keeps the server's order. */
export function filterPatients(rows: PatientRow[], f: Filters): PatientRow[] {
  const q = f.search.trim().toLocaleLowerCase()
  return rows.filter(
    (r) =>
      (!q || r.name.toLocaleLowerCase().includes(q)) &&
      (!f.status || r.pregnancy_status === f.status) &&
      (!f.fetal || r.fetal?.predicted_class === f.fetal) &&
      (!f.maternal || r.maternal?.predicted_class === f.maternal) &&
      (!f.genetic || geneticLabel(r.genetic) === f.genetic) &&
      (!f.symptom || r.symptom?.level === f.symptom) &&
      (!f.unseenOnly || r.unseen_count > 0),
  )
}

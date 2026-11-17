/** Pure helpers for the Journey screens (no network), so they can be unit-tested. */
import type { JourneyHome } from '@alovia/shared'

/** Shown in place of any message a doctor has not approved yet (DEC-041). */
export const PENDING_TEXT = '[Text pending doctor approval]'

export function messageText(messages: JourneyHome['messages'], key: string): string {
  return messages[key] ?? PENDING_TEXT
}

/** 2027-03-01 -> "1 March 2027" (dates are plain calendar days; no time zone shift). */
export function formatDay(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(y ?? 0, (m ?? 1) - 1, d ?? 1)).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

/** Home header (Journey spec §4.3): "N weeks, D days pregnant"; the counter stops at 42. */
export function weeksLabel(pregnancy: NonNullable<JourneyHome['pregnancy']>): string {
  if (pregnancy.completed_weeks >= 42) return '42 weeks pregnant'
  const weeks = `${pregnancy.completed_weeks} ${pregnancy.completed_weeks === 1 ? 'week' : 'weeks'}`
  const days = `${pregnancy.days} ${pregnancy.days === 1 ? 'day' : 'days'}`
  return `${weeks}, ${days} pregnant`
}

export const SOURCE_LABEL: Record<string, string> = {
  lmp_estimate: 'Estimate from your last period',
  clinician_confirmed: 'Given by your doctor',
  ultrasound: 'From an ultrasound scan',
}

/** Field messages for the date rules (Journey spec §5.2). D2's wording follows the spec's
 * stated result: "ask her to check the date or talk to her doctor". */
export function dateRuleText(code: string | undefined): string | undefined {
  switch (code) {
    case undefined:
      return undefined
    case 'D1':
      return "This date can't be in the future."
    case 'D2':
      return 'Please check this date, or talk to your doctor.'
    case 'D3':
      return 'Enter a pregnancy age between 0 and 42 weeks.'
    default:
      return 'Please check this value.'
  }
}

/** "Weeks 23–27" (month card and detail header; data from the config month map). */
export function weekRangeLabel(weekStart: number, weekEnd: number): string {
  return `Weeks ${weekStart}–${weekEnd}`
}

/** Placeholder month illustrations (spec §7.1): simple shapes labelled "placeholder",
 * allowed only while the prototype banner is shown; replaced by openly licensed drawings. */
export function illustrationSrc(month: number): string {
  return `/illustrations/month_${month}.svg`
}

export function illustrationAlt(month: number): string {
  return `Placeholder drawing for month ${month}`
}

/** §7.2 wording: "about the size of a [object]" plus the typical value — never "your baby". */
export function sizeLine(size: {
  object_name: string
  length_cm?: number | null
  weight_g?: number | null
}): string {
  const values = [
    size.length_cm != null ? `about ${size.length_cm} cm` : null,
    size.weight_g != null ? `about ${size.weight_g} g` : null,
  ].filter(Boolean)
  return `About the size of a ${size.object_name} (${values.join(', ')})`
}

// ---- calendar and appointments (Journey §6.4, §9) ----

/** A local calendar day as "YYYY-MM-DD" (the browser's own date, no UTC shift). */
export function isoDay(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** "YYYY-MM-DD" -> a local Date at midnight (the inverse of isoDay). */
export function parseDay(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y ?? 0, (m ?? 1) - 1, d ?? 1)
}

/** First and last day of the month that contains `d`, for GET /journey/calendar. */
export function monthBounds(d: Date): { from: string; to: string } {
  return {
    from: isoDay(new Date(d.getFullYear(), d.getMonth(), 1)),
    to: isoDay(new Date(d.getFullYear(), d.getMonth() + 1, 0)),
  }
}

/** The 7 days (Sunday to Saturday, as the month view) of the week that contains `d`. */
export function weekDays(d: Date): Date[] {
  const sunday = new Date(d.getFullYear(), d.getMonth(), d.getDate() - d.getDay())
  return Array.from(
    { length: 7 },
    (_, i) => new Date(sunday.getFullYear(), sunday.getMonth(), sunday.getDate() + i),
  )
}

/** Keep the shown month inside §9.1's navigation range (pregnancy start .. due date + 2 weeks). */
export function clampMonth(month: Date, start?: string | null, end?: string | null): Date {
  const first = (d: Date) => new Date(d.getFullYear(), d.getMonth(), 1)
  if (start && month < first(parseDay(start))) return first(parseDay(start))
  if (end && month > first(parseDay(end))) return first(parseDay(end))
  return first(month)
}

/** "14:30:00" -> "2:30 pm" (the backend already sends the patient's local time). */
export function formatTime(time: string): string {
  const [h, m] = time.split(':').map(Number)
  return new Date(Date.UTC(1970, 0, 1, h ?? 0, m ?? 0)).toLocaleTimeString('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'UTC',
  })
}

/** "1 March 2027, 2:30 pm", or just the day for a date-only appointment. */
export function appointmentWhen(a: { date: string; time?: string | null }): string {
  return a.time ? `${formatDay(a.date)}, ${formatTime(a.time)}` : formatDay(a.date)
}

/** §6.4/§9.2 small calendar labels (neutral markers, no medical claims). */
export function milestoneLabel(m: { kind: string; value: number }): string {
  switch (m.kind) {
    case 'new_week':
      return `Week ${m.value} begins`
    case 'new_month':
      return `Month ${m.value} begins`
    case 'new_trimester':
      return `Trimester ${m.value} begins`
    case 'term':
      return `${m.value} weeks`
    case 'due_date':
      return 'Due date'
    default:
      return 'Milestone'
  }
}

// ---- notification bar (Journey §4.2, §10.1) ----

/** Neutral wording for each notification (never celebratory: §10.2). */
export function notificationText(n: { type: string; target_ref?: string | null }): string {
  switch (n.type) {
    case 'new_week':
      return `Week ${n.target_ref} has started`
    case 'new_month':
      return `Month ${n.target_ref} has started`
    case 'appointment_soon':
      return 'You have an appointment coming up soon'
    case 'doctor_note':
      return 'Your doctor shared a note with you'
    case 'result_available':
      return 'A new result is available'
    case 'genetic_reviewed':
      return 'Your genetic check has been reviewed'
    case 'dates_updated':
      return 'Your doctor updated your pregnancy dates'
    default:
      return 'New notification'
  }
}

/** Where tapping a notification leads (§10.1 "Target"). TODO(Phases 4-5): My results and
 * Genetic risk pages; until then those open More. */
export function notificationTarget(n: { type: string; target_ref?: string | null }): string {
  switch (n.type) {
    case 'new_month':
      return `/months/${n.target_ref}`
    case 'appointment_soon':
      return '/appointments'
    case 'doctor_note':
      return '/doctor-notes'
    case 'dates_updated':
      return '/dates'
    case 'result_available':
    case 'genetic_reviewed':
      return '/more'
    default:
      return '/home'
  }
}

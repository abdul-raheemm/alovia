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

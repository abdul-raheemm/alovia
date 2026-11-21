/** Pregnancy ring geometry (FRONTEND_REDESIGN §7.2). Pure functions, so the headline and the
 * drawing are computed from the same day number in the same render (§11 rule 10).
 *
 * Positions are in weeks (t = day / 7, 0 to 42). The ring has 43 week slots in three arcs
 * (weeks 0-13, 14-27, 28-42: 14, 14 and 15 slots) separated by 3 degree gaps, starting at
 * 12 o'clock and running clockwise. The marker stops at 42 weeks (§7.2 "Cap"). */

export const MAX_DAY = 42 * 7
export const GAP_DEG = 3
const SLOTS = 43
const DEG_PER_WEEK = (360 - 3 * GAP_DEG) / SLOTS
/** First week of each trimester arc and its slot count. */
export const ARCS = [
  { from: 0, slots: 14 },
  { from: 14, slots: 14 },
  { from: 28, slots: 15 },
] as const

export function trimesterOf(t: number): 0 | 1 | 2 {
  return t < 14 ? 0 : t < 28 ? 1 : 2
}

/** Degrees clockwise from 12 o'clock for a position in weeks (half a gap before arc 1). */
export function angleOf(t: number): number {
  return GAP_DEG / 2 + t * DEG_PER_WEEK + trimesterOf(t) * GAP_DEG
}

/** Start and end angle of each trimester arc. */
export function arcAngles(i: 0 | 1 | 2): [number, number] {
  const { from, slots } = ARCS[i]
  const start = GAP_DEG / 2 + from * DEG_PER_WEEK + i * GAP_DEG
  return [start, start + slots * DEG_PER_WEEK]
}

/** The position in weeks for an angle; angles inside a gap snap to the nearer arc end. */
export function weeksAt(angle: number): number {
  const a = ((angle % 360) + 360) % 360
  for (const i of [0, 1, 2] as const) {
    const [start, end] = arcAngles(i)
    if (a <= end + GAP_DEG / 2) {
      const clamped = Math.max(start, Math.min(end, a))
      return ARCS[i].from + (clamped - start) / DEG_PER_WEEK
    }
  }
  return 0 // the half gap before 12 o'clock belongs to the start
}

/** Day number (0 to MAX_DAY) for a pointer at (x, y) around the centre (cx, cy), in screen
 * coordinates (y down). `previous` keeps the marker from jumping across 12 o'clock: past either
 * end it stops there (§7.2: "at both ends the marker stops"). */
export function dayAtPoint(x: number, y: number, cx: number, cy: number, previous: number): number {
  const angle = (Math.atan2(x - cx, cy - y) * 180) / Math.PI
  const day = Math.round(Math.min(42, weeksAt(angle)) * 7)
  // a jump of more than half the ring means the pointer crossed the top: stay at the end
  if (Math.abs(day - previous) > MAX_DAY / 2) return previous < MAX_DAY / 2 ? 0 : MAX_DAY
  return day
}

/** Point on a circle for an angle measured clockwise from 12 o'clock. */
export function pointAt(angle: number, r: number, cx = 160, cy = 160): [number, number] {
  const rad = (angle * Math.PI) / 180
  return [cx + r * Math.sin(rad), cy - r * Math.cos(rad)]
}

/** SVG path for an arc from angle a to angle b (clockwise). */
export function arcPath(a: number, b: number, r: number, cx = 160, cy = 160): string {
  const [x1, y1] = pointAt(a, r, cx, cy)
  const [x2, y2] = pointAt(b, r, cx, cy)
  const large = b - a > 180 ? 1 : 0
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`
}

/** Today's day number from the home data, held at the 42-week end. */
export function todayDay(p: { completed_weeks: number; days: number }): number {
  return Math.min(MAX_DAY, p.completed_weeks * 7 + p.days)
}

/** The date a pregnancy week starts, from the due date (day 280 = due date, the same rule as
 * the backend's Journey engine). ISO dates in, ISO date out, no time-zone shift. */
export function weekStartDate(dueDate: string, week: number): string {
  const [y, m, d] = dueDate.split('-').map(Number) as [number, number, number]
  const date = new Date(Date.UTC(y, m - 1, d - 280 + week * 7))
  return date.toISOString().slice(0, 10)
}

/** The month whose week range holds this week (from the served month map, Journey §6.3). */
export function monthOfWeek(
  months: readonly { month: number; week_start: number; week_end: number }[],
  week: number,
): number | undefined {
  return months.find((m) => m.week_start <= week && week <= m.week_end)?.month
}

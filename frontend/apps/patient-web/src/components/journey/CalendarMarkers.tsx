import type { Appointment, JourneyCalendar, Milestone } from '@alovia/shared'
import { CalendarClock, CircleDashed, Flag, TriangleAlert } from 'lucide-react'

import { isoDay } from '../../app/journey'

export interface DayMarkers {
  milestones: Milestone[]
  appointments: Appointment[]
  suggested: string[] // §9.2 suggested check-up labels (official schedule)
  levels: string[] // §9.2 the day's symptom check-in levels (Module 7)
}

/** Calendar data grouped by local day ("YYYY-MM-DD"). */
export function markersByDay(data: JourneyCalendar | undefined): Map<string, DayMarkers> {
  const byDay = new Map<string, DayMarkers>()
  const entry = (day: string) => {
    const found = byDay.get(day) ?? {
      milestones: [],
      appointments: [],
      suggested: [],
      levels: [],
    }
    byDay.set(day, found)
    return found
  }
  for (const m of data?.milestones ?? []) entry(m.date).milestones.push(m)
  for (const a of data?.appointments ?? []) entry(a.date).appointments.push(a)
  for (const s of data?.suggested_checkups ?? []) entry(s.date).suggested.push(s.label)
  for (const d of data?.symptom_days ?? []) entry(d.date).levels.push(...d.levels)
  return byDay
}

/** Words for screen readers, matching the small icons (§9.2 markers). */
export function markerWords(markers: DayMarkers | undefined): string {
  const words = [
    markers?.milestones.length ? 'milestone' : null,
    markers?.appointments.length ? 'appointment' : null,
    markers?.suggested.length ? 'suggested check-up' : null,
    markers?.levels.length ? 'symptoms logged' : null,
    // FRONTEND_REDESIGN §7.6: the level is named, not only coloured
    markers && warningLevel(markers)
      ? `Level ${warningLevel(markers)?.slice(1)} warning logged`
      : null,
  ].filter(Boolean)
  return words.length ? `, ${words.join(', ')}` : ''
}

/** §9.2: a day with an L1 or L2 check-in gets the distinct red-flag icon. */
export function hasRedFlag(markers: DayMarkers): boolean {
  return warningLevel(markers) !== null
}

/** The day's highest warning level: L1 above L2; null when there is none. */
export function warningLevel(markers: DayMarkers): 'L1' | 'L2' | null {
  if (markers.levels.includes('L1')) return 'L1'
  if (markers.levels.includes('L2')) return 'L2'
  return null
}

/** Pregnancy week of a local day, counted from the pregnancy start (Journey §9.1 range start). */
export function pregnancyWeekOn(start: string, day: string): number {
  const [a, b] = [start, day].map((d) => {
    const [y, m, dd] = d.split('-').map(Number) as [number, number, number]
    return Date.UTC(y, m - 1, dd)
  }) as [number, number]
  return Math.floor((b - a) / (7 * 86_400_000))
}

export function markersFor(byDay: Map<string, DayMarkers>, day: Date): DayMarkers | undefined {
  return byDay.get(isoDay(day))
}

/** The small §9.2 icons: flag = milestone, clock = appointment, dashed circle = suggested
 * check-up, dot = symptoms logged, triangle = red-flag check-in (decorative; see markerWords). */
export function MarkerIcons({
  milestone,
  appointment,
  suggested = false,
  symptoms = false,
  redFlag = false,
}: {
  milestone: boolean
  appointment: boolean
  suggested?: boolean
  symptoms?: boolean
  redFlag?: boolean
}) {
  return (
    <span aria-hidden="true" className="flex h-3 items-center gap-0.5 text-primary">
      {milestone && <Flag className="size-3" />}
      {appointment && <CalendarClock className="size-3" />}
      {suggested && <CircleDashed className="size-3" />}
      {/* §9.2: a dot for any check-in; red-flag days get a distinct icon in another colour */}
      {symptoms && <span className="size-2 rounded-full bg-muted" />}
      {redFlag && <TriangleAlert className="size-3 text-urgent" />}
    </span>
  )
}

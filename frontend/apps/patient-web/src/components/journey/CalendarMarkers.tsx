import type { Appointment, JourneyCalendar, Milestone } from '@alovia/shared'
import { CalendarClock, Flag } from 'lucide-react'

import { isoDay } from '../../app/journey'

export interface DayMarkers {
  milestones: Milestone[]
  appointments: Appointment[]
}

/** Calendar data grouped by local day ("YYYY-MM-DD"). */
export function markersByDay(data: JourneyCalendar | undefined): Map<string, DayMarkers> {
  const byDay = new Map<string, DayMarkers>()
  const entry = (day: string) => {
    const found = byDay.get(day) ?? { milestones: [], appointments: [] }
    byDay.set(day, found)
    return found
  }
  for (const m of data?.milestones ?? []) entry(m.date).milestones.push(m)
  for (const a of data?.appointments ?? []) entry(a.date).appointments.push(a)
  return byDay
}

/** Words for screen readers, matching the small icons (§9.2 markers). */
export function markerWords(markers: DayMarkers | undefined): string {
  const words = [
    markers?.milestones.length ? 'milestone' : null,
    markers?.appointments.length ? 'appointment' : null,
  ].filter(Boolean)
  return words.length ? `, ${words.join(', ')}` : ''
}

export function markersFor(byDay: Map<string, DayMarkers>, day: Date): DayMarkers | undefined {
  return byDay.get(isoDay(day))
}

/** The small §9.2 icons: flag = milestone, clock = appointment (decorative; see markerWords).
 * TODO(Phase 3): symptom-day dot and a distinct red-flag icon (Module 7, §15 test 8). */
export function MarkerIcons({
  milestone,
  appointment,
}: {
  milestone: boolean
  appointment: boolean
}) {
  return (
    <span aria-hidden="true" className="flex h-3 items-center gap-0.5 text-primary">
      {milestone && <Flag className="size-3" />}
      {appointment && <CalendarClock className="size-3" />}
    </span>
  )
}

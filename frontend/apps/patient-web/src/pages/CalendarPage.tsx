import 'react-day-picker/style.css'

import { userMessage } from '@alovia/shared'
import { Card, cn, ErrorState, PageSkeleton } from '@alovia/ui'
import { CalendarClock, CircleDashed, Flag, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { DayPicker, type DayButtonProps } from 'react-day-picker'
import { Link, useSearchParams } from 'react-router'

import {
  clampMonth,
  formatDay,
  formatTime,
  isoDay,
  milestoneLabel,
  monthBounds,
  parseDay,
} from '../app/journey'
import { LEVEL_HEADING, type Level } from '../app/symptoms'
import { useCalendar } from '../app/useAppointments'
import { DoctorAddedLabel } from '../components/journey/Appointments'
import {
  hasRedFlag,
  MarkerIcons,
  markersByDay,
  markersFor,
  markerWords,
  type DayMarkers,
} from '../components/journey/CalendarMarkers'

const DAY = /^\d{4}-\d{2}-\d{2}$/

/** Calendar tab (Journey §9.1-9.2, UX_FLOWS P7): month view with milestone and appointment
 * markers; tapping a day shows that day's details. `?day=YYYY-MM-DD` opens on that day. */
export function CalendarPage() {
  const [params] = useSearchParams()
  const asked = params.get('day')
  const initial = asked && DAY.test(asked) ? parseDay(asked) : new Date()
  const [month, setMonth] = useState(() => clampMonth(initial))
  const [selected, setSelected] = useState<Date | undefined>(initial)
  const { from, to } = monthBounds(month)
  const calendar = useCalendar(from, to)

  if (calendar.isPending) return <PageSkeleton />
  if (calendar.isError) {
    return (
      <ErrorState
        message={userMessage(calendar.error, 'patient')}
        onRetry={() => void calendar.refetch()}
      />
    )
  }
  const data = calendar.data
  const byDay = markersByDay(data)
  const shown = clampMonth(month, data.start, data.end)
  const has = (kind: keyof DayMarkers) => (day: Date) =>
    (markersFor(byDay, day)?.[kind].length ?? 0) > 0

  return (
    <section className="flex flex-col gap-4">
      <h1>Calendar</h1>
      <Card className="flex justify-center px-1 sm:px-5">
        <DayPicker
          className="alovia-calendar"
          mode="single"
          selected={selected}
          onSelect={setSelected}
          month={shown}
          onMonthChange={(m) => {
            setMonth(m)
            setSelected(undefined) // the details below only cover the month on screen
          }}
          startMonth={data.start ? parseDay(data.start) : undefined}
          endMonth={data.end ? parseDay(data.end) : undefined}
          modifiers={{
            milestone: has('milestones'),
            appointment: has('appointments'),
            suggested: has('suggested'),
            symptoms: has('levels'),
            redFlag: (day: Date) => {
              const m = markersFor(byDay, day)
              return Boolean(m && hasRedFlag(m))
            },
          }}
          components={{ DayButton: MarkerDayButton }}
          labels={{
            // starts with the visible day number (WCAG 2.5.3), e.g. "17 November 2026, Tuesday"
            labelDayButton: (date, modifiers) =>
              [
                formatDay(isoDay(date)),
                date.toLocaleDateString('en-IN', { weekday: 'long' }),
                modifiers.today ? 'today' : null,
                modifiers.selected ? 'selected' : null,
              ]
                .filter(Boolean)
                .join(', ') + markerWords(markersFor(byDay, date)),
          }}
        />
      </Card>
      <p className="flex flex-wrap gap-4 text-sm text-muted">
        <span className="flex items-center gap-1">
          <Flag aria-hidden="true" className="size-4 text-primary" /> Milestone
        </span>
        <span className="flex items-center gap-1">
          <CalendarClock aria-hidden="true" className="size-4 text-primary" /> Appointment
        </span>
        <span className="flex items-center gap-1">
          <span aria-hidden="true" className="size-2 rounded-full bg-muted" /> Symptoms logged
        </span>
        <span className="flex items-center gap-1">
          <TriangleAlert aria-hidden="true" className="size-4 text-urgent" /> Red flag
        </span>
        {data.suggested_source && (
          <span className="flex items-center gap-1">
            <CircleDashed aria-hidden="true" className="size-4 text-primary" /> Suggested check-up
          </span>
        )}
      </p>
      {/* §9.2: suggested check-ups come only from the official schedule in config.yaml */}
      {data.suggested_source && (
        <p className="text-sm text-muted">
          Suggested check-ups: {data.suggested_source.publisher} —{' '}
          <a href={data.suggested_source.url} target="_blank" rel="noreferrer">
            {data.suggested_source.title}
          </a>
        </p>
      )}
      <DayDetails day={selected} markers={selected ? markersFor(byDay, selected) : undefined} />
    </section>
  )
}

/** The library's day button plus the §9.2 marker icons. Keeps its keyboard focus handling. */
function MarkerDayButton({ day, modifiers, className, children, ...props }: DayButtonProps) {
  const ref = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (modifiers.focused) ref.current?.focus()
  }, [modifiers.focused])
  return (
    <button
      ref={ref}
      data-day={isoDay(day.date)}
      className={cn(className, 'flex flex-col items-center justify-center gap-0.5 leading-none')}
      {...props}
    >
      {children}
      <MarkerIcons
        milestone={Boolean(modifiers.milestone)}
        appointment={Boolean(modifiers.appointment)}
        suggested={Boolean(modifiers.suggested)}
        symptoms={Boolean(modifiers.symptoms)}
        redFlag={Boolean(modifiers.redFlag)}
      />
    </button>
  )
}

/** "Tapping a day shows that day's appointments, check-ins and milestones" (§9.2).
 * TODO(Phase 3): that day's check-ins with their levels (Module 7). */
function DayDetails({ day, markers }: { day?: Date; markers?: DayMarkers }) {
  if (!day) {
    return (
      <Card>
        <p className="text-muted">Choose a day to see its details.</p>
      </Card>
    )
  }
  const empty =
    !markers ||
    (markers.milestones.length === 0 &&
      markers.appointments.length === 0 &&
      markers.suggested.length === 0 &&
      markers.levels.length === 0)
  return (
    <section aria-labelledby="day-heading" className="flex flex-col gap-3">
      <h2 id="day-heading">{formatDay(isoDay(day))}</h2>
      {empty ? (
        <Card>
          <p className="text-muted">Nothing on this day.</p>
        </Card>
      ) : (
        <Card className="flex flex-col gap-3">
          {markers.milestones.length > 0 && (
            <ul className="flex flex-col gap-1">
              {markers.milestones.map((m) => (
                <li key={`${m.kind}-${m.value}`} className="flex items-center gap-2">
                  <Flag aria-hidden="true" className="size-4 shrink-0 text-primary" />
                  {milestoneLabel(m)}
                </li>
              ))}
            </ul>
          )}
          {markers.levels.length > 0 && (
            // §9.2: that day's check-ins with their levels
            <ul className="flex flex-col gap-1">
              {markers.levels.map((level, i) => (
                <li key={i} className="flex items-center gap-2">
                  {level === 'L0' ? (
                    <span aria-hidden="true" className="size-2 rounded-full bg-muted" />
                  ) : (
                    <TriangleAlert aria-hidden="true" className="size-4 text-urgent" />
                  )}
                  Check-in: {LEVEL_HEADING[level as Level]}
                </li>
              ))}
            </ul>
          )}
          {markers.suggested.length > 0 && (
            <ul className="flex flex-col gap-1">
              {markers.suggested.map((label) => (
                <li key={label} className="flex items-center gap-2">
                  <span className="rounded-md border border-dashed border-primary px-2 py-0.5 text-sm">
                    suggested
                  </span>
                  {label}
                </li>
              ))}
            </ul>
          )}
          {markers.appointments.length > 0 && (
            <ul className="flex flex-col gap-3">
              {markers.appointments.map((a) => (
                <li key={a.id} className="flex items-start gap-2">
                  <CalendarClock
                    aria-hidden="true"
                    className="mt-0.5 size-4 shrink-0 text-primary"
                  />
                  <div>
                    <p className="font-semibold">
                      {a.time ? `${formatTime(a.time)} — ` : ''}
                      {a.title}
                    </p>
                    {a.source === 'doctor' && <DoctorAddedLabel />}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}
      <p className="text-sm">
        <Link to="/appointments">Manage appointments</Link>
      </p>
    </section>
  )
}

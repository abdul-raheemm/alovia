import 'react-day-picker/style.css'

import { userMessage, type CheckinHistory, type JourneyCalendar } from '@alovia/shared'
import { Button, CalendarMonthSkeleton, Card, cn, ErrorState, Sheet } from '@alovia/ui'
import {
  CalendarClock,
  CircleAlert,
  CircleDashed,
  Flag,
  LocateFixed,
  TriangleAlert,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { DayPicker, type DayButtonProps, type WeekNumberProps } from 'react-day-picker'
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
import { SYMPTOM_BUNDLE } from '../app/symptomBundle.generated'
import { useCalendar } from '../app/useAppointments'
import { useMediaQuery } from '../app/useMediaQuery'
import { useCheckins, useVocabulary } from '../app/useSymptoms'
import { DoctorAddedLabel } from '../components/journey/Appointments'
import {
  markersByDay,
  markersFor,
  markerWords,
  pregnancyWeekOn,
  warningLevel,
  type DayMarkers,
} from '../components/journey/CalendarMarkers'

const DAY = /^\d{4}-\d{2}-\d{2}$/
const LAPTOP = '(min-width: 1024px)'
const WEEKDAY = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

/** Calendar (Journey §9.1-9.2, FRONTEND_REDESIGN §7.6): where logged symptoms live, with
 * appointments and milestones. Phone: one scroll of months from the pregnancy start to the due
 * date + 2 weeks, rows = pregnancy weeks with a "W24" gutter (owner 2026-11-21, DEC-115), a day
 * opens a bottom sheet. Laptop: one month with Previous / Next / Today and a day panel.
 * `?day=YYYY-MM-DD` opens on that day. */
export function CalendarPage() {
  const [params] = useSearchParams()
  const asked = params.get('day')
  const askedDay = asked && DAY.test(asked) ? asked : null
  // the current month first (it carries the range), then the whole range in one request
  const { from, to } = monthBounds(askedDay ? parseDay(askedDay) : new Date())
  const probe = useCalendar(from, to)
  const range = probe.data?.start && probe.data.end ? probe.data : null
  const full = useCalendar(range?.start ?? from, range?.end ?? to)
  const calendar = range ? full : probe
  const laptop = useMediaQuery(LAPTOP)

  if (calendar.isPending || (range && full.isPlaceholderData)) {
    return (
      <div role="status" aria-label="Loading" className="flex flex-col gap-4">
        <CalendarMonthSkeleton />
      </div>
    )
  }
  if (calendar.isError) {
    return (
      <ErrorState
        message={userMessage(calendar.error, 'patient')}
        onRetry={() => void calendar.refetch()}
      />
    )
  }
  return <CalendarView data={calendar.data} askedDay={askedDay} laptop={laptop} />
}

function CalendarView({
  data,
  askedDay,
  laptop,
}: {
  data: JourneyCalendar
  askedDay: string | null
  laptop: boolean
}) {
  const byDay = useMemo(() => markersByDay(data), [data])
  const today = isoDay(new Date())
  // laptop: the panel always shows a day (today at first); phone: a sheet opens on a tap
  const [selected, setSelected] = useState<string | null>(askedDay)
  const [legendOpen, setLegendOpen] = useState(false)
  const start = data.start
  const weekStartsOn = start ? (parseDay(start).getDay() as 0 | 1 | 2 | 3 | 4 | 5 | 6) : 0
  const shown = selected ?? (laptop ? today : null)
  // stable component types, so a tap does not rebuild every cell (and keeps keyboard focus)
  const components = useMemo(
    () => ({
      DayButton: (props: DayButtonProps) => (
        <MarkerDayButton {...props} markers={markersFor(byDay, props.day.date)} />
      ),
      WeekNumber: (props: WeekNumberProps) => <WeekGutter {...props} start={start} />,
    }),
    [byDay, start],
  )

  const common = {
    className: 'alovia-calendar w-full',
    weekStartsOn,
    showWeekNumber: Boolean(start),
    showOutsideDays: false,
    startMonth: start ? parseDay(start) : undefined,
    endMonth: data.end ? parseDay(data.end) : undefined,
    modifiers: {
      suggested: (d: Date) => (markersFor(byDay, d)?.suggested.length ?? 0) > 0,
    },
    modifiersClassNames: { suggested: 'cal-suggested', today: 'cal-today' },
    components,
    labels: {
      // starts with the visible day number (WCAG 2.5.3), e.g. "17 November 2026, Tuesday"
      labelDayButton: (date: Date, modifiers: Record<string, boolean>) =>
        [
          formatDay(isoDay(date)),
          date.toLocaleDateString('en-IN', { weekday: 'long' }),
          modifiers.today ? 'today' : null,
        ]
          .filter(Boolean)
          .join(', ') + markerWords(markersFor(byDay, date)),
      labelWeekNumber: (n: number) => `Pregnancy week ${n}`,
    },
  }

  const details = shown ? <DayDetails day={shown} start={start} markers={byDay.get(shown)} /> : null

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h1>Calendar</h1>
        <Button
          type="button"
          variant="ghost"
          aria-expanded={legendOpen}
          aria-controls="calendar-legend"
          onClick={() => setLegendOpen(!legendOpen)}
          className="text-sm underline"
        >
          What these mean
        </Button>
      </div>
      {legendOpen && <Legend id="calendar-legend" suggested={Boolean(data.suggested_source)} />}

      {laptop || !start ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
          <LaptopMonth
            dayPicker={common}
            today={today}
            initialMonth={parseDay(shown ?? today)}
            start={start}
            end={data.end}
            selected={shown}
            onSelect={setSelected}
          />
          {laptop && <div className="lg:sticky lg:top-4">{details}</div>}
        </div>
      ) : (
        <PhoneMonths
          dayPicker={common}
          start={start}
          end={data.end ?? start}
          today={today}
          focusDay={askedDay ?? today}
          selected={selected}
          onSelect={setSelected}
          weekStartsOn={weekStartsOn}
        />
      )}

      {/* §9.2: suggested check-ups come only from the official schedule in config.yaml */}
      {data.suggested_source && (
        <p className="text-sm text-muted">
          Suggested check-ups: {data.suggested_source.publisher} —{' '}
          <a href={data.suggested_source.url} target="_blank" rel="noreferrer">
            {data.suggested_source.title}
          </a>
        </p>
      )}

      {!laptop && (
        <Sheet
          open={selected !== null}
          onClose={() => setSelected(null)}
          labelledBy="day-heading"
          from="bottom"
          className="top-auto bottom-0 h-auto max-h-[85dvh] rounded-t-2xl"
        >
          <div className="flex flex-col gap-3 p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
            <div className="flex justify-end">
              <button
                type="button"
                aria-label="Close"
                onClick={() => setSelected(null)}
                className="flex size-11 items-center justify-center rounded-full hover:bg-primary-soft"
              >
                <X aria-hidden="true" className="size-6" />
              </button>
            </div>
            {details}
          </div>
        </Sheet>
      )}
    </section>
  )
}

type PickerProps = Record<string, unknown>

/** Laptop: one month grid with Previous, Next and Today (FRONTEND_REDESIGN §7.6). */
function LaptopMonth({
  dayPicker,
  today,
  initialMonth,
  start,
  end,
  selected,
  onSelect,
}: {
  dayPicker: PickerProps
  today: string
  initialMonth: Date
  start: string | null
  end: string | null
  selected: string | null
  onSelect: (day: string) => void
}) {
  const [month, setMonth] = useState(() => clampMonth(initialMonth, start, end))
  return (
    <Card className="flex flex-col gap-3 px-2 sm:px-4">
      <div className="flex justify-end">
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            setMonth(clampMonth(parseDay(today), start, end))
            onSelect(today)
          }}
        >
          Today
        </Button>
      </div>
      <DayPicker
        {...dayPicker}
        mode="single"
        month={month}
        onMonthChange={setMonth}
        selected={selected ? parseDay(selected) : undefined}
        onSelect={(d) => d && onSelect(isoDay(d))}
        classNames={{ day: 'cal-cell cal-cell-lg' }}
      />
    </Card>
  )
}

/** Phone: every month of the range in one scroll; weekday letters pinned, month names sticky,
 * "Jump to today" when today is well out of view (FRONTEND_REDESIGN §7.6). */
function PhoneMonths({
  dayPicker,
  start,
  end,
  today,
  focusDay,
  selected,
  onSelect,
  weekStartsOn,
}: {
  dayPicker: PickerProps
  start: string
  end: string
  today: string
  focusDay: string
  selected: string | null
  onSelect: (day: string) => void
  weekStartsOn: number
}) {
  const list = useRef<HTMLDivElement>(null)
  const [todayAway, setTodayAway] = useState(false)
  const first = parseDay(start)
  const last = parseDay(end)
  const months =
    (last.getFullYear() - first.getFullYear()) * 12 + last.getMonth() - first.getMonth() + 1

  // open on today (or the asked day); then watch whether today is in view
  useEffect(() => {
    const cell = list.current?.querySelector(`[data-day="${focusDay}"]`)
    cell?.scrollIntoView({ block: 'center' })
  }, [focusDay])
  useEffect(() => {
    const cell = list.current?.querySelector(`[data-day="${today}"]`)
    if (!cell) return
    const watch = new IntersectionObserver(([e]) => setTodayAway(!e?.isIntersecting), {
      rootMargin: '50% 0px', // "well off-screen": more than half a screen away
    })
    watch.observe(cell)
    return () => watch.disconnect()
  }, [today])

  return (
    <div ref={list} className="relative">
      <div
        aria-hidden="true"
        className="sticky top-0 z-30 grid grid-cols-[2rem_repeat(7,minmax(0,1fr))] border-b border-border bg-bg py-1 text-center text-xs font-semibold text-muted"
      >
        <span />
        {Array.from({ length: 7 }, (_, i) => (
          <span key={i}>{WEEKDAY[(weekStartsOn + i) % 7]}</span>
        ))}
      </div>
      <DayPicker
        {...dayPicker}
        mode="single"
        defaultMonth={first}
        numberOfMonths={months}
        hideNavigation
        hideWeekdays
        selected={selected ? parseDay(selected) : undefined}
        onSelect={(d) => d && onSelect(isoDay(d))}
        classNames={{
          months: 'flex flex-col gap-4',
          // sits right under the 25 px weekday row, so no row shows through between them
          month_caption: 'sticky top-[25px] z-10 bg-bg py-2 font-display text-lg font-bold',
          day: 'cal-cell',
        }}
      />
      {todayAway && (
        <Button
          type="button"
          className="fixed right-4 bottom-[calc(5.5rem+env(safe-area-inset-bottom))] z-20 rounded-full shadow-md"
          onClick={() =>
            list.current?.querySelector(`[data-day="${today}"]`)?.scrollIntoView({
              block: 'center',
              // §5.4: instant with reduced motion
              behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
            })
          }
        >
          <LocateFixed aria-hidden="true" className="size-5" />
          Jump to today
        </Button>
      )}
    </div>
  )
}

/** "W24" at the start of each row: the row is exactly one pregnancy week (DEC-115). */
function WeekGutter({ week, start, ...props }: WeekNumberProps & { start: string | null }) {
  const firstDay = week.days[0]?.date
  const n = start && firstDay ? pregnancyWeekOn(start, isoDay(firstDay)) : null
  return (
    <th {...props} className="w-8 text-xs font-semibold text-muted tabular-nums">
      {n !== null && n >= 0 && n <= 44 ? `W${n}` : ''}
    </th>
  )
}

/** The library's day button with this day's markers (§7.6 table; up to two plus "+n"). */
function MarkerDayButton({
  day,
  modifiers,
  className,
  children,
  markers,
  ...props
}: DayButtonProps & { markers: DayMarkers | undefined }) {
  const ref = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (modifiers.focused) ref.current?.focus()
  }, [modifiers.focused])
  const icons = markerIcons(markers)
  return (
    <button
      ref={ref}
      data-day={isoDay(day.date)}
      className={cn(className, 'flex flex-col items-center justify-center gap-0.5 leading-none')}
      {...props}
    >
      {children}
      <span aria-hidden="true" className="flex h-3 items-center gap-0.5">
        {icons.slice(0, 2)}
        {icons.length > 2 && <span className="text-[10px] font-bold">+{icons.length - 2}</span>}
      </span>
    </button>
  )
}

/** Marker icons in priority order: warning level, check-in dot, appointment, milestone flag
 * (new weeks are in the gutter instead). Suggested check-ups are a dashed cell outline. */
function markerIcons(m: DayMarkers | undefined): ReactNode[] {
  if (!m) return []
  const icons: ReactNode[] = []
  const level = warningLevel(m)
  if (level === 'L1') icons.push(<TriangleAlert key="l1" className="size-3 text-urgent" />)
  if (level === 'L2') icons.push(<CircleAlert key="l2" className="size-3 text-caution" />)
  if (m.levels.length) icons.push(<span key="dot" className="size-2 rounded-full bg-primary" />)
  if (m.appointments.length)
    icons.push(<CalendarClock key="appt" className="size-3 text-primary" />)
  if (m.milestones.some((x) => x.kind !== 'new_week'))
    icons.push(<Flag key="flag" className="size-3 text-primary" />)
  return icons
}

function Legend({ id, suggested }: { id: string; suggested: boolean }) {
  const row = (icon: ReactNode, text: string) => (
    <li className="flex items-center gap-2">
      <span aria-hidden="true" className="flex w-5 justify-center">
        {icon}
      </span>
      {text}
    </li>
  )
  return (
    <Card id={id}>
      <ul className="grid gap-2 text-sm sm:grid-cols-2">
        {row(<span className="size-2 rounded-full bg-primary" />, 'Check-in logged')}
        {row(<TriangleAlert className="size-4 text-urgent" />, 'Level 1 warning logged')}
        {row(<CircleAlert className="size-4 text-caution" />, 'Level 2 warning logged')}
        {row(<CalendarClock className="size-4 text-primary" />, 'Appointment')}
        {row(<Flag className="size-4 text-primary" />, 'Milestone')}
        {row(<span className="text-xs font-semibold">W24</span>, 'Pregnancy week')}
        {suggested &&
          row(<CircleDashed className="size-4 text-primary" />, 'Suggested check-up (dashed)')}
      </ul>
    </Card>
  )
}

/** A day's details (§7.6 "Tap a day"): pregnancy week, check-ins with their symptoms, severity,
 * duration and level, appointments, milestones, suggested check-ups. Past days are view-only. */
function DayDetails({
  day,
  start,
  markers,
}: {
  day: string
  start: string | null
  markers: DayMarkers | undefined
}) {
  const checkins = useCheckins()
  const ofDay = (checkins.data ?? []).filter((c) => c.local_date === day)
  const week = start ? pregnancyWeekOn(start, day) : null
  const empty =
    !markers ||
    (markers.milestones.length === 0 &&
      markers.appointments.length === 0 &&
      markers.suggested.length === 0 &&
      markers.levels.length === 0)
  return (
    <section aria-labelledby="day-heading" className="flex flex-col gap-3">
      <div>
        <h2 id="day-heading">{formatDay(day)}</h2>
        {week !== null && week >= 0 && <p className="text-sm text-muted">Week {week}</p>}
      </div>
      {empty ? (
        <Card className="flex flex-col items-start gap-3">
          <p className="text-muted">Nothing on this day.</p>
          {/* empty state (open item 6, DEC-118): only today can be logged (§7.6) */}
          {day === isoDay(new Date()) && (
            <Button asChild>
              <Link to="/log">Log a symptom</Link>
            </Button>
          )}
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
          {ofDay.length > 0 ? (
            <ul className="flex flex-col gap-3">
              {ofDay.map((c) => (
                <CheckinItem key={c.checkin_id} checkin={c} />
              ))}
            </ul>
          ) : (
            // the check-in list could not be loaded: fall back to the day's levels
            markers.levels.length > 0 && (
              <ul className="flex flex-col gap-1">
                {markers.levels.map((level, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <LevelIcon level={level} />
                    Check-in: {LEVEL_HEADING[level as Level]}
                  </li>
                ))}
              </ul>
            )
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

function LevelIcon({ level }: { level: string }) {
  if (level === 'L1')
    return <TriangleAlert aria-hidden="true" className="size-4 shrink-0 text-urgent" />
  if (level === 'L2')
    return <CircleAlert aria-hidden="true" className="size-4 shrink-0 text-caution" />
  return <span aria-hidden="true" className="size-2 shrink-0 rounded-full bg-primary" />
}

/** One check-in with each symptom's severity and duration (labels from the vocabulary; warning
 * signs no longer offered this week fall back to the bundled list). */
function CheckinItem({ checkin }: { checkin: CheckinHistory }) {
  const vocab = useVocabulary()
  const v = vocab.data
  const label = (id: string) =>
    v?.common.find((s) => s.id === id)?.label ??
    v?.warning.find((s) => s.id === id)?.label ??
    SYMPTOM_BUNDLE.warning.find((s) => s.id === id)?.label ??
    id
  const word = (map: Record<string, string> | undefined, key: string | null | undefined) =>
    key ? (map?.[key] ?? key) : null
  return (
    <li className="flex flex-col gap-1">
      <p className="flex items-center gap-2 font-semibold">
        <LevelIcon level={checkin.red_flag_level} />
        Check-in: {LEVEL_HEADING[checkin.red_flag_level as Level]}
      </p>
      <ul className="ml-6 flex flex-col gap-0.5 text-sm">
        {checkin.entries.map((e, i) => (
          <li key={i}>
            {[
              label(e.symptom),
              word(v?.severities, e.severity),
              word({ ...v?.durations, ...v?.labour_durations }, e.duration),
            ]
              .filter(Boolean)
              .join(' · ')}
          </li>
        ))}
      </ul>
    </li>
  )
}

import type { JourneyContentItem, JourneyHome } from '@alovia/shared'
import { Card, cn } from '@alovia/ui'
import { BookOpen, CalendarClock, PenLine } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router'

import {
  appointmentWhen,
  illustrationAlt,
  isoDay,
  illustrationSrc,
  messageText,
  sizeLine,
  weekDays,
  weekRangeLabel,
} from '../../app/journey'
import { useCalendar } from '../../app/useAppointments'
import { MarkerIcons, markersByDay, markersFor, markerWords } from './CalendarMarkers'

type Messages = JourneyHome['messages']

/** §8.3: shown on every content screen while prototype content is active. */
export function PrototypeBanner({ messages }: { messages: Messages }) {
  return (
    <p role="status" className="rounded-md border border-caution/40 bg-caution/10 p-3 text-sm">
      {messageText(messages, 'msg_prototype_content')}
    </p>
  )
}

/** §4.3 baby card: month illustration (gentle float, D3) and the size comparison, worded as
 * typical (§13.1). No size row -> no comparison (§7.2). */
export function BabyCard({
  pregnancy,
  size,
  messages,
}: {
  pregnancy: NonNullable<JourneyHome['pregnancy']>
  size: JourneyHome['size']
  messages: Messages
}) {
  const reduceMotion = useReducedMotion()
  return (
    <Card className="flex items-center gap-4">
      <motion.img
        src={illustrationSrc(pregnancy.month)}
        alt={illustrationAlt(pregnancy.month)}
        width={112}
        height={112}
        className="size-28 shrink-0"
        animate={reduceMotion ? undefined : { y: [0, -5, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="flex flex-col gap-1">
        <h2>Month {pregnancy.month}</h2>
        {size && (
          <p className="flex items-center gap-2">
            {/* comparison object from Microsoft Fluent Emoji (MIT); name is in the text */}
            <img
              src={`/icons/fluent/${size.object_icon_id}.svg`}
              alt=""
              width={28}
              height={28}
              className="size-7 shrink-0"
            />
            {sizeLine(size)}
          </p>
        )}
        {size && (
          <p className="text-sm text-muted">
            Source: {size.source.publisher} — {size.source.title}
          </p>
        )}
        <p className="text-sm text-muted">{messageText(messages, 'msg_typical_not_yours')}</p>
      </div>
    </Card>
  )
}

/** One educational content card: primary-soft, "Learn" label and source line (DESIGN_SYSTEM
 * §10, D15 — educational content always looks different from her own data). */
export function ContentCard({ item }: { item: JourneyContentItem }) {
  return (
    <article className="rounded-lg bg-primary-soft p-4">
      <p className="mb-1 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-primary">
        <BookOpen aria-hidden="true" className="size-4" />
        Learn
      </p>
      <h3>{item.title}</h3>
      <p className="mt-1 whitespace-pre-line">{item.body}</p>
      <p className="mt-2 text-sm text-muted">
        Source:{' '}
        <a href={item.source.url} target="_blank" rel="noreferrer">
          {item.source.publisher} — {item.source.title}
        </a>
      </p>
    </article>
  )
}

/** §4.3 "This stage": fetal development and body changes for the content week, with
 * "Read more" into the month detail. Empty until task 4 fills the content files. */
export function StageSection({
  items,
  month,
  messages,
  showBanner,
}: {
  items: JourneyContentItem[]
  month: number
  messages: Messages
  showBanner: boolean
}) {
  return (
    <section aria-labelledby="stage-heading" className="flex flex-col gap-3">
      <h2 id="stage-heading">This stage</h2>
      {showBanner && <PrototypeBanner messages={messages} />}
      {items.length === 0 ? (
        <Card>
          <p className="text-muted">Content for this stage is being prepared.</p>
        </Card>
      ) : (
        items.map((item) => <ContentCard key={item.id} item={item} />)
      )}
      <p className="text-sm">
        <Link to={`/months/${month}`}>Read more about month {month}</Link>
      </p>
    </section>
  )
}

/** §4.4 month cards: swipeable strip of 9, the current month highlighted. */
export function MonthsStrip({
  months,
  currentMonth,
}: {
  months: JourneyHome['months']
  currentMonth: number
}) {
  return (
    <section aria-labelledby="months-heading" className="flex flex-col gap-3">
      <h2 id="months-heading">Your nine months</h2>
      <ul className="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2">
        {months.map(({ month, week_start, week_end }) => {
          const current = month === currentMonth
          return (
            <li key={month} className="w-36 shrink-0 snap-start">
              <Link
                to={`/months/${month}`}
                aria-current={current ? 'true' : undefined}
                className={cn(
                  'flex h-full flex-col items-center gap-2 rounded-lg border bg-surface p-3 text-center no-underline',
                  current ? 'border-primary shadow-sm' : 'border-border',
                )}
              >
                <img
                  src={illustrationSrc(month)}
                  alt={illustrationAlt(month)}
                  width={72}
                  height={72}
                  className="size-18"
                />
                <span className={cn('font-semibold', current && 'text-primary')}>
                  Month {month}
                </span>
                <span className="text-sm text-muted">{weekRangeLabel(week_start, week_end)}</span>
                {current && (
                  <span className="text-xs font-semibold text-primary">You are here</span>
                )}
              </Link>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/** §4.3 quick log shortcut. The "logged today" state arrives with Phase 3 (Module 7). */
export function QuickLogCard() {
  return (
    <Card>
      <Link to="/log" className="flex items-center gap-3 no-underline">
        <PenLine aria-hidden="true" className="size-6 shrink-0 text-primary" />
        <span className="font-semibold text-text">Log a symptom</span>
      </Link>
    </Card>
  )
}

/** §4.3 next appointment block (shown only when one is upcoming). */
export function NextAppointmentCard({
  appointment,
}: {
  appointment: NonNullable<JourneyHome['next_appointment']>
}) {
  return (
    <Card className="flex items-center gap-3">
      <CalendarClock aria-hidden="true" className="size-6 shrink-0 text-primary" />
      <div>
        <h2 className="text-base">Next appointment</h2>
        <p>
          {/* date and time arrive already in the patient's local time (config timezone) */}
          {appointment.title} — {appointmentWhen(appointment)}
        </p>
      </div>
    </Card>
  )
}

/** §9.1 week strip on the home screen: this week's days with their markers; a day opens the
 * calendar on that day. Markers load on their own, so the home never waits for them. */
export function WeekStrip() {
  const days = weekDays(new Date())
  const today = isoDay(new Date())
  const calendar = useCalendar(isoDay(days[0] as Date), isoDay(days[6] as Date))
  const byDay = markersByDay(calendar.data)
  return (
    <section aria-labelledby="week-heading" className="flex flex-col gap-3">
      <h2 id="week-heading">This week</h2>
      <ol className="grid grid-cols-7 gap-1">
        {days.map((d) => {
          const iso = isoDay(d)
          const markers = markersFor(byDay, d)
          const current = iso === today
          return (
            <li key={iso}>
              <Link
                to={`/calendar?day=${iso}`}
                aria-current={current ? 'date' : undefined}
                className={cn(
                  'flex min-h-16 flex-col items-center justify-center gap-0.5 rounded-md border text-sm no-underline',
                  current
                    ? 'border-primary bg-primary-soft font-bold text-primary'
                    : 'border-border bg-surface text-text',
                )}
              >
                <span className="text-xs">
                  {d.toLocaleDateString('en-IN', { weekday: 'short' })}
                </span>
                {/* the name starts with the visible "Tue 17" (WCAG 2.5.3), then the rest */}{' '}
                <span>{d.getDate()}</span>{' '}
                <span className="sr-only">
                  {d.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
                  {markerWords(markers)}
                </span>
                <MarkerIcons
                  milestone={Boolean(markers?.milestones.length)}
                  appointment={Boolean(markers?.appointments.length)}
                />
              </Link>
            </li>
          )
        })}
      </ol>
      <p className="text-sm">
        <Link to="/calendar">Open the calendar</Link>
      </p>
    </section>
  )
}

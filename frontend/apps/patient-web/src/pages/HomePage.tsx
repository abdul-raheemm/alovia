import { userMessage, type JourneyHome } from '@alovia/shared'
import { Button, Card, CardSkeleton, ErrorState, RingSkeleton, Skeleton } from '@alovia/ui'
import { Eye, Info } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { formatDay, messageText, weeksLabel } from '../app/journey'
import { monthOfWeek, todayDay, weekStartDate } from '../app/ring'
import { useJourneyHome } from '../app/useJourneyHome'
import { useNotifications } from '../app/useNotifications'
import { EndedHome } from '../components/journey/EndedHome'
import {
  GeneticCheckCard,
  MonthsStrip,
  NextAppointmentCard,
  QuickLogCard,
  SizeLine,
  StageSection,
  WeekStrip,
  WeeklySummary,
} from '../components/journey/JourneyBlocks'
import { NotificationBar, StatusCards } from '../components/journey/NotificationBar'
import { PregnancyRing } from '../components/journey/PregnancyRing'

type Pregnancy = NonNullable<JourneyHome['pregnancy']>
const TRIMESTER = ['First trimester', 'Second trimester', 'Third trimester']

/** Journey home (Journey §4.3, FRONTEND_REDESIGN §7.1): notification bar, the ring with today's
 * month image, the headline, the preview chip while dragging, the size line; then quick log,
 * this stage, this week's summary, next appointment, status cards, the week strip and the nine
 * month cards (which keep every week reachable without the ring). Laptop: two columns. */
export function HomePage() {
  const home = useJourneyHome()
  // §11 rule 5: home data and notifications appear together (no layout shift); a failed
  // notifications call does not block the home (it shows no bar)
  const notifications = useNotifications()
  if (home.isPending || notifications.isPending) return <HomeSkeleton />
  if (home.isError) {
    return (
      <ErrorState
        message={userMessage(home.error, 'patient')}
        onRetry={() => void home.refetch()}
      />
    )
  }
  const data = home.data
  if (data.state === 'ended') return <EndedHome data={data} />
  const pregnancy = data.state === 'no_date' ? null : data.pregnancy
  return (
    <section className="flex flex-col gap-6">
      <h1 className="sr-only">Home</h1>
      <NotificationBar />
      {data.notices.map((key) => (
        <Notice key={key}>{messageText(data.messages, key)}</Notice>
      ))}
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[420px_minmax(0,1fr)] lg:items-start lg:gap-8">
        {pregnancy ? (
          <RingColumn data={data} pregnancy={pregnancy} />
        ) : (
          <OnboardingCard data={data} />
        )}
        <div className="flex flex-col gap-6">
          <QuickLogCard loggedToday={data.logged_today} />
          {pregnancy && (
            <StageSection
              items={data.stage_items}
              month={pregnancy.month}
              messages={data.messages}
              showBanner={data.show_prototype_banner}
            />
          )}
          {data.weekly_summary && <WeeklySummary summary={data.weekly_summary} />}
          {data.next_appointment && <NextAppointmentCard appointment={data.next_appointment} />}
          <StatusCards />
          {data.genetic_check && <GeneticCheckCard check={data.genetic_check} />}
          {pregnancy && <WeekStrip />}
          {pregnancy && data.months.length > 0 && (
            <MonthsStrip months={data.months} currentMonth={pregnancy.month} />
          )}
        </div>
      </div>
    </section>
  )
}

/** First paint (§7.1): the ring's shape and a card, never a blank screen. */
function HomeSkeleton() {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-6">
      <RingSkeleton />
      <Skeleton className="mx-auto h-8 w-2/3 rounded-sm" />
      <CardSkeleton />
    </div>
  )
}

/** Ring, headline, preview chip and size line; sticky on laptops (§7.1 "Home on desktop"). */
function RingColumn({ data, pregnancy }: { data: JourneyHome; pregnancy: Pregnancy }) {
  const today = todayDay(pregnancy)
  // §7.2 (c): local state only, so leaving Home and coming back returns to today
  const [previewDay, setPreviewDay] = useState(today)
  const previewing = previewDay !== today
  const week = Math.floor(previewDay / 7)
  const readMonth = monthOfWeek(data.months, week)
  return (
    <div className="flex flex-col gap-3 lg:sticky lg:top-4">
      <PregnancyRing
        today={today}
        previewDay={previewDay}
        onPreview={setPreviewDay}
        month={pregnancy.month}
      />
      {/* §11 rule 10: computed from previewDay in the same render */}
      {previewing && data.dates.due_date ? (
        <div className="flex flex-col items-center gap-2 text-center">
          <h2 className="tabular-nums">Week {week}</h2>
          <p>Starts {formatDay(weekStartDate(data.dates.due_date, week))}</p>
          {readMonth && (
            <p>
              <Link to={`/months/${readMonth}`}>Read about week {week}</Link>
            </p>
          )}
          <p className="flex flex-wrap items-center justify-center gap-2 rounded-full bg-primary-soft py-1 pr-1 pl-3 text-sm font-semibold">
            <Eye aria-hidden="true" className="size-4 text-primary" />
            Viewing week {week} ·
            <Button
              type="button"
              variant="ghost"
              className="min-h-11 rounded-full px-3 text-sm"
              onClick={() => setPreviewDay(today)}
            >
              Back to today
            </Button>
          </p>
        </div>
      ) : (
        <Headline data={data} pregnancy={pregnancy} />
      )}
      <SizeLine size={data.size} messages={data.messages} />
      <p className="text-sm">
        <Link to="/dates">Change pregnancy dates</Link>
      </p>
    </div>
  )
}

/** §7.1 row 4: weeks and days, trimester, days to go, due date and the estimate label. */
function Headline({ data, pregnancy }: { data: JourneyHome; pregnancy: Pregnancy }) {
  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <h2 className="text-[clamp(1.375rem,1.1rem+1.2vw,1.75rem)]">{weeksLabel(pregnancy)}</h2>
      <p className="text-muted">{TRIMESTER[pregnancy.trimester - 1]}</p>
      <p className="flex flex-wrap items-center justify-center gap-x-2">
        {pregnancy.days_to_go !== null && (
          <>
            <span>
              {pregnancy.days_to_go} {pregnancy.days_to_go === 1 ? 'day' : 'days'} to go
            </span>
            <span aria-hidden="true">·</span>
          </>
        )}
        {data.dates.due_date && <span>Due date: {formatDay(data.dates.due_date)}</span>}
        {pregnancy.is_estimate && (
          <span className="rounded-full bg-primary-soft px-2 py-0.5 text-sm font-semibold">
            estimate
          </span>
        )}
      </p>
      {pregnancy.is_estimate && (
        <p className="text-sm text-muted">{messageText(data.messages, 'msg_estimate_label')}</p>
      )}
      {data.state === 'past_due' && (
        <Notice>{messageText(data.messages, 'msg_past_due_date')}</Notice>
      )}
      {data.state === 'beyond_42' && (
        <Notice>{messageText(data.messages, 'msg_beyond_42_weeks')}</Notice>
      )}
    </div>
  )
}

/** §4.5 "No due date": onboarding card only (no ring); quick log and urgent stay. */
function OnboardingCard({ data }: { data: JourneyHome }) {
  return (
    <Card className="flex flex-col items-start gap-4">
      <h2>Your pregnancy dates</h2>
      <p>{messageText(data.messages, 'msg_onboarding')}</p>
      <Button asChild>
        <Link to="/dates">Enter your dates</Link>
      </Button>
    </Card>
  )
}

function Notice({ children }: { children: string }) {
  return (
    <p role="status" className="flex items-start gap-2 rounded-md bg-primary-soft p-3 text-left">
      <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-primary" />
      {children}
    </p>
  )
}

import { userMessage, type JourneyHome } from '@alovia/shared'
import { Button, Card, ErrorState, PageSkeleton, PlaceholderPage } from '@alovia/ui'
import { Info } from 'lucide-react'
import { Link } from 'react-router'

import { formatDay, messageText, weeksLabel } from '../app/journey'
import { useJourneyHome } from '../app/useJourneyHome'

/** Journey home (spec §4.3, §4.5). This task: onboarding card and the header.
 * TODO(Phase 2 tasks 5-8): baby card, this stage, appointments, status cards, ended screens. */
export function HomePage() {
  const home = useJourneyHome()
  if (home.isPending) return <PageSkeleton />
  if (home.isError) {
    return (
      <ErrorState
        message={userMessage(home.error, 'patient')}
        onRetry={() => void home.refetch()}
      />
    )
  }
  const data = home.data
  if (data.state === 'ended') return <PlaceholderPage title="Home" />
  return (
    <section className="flex flex-col gap-4">
      <h1 className="sr-only">Home</h1>
      {data.notices.map((key) => (
        <Notice key={key}>{messageText(data.messages, key)}</Notice>
      ))}
      {data.state === 'no_date' || !data.pregnancy ? (
        <OnboardingCard data={data} />
      ) : (
        <Header data={data} pregnancy={data.pregnancy} />
      )}
    </section>
  )
}

/** §4.5 "No due date": onboarding card only. */
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

/** §4.3 header: weeks and days, days to go, due date, and the estimate label. */
function Header({
  data,
  pregnancy,
}: {
  data: JourneyHome
  pregnancy: NonNullable<JourneyHome['pregnancy']>
}) {
  return (
    <Card className="flex flex-col gap-2">
      <h2>{weeksLabel(pregnancy)}</h2>
      {pregnancy.days_to_go !== null && (
        <p>
          {pregnancy.days_to_go} {pregnancy.days_to_go === 1 ? 'day' : 'days'} to go
        </p>
      )}
      {data.dates.due_date && (
        <p>
          Due date: {formatDay(data.dates.due_date)}
          {pregnancy.is_estimate && (
            <span className="ml-2 rounded-full bg-primary-soft px-2 py-0.5 text-sm font-semibold">
              estimate
            </span>
          )}
        </p>
      )}
      {pregnancy.is_estimate && (
        <p className="text-sm text-muted">{messageText(data.messages, 'msg_estimate_label')}</p>
      )}
      {data.state === 'past_due' && (
        <Notice>{messageText(data.messages, 'msg_past_due_date')}</Notice>
      )}
      {data.state === 'beyond_42' && (
        <Notice>{messageText(data.messages, 'msg_beyond_42_weeks')}</Notice>
      )}
      <p className="text-sm">
        <Link to="/dates">Change pregnancy dates</Link>
      </p>
    </Card>
  )
}

function Notice({ children }: { children: string }) {
  return (
    <p role="status" className="flex items-start gap-2 rounded-md bg-primary-soft p-3">
      <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-primary" />
      {children}
    </p>
  )
}

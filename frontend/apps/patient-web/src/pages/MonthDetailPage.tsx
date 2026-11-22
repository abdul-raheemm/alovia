import { userMessage } from '@alovia/shared'
import { Card, ErrorState, PageSkeleton } from '@alovia/ui'
import { Link, useParams } from 'react-router'

import { illustrationAlt, illustrationSrc, messageText, weekRangeLabel } from '../app/journey'
import { useJourneyHome, useMonthDetail } from '../app/useJourneyHome'
import { ContentCard, PrototypeBanner } from '../components/journey/JourneyBlocks'

/** §4.4 month detail: larger illustration, this month's content, warning-signs link and
 * sources, from the content provider (§8). */
export function MonthDetailPage() {
  const params = useParams()
  const month = Number(params.month)
  const home = useJourneyHome()
  const detail = useMonthDetail(month)

  if (!Number.isInteger(month) || month < 1 || month > 9) {
    return (
      <section className="flex flex-col gap-4">
        <h1>We couldn't find this.</h1>
        <Link to="/home">Back to home</Link>
      </section>
    )
  }
  if (home.isPending || detail.isPending) return <PageSkeleton />
  if (home.isError || detail.isError) {
    const failed = home.isError ? home : detail
    return (
      <ErrorState
        message={userMessage(failed.error, 'patient')}
        onRetry={() => {
          void home.refetch()
          void detail.refetch()
        }}
      />
    )
  }
  const { messages, show_prototype_banner } = home.data
  const data = detail.data
  return (
    <section className="flex flex-col gap-4">
      <p>
        <Link className="tap" to="/home">
          &larr; Back to home
        </Link>
      </p>
      <div className="flex items-center gap-4">
        <img
          src={illustrationSrc(month)}
          alt={illustrationAlt(month)}
          width={144}
          height={144}
          className="size-36 shrink-0"
        />
        <div>
          <h1>Month {data.month}</h1>
          <p className="text-muted">{weekRangeLabel(data.week_start, data.week_end)}</p>
          {data.is_current && <p className="font-semibold text-primary">You are here</p>}
        </div>
      </div>
      {show_prototype_banner && <PrototypeBanner messages={messages} />}
      {data.items.length === 0 ? (
        <Card>
          <p className="text-muted">Content for this month is being prepared.</p>
        </Card>
      ) : (
        data.items.map((item) => <ContentCard key={item.id} item={item} />)
      )}
      <p className="text-sm text-muted">{messageText(messages, 'msg_typical_not_yours')}</p>
      <Card>
        <h2 className="font-sans text-base">Warning signs</h2>
        <p className="mt-1">
          If something feels wrong, check the <Link to="/log">warning signs</Link> or use the urgent
          button at the top.
        </p>
      </Card>
    </section>
  )
}

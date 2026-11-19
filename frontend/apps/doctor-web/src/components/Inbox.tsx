import { userMessage, type InboxItem } from '@alovia/shared'
import { Button, Card, cn, ErrorState, PageSkeleton } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { formatDateTime, INBOX_LABEL, inboxTab } from '../app/patients'
import { api } from '../app/services'

function Item({ item }: { item: InboxItem }) {
  const qc = useQueryClient()
  const seen = useMutation({
    mutationFn: () => api.post<InboxItem>(`/doctor/inbox/${item.id}/seen`, {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['doctor-inbox'] })
      void qc.invalidateQueries({ queryKey: ['doctor-patients'] })
    },
  })
  const ai = item.type === 'ai_note_flag'
  return (
    <li
      className={cn('flex flex-wrap items-center justify-between gap-3 py-3', ai && 'text-muted')}
    >
      <div className="flex flex-col gap-1">
        <span className="flex items-center gap-2 font-semibold">
          {ai && <Sparkles aria-hidden="true" className="size-4" />}
          {INBOX_LABEL[item.type]}
        </span>
        <span>
          <Link to={`/patients/${item.patient_id}/${inboxTab(item)}`}>{item.patient_name}</Link>
          <span className="text-sm text-muted"> · {formatDateTime(item.created_at)}</span>
        </span>
        {item.seen_at && (
          <span className="text-sm text-muted">
            Seen by {item.seen_by_name ?? 'a doctor'} at {formatDateTime(item.seen_at)}
          </span>
        )}
        {seen.isError && (
          <span role="alert" className="text-sm text-urgent">
            {userMessage(seen.error, 'doctor')}
          </span>
        )}
      </div>
      {!item.seen_at && (
        <Button
          variant="secondary"
          loading={seen.isPending}
          onClick={() => seen.mutate()}
          aria-label={`Mark as seen: ${INBOX_LABEL[item.type]}, ${item.patient_name}`}
        >
          Mark as seen
        </Button>
      )}
    </li>
  )
}

/** Needs-attention inbox (§7): unseen items first; AI suggestions come last from the server
 * and are labelled; seen items show who saw them and when. */
export function Inbox() {
  const [showSeen, setShowSeen] = useState(false)
  const inbox = useQuery({
    queryKey: ['doctor-inbox', showSeen],
    queryFn: () => api.get<InboxItem[]>(`/doctor/inbox${showSeen ? '?seen=true' : ''}`),
  })
  return (
    <section aria-labelledby="inbox-heading" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="inbox-heading">Needs attention</h2>
        <Button variant="ghost" onClick={() => setShowSeen((s) => !s)} aria-pressed={showSeen}>
          {showSeen ? 'Show unseen items' : 'Show seen items'}
        </Button>
      </div>
      {inbox.isPending ? (
        <PageSkeleton />
      ) : inbox.isError ? (
        <ErrorState
          message={userMessage(inbox.error, 'doctor')}
          onRetry={() => void inbox.refetch()}
        />
      ) : inbox.data.length === 0 ? (
        <Card>
          <p>{showSeen ? 'No seen items yet.' : 'Nothing needs attention right now.'}</p>
        </Card>
      ) : (
        <Card className="py-2">
          <ul className="divide-y divide-border">
            {inbox.data.map((item) => (
              <Item key={item.id} item={item} />
            ))}
          </ul>
        </Card>
      )}
    </section>
  )
}

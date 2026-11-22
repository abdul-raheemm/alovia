import { userMessage, type InboxItem } from '@alovia/shared'
import { Button, Card, cn, ErrorState, TableRowSkeleton } from '@alovia/ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  CircleAlert,
  Dna,
  FileText,
  Info,
  MessageCircleWarning,
  Sparkles,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { formatDateTime, gaLabel, INBOX_LABEL, inboxTab } from '../app/patients'
import { api } from '../app/services'
import { usePatients } from './PatientList'

export function useInbox(showSeen = false) {
  return useQuery({
    queryKey: ['doctor-inbox', showSeen],
    queryFn: () => api.get<InboxItem[]>(`/doctor/inbox${showSeen ? '?seen=true' : ''}`),
  })
}

// level icon next to the label (text is always there too); L1 / L2 keep their reserved colours
const ICON: Record<InboxItem['type'], { Icon: LucideIcon; tone?: string }> = {
  symptom_l1: { Icon: TriangleAlert, tone: 'text-urgent' },
  symptom_l2: { Icon: CircleAlert, tone: 'text-caution' },
  pattern_p1: { Icon: Activity },
  pattern_p2: { Icon: Activity },
  pattern_p3: { Icon: Activity },
  pattern_p4: { Icon: Activity },
  pattern_p5: { Icon: Activity },
  genetic_pending: { Icon: Dna },
  genetic_high_priority: { Icon: Dna },
  pregnancy_ended: { Icon: Info },
  record_uploaded: { Icon: FileText },
  ai_note_flag: { Icon: Sparkles },
  chat_urgent: { Icon: MessageCircleWarning, tone: 'text-urgent' },
}

function Item({ item, week }: { item: InboxItem; week: string | null }) {
  const qc = useQueryClient()
  const seen = useMutation({
    mutationFn: () => api.post<InboxItem>(`/doctor/inbox/${item.id}/seen`, {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['doctor-inbox'] })
      void qc.invalidateQueries({ queryKey: ['doctor-patients'] })
    },
  })
  const ai = item.type === 'ai_note_flag'
  const { Icon, tone } = ICON[item.type]
  return (
    <li
      className={cn('flex flex-wrap items-center justify-between gap-3 py-3', ai && 'text-muted')}
    >
      <div className="flex min-w-0 items-start gap-3">
        <Icon aria-hidden="true" className={cn('mt-0.5 size-5 shrink-0', tone ?? 'text-muted')} />
        <div className="flex flex-col gap-1">
          <span className="font-semibold">{INBOX_LABEL[item.type]}</span>
          <span>
            <Link to={`/patients/${item.patient_id}/${inboxTab(item)}`}>{item.patient_name}</Link>
            <span className="text-sm text-muted tabular-nums">
              {week && ` · ${week}`} · {formatDateTime(item.created_at)}
            </span>
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

/** Needs-attention inbox (Dashboard §7, FRONTEND_REDESIGN §8.2): unseen items first (red-flag
 * items lead, in the server's order); AI suggestions come last and are labelled; seen items show
 * who saw them and when. The pregnancy week comes from the patient list already on screen. */
export function Inbox() {
  const [showSeen, setShowSeen] = useState(false)
  const inbox = useInbox(showSeen)
  const patients = usePatients()
  const weekOf = (id: string) => {
    const row = patients.data?.find((p) => p.id === id)
    return row && row.ga_weeks !== null ? gaLabel(row) : null
  }
  return (
    <section aria-labelledby="inbox-heading" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="inbox-heading">Needs attention</h2>
        <Button variant="ghost" onClick={() => setShowSeen((s) => !s)} aria-pressed={showSeen}>
          {showSeen ? 'Show unseen items' : 'Show seen items'}
        </Button>
      </div>
      {inbox.isPending ? (
        <div role="status" aria-label="Loading" className="flex flex-col gap-2">
          <TableRowSkeleton />
          <TableRowSkeleton />
        </div>
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
              <Item key={item.id} item={item} week={weekOf(item.patient_id)} />
            ))}
          </ul>
        </Card>
      )}
    </section>
  )
}

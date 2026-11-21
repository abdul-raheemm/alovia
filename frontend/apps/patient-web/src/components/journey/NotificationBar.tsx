import { Card } from '@alovia/ui'
import { Bell, ChevronRight, FileText, NotebookPen, X } from 'lucide-react'
import { Link } from 'react-router'

import { notificationTarget, notificationText } from '../../app/journey'
import { useMarkNotification, useNotifications } from '../../app/useNotifications'

// DEC-112 / owner 2026-11-21 (step 4 plan): these show as Home status cards, not in the bar
const STATUS_ICONS = { doctor_note: NotebookPen, result_available: FileText } as const
const isStatus = (type: string) => type in STATUS_ICONS

/** §4.2 notification bar at the top of the home screen: unread notifications; tapping one
 * opens its target (and marks it read); each can be dismissed. Never blocks the home: while
 * loading or on an error it shows nothing. */
export function NotificationBar() {
  const notifications = useNotifications()
  const mark = useMarkNotification()
  const items = (notifications.data ?? []).filter((n) => !isStatus(n.type))
  if (items.length === 0) return null
  return (
    <section aria-label="Notifications" className="flex flex-col gap-2">
      <ul className="flex flex-col gap-2">
        {items.map((n) => {
          const text = notificationText(n)
          return (
            <li
              key={n.id}
              className="flex items-center gap-2 rounded-md border border-border bg-surface pl-3"
            >
              <Bell aria-hidden="true" className="size-5 shrink-0 text-primary" />
              <Link
                to={notificationTarget(n)}
                onClick={() => mark.mutate({ id: n.id, action: 'read' })}
                className="flex min-h-11 flex-1 items-center py-2"
              >
                {text}
              </Link>
              <button
                type="button"
                aria-label={`Dismiss: ${text}`}
                onClick={() => mark.mutate({ id: n.id, action: 'dismiss' })}
                className="flex size-11 shrink-0 items-center justify-center rounded-md text-muted hover:bg-primary-soft"
              >
                <X aria-hidden="true" className="size-5" />
              </button>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/** Home status cards (FRONTEND_REDESIGN §7.1 row 11): a new doctor note or result while its
 * notification is unread. Opening one marks it read, like the bar. */
export function StatusCards() {
  const notifications = useNotifications()
  const mark = useMarkNotification()
  const items = (notifications.data ?? []).filter((n) => isStatus(n.type))
  return items.map((n) => {
    const Icon = STATUS_ICONS[n.type as keyof typeof STATUS_ICONS]
    return (
      <Card key={n.id} className="p-0">
        <Link
          to={notificationTarget(n)}
          onClick={() => mark.mutate({ id: n.id, action: 'read' })}
          className="flex min-h-14 items-center gap-3 p-4 font-semibold no-underline"
        >
          <Icon aria-hidden="true" className="size-6 shrink-0 text-primary" />
          <span className="flex-1">{notificationText(n)}</span>
          <ChevronRight aria-hidden="true" className="size-5 shrink-0 text-muted" />
        </Link>
      </Card>
    )
  })
}

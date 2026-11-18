import { userMessage, type JourneyHome } from '@alovia/shared'
import { Button, Card, ErrorState } from '@alovia/ui'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'

import { messageText } from '../../app/journey'
import { api } from '../../app/services'
import { HOME_KEY } from '../../app/useJourneyHome'
import { NotificationBar } from './NotificationBar'

/** Home after a pregnancy has ended (Journey §11.3-11.6): a quiet page, no baby imagery and
 * no animation. Loss / not specified: support and safety messages (§11.4); birth: the short
 * message and the same safety message (§11.5). Records stay reachable; undo while allowed. */
export function EndedHome({ data }: { data: JourneyHome }) {
  const ended = data.ended
  const isBirth = ended?.status === 'ended_birth'
  return (
    <section className="flex flex-col gap-6">
      <h1 className="sr-only">Home</h1>
      <NotificationBar />
      {ended && (
        <Card className="flex flex-col gap-3">
          <p>
            {messageText(data.messages, isBirth ? 'msg_birth_congratulations' : 'msg_loss_support')}
          </p>
          {!isBirth && <Helplines helplines={data.helplines ?? []} />}
        </Card>
      )}
      {ended && (
        <p className="rounded-md border border-caution/40 bg-caution/10 p-3">
          {messageText(data.messages, 'msg_after_pregnancy_danger_signs')}
        </p>
      )}
      <section aria-labelledby="records-heading" className="flex flex-col gap-3">
        <h2 id="records-heading">My records</h2>
        {/* §11.3: appointments and doctor notes stay available. TODO(Phases 3-5): symptom
            history and results join this list. */}
        <Card>
          <ul className="flex flex-col gap-2">
            <li>
              <Link to="/appointments">Appointments</Link>
            </li>
            <li>
              <Link to="/doctor-notes">Doctor notes</Link>
            </li>
          </ul>
        </Card>
      </section>
      {ended?.undo_until && <UndoCard />}
    </section>
  )
}

/** §11.6 "I marked this by mistake", available for resume_window_days. */
function UndoCard() {
  const queryClient = useQueryClient()
  const [asking, setAsking] = useState(false)
  const undo = useMutation({
    mutationFn: () => api.post<JourneyHome>('/patient/pregnancy-end/undo', {}),
    onSuccess: async (data) => {
      queryClient.setQueryData(HOME_KEY, data)
      await queryClient.invalidateQueries({ queryKey: ['notifications'] })
      await queryClient.invalidateQueries({ queryKey: ['journey-calendar'] })
    },
  })
  return (
    <Card className="flex flex-col items-start gap-3">
      {undo.isError && <ErrorState message={userMessage(undo.error, 'patient')} />}
      {asking ? (
        <div role="alertdialog" aria-label="Undo this change?" className="flex flex-col gap-3">
          <p className="font-semibold">Undo this change?</p>
          <div className="flex flex-wrap gap-3">
            <Button loading={undo.isPending} onClick={() => undo.mutate()}>
              Yes, undo
            </Button>
            <Button variant="secondary" onClick={() => setAsking(false)}>
              Keep it
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="secondary" onClick={() => setAsking(true)}>
          I marked this by mistake
        </Button>
      )}
    </Card>
  )
}

/** §11.4 support helplines (§13.3): only numbers copied from an official page, with it named. */
function Helplines({ helplines }: { helplines: NonNullable<JourneyHome['helplines']> }) {
  if (helplines.length === 0) return null
  const source = helplines[0]
  return (
    <div className="flex flex-col gap-2">
      <ul className="flex flex-col gap-1">
        {helplines.map((h) => (
          <li key={h.label}>
            {h.label}:{' '}
            {h.numbers.map((n, i) => (
              <span key={n}>
                {i > 0 && ', '}
                <a href={`tel:${n}`} className="font-semibold">
                  {n}
                </a>
              </span>
            ))}
          </li>
        ))}
      </ul>
      {source && (
        <p className="text-sm text-muted">
          Source:{' '}
          <a href={source.source_url} target="_blank" rel="noreferrer">
            {source.source_title}
          </a>
        </p>
      )}
    </div>
  )
}

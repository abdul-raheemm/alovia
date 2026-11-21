import { Button, Card, cn } from '@alovia/ui'
import { Phone } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { messageText } from '../../app/journey'
import {
  adviceParts,
  adviceText,
  LEVEL_HEADING,
  type HelplineKey,
  type Level,
} from '../../app/symptoms'
import { SYMPTOM_BUNDLE } from '../../app/symptomBundle.generated'
import { useJourneyHome } from '../../app/useJourneyHome'
import { Helplines } from '../journey/EndedHome'

/** An official phone number with its source (§11.3), tap to call. Bundled, so it shows even
 * when the backend is down. */
export function SymptomHelpline({ which }: { which: HelplineKey }) {
  const h = SYMPTOM_BUNDLE.helplines[which]
  return (
    <div className="flex flex-col gap-1">
      <p className="flex flex-wrap items-center gap-2 font-semibold">
        <Phone aria-hidden="true" className="size-5 shrink-0" />
        {h.label}:{' '}
        {h.numbers.map((n, i) => (
          <span key={n}>
            {i > 0 && ', '}
            <a href={`tel:${n}`}>{n}</a>
          </span>
        ))}
      </p>
      <p className="text-sm">
        Source:{' '}
        <a href={h.sourceUrl} target="_blank" rel="noreferrer">
          {h.sourceTitle}
        </a>
      </p>
    </div>
  )
}

/** §11.2 msg_not_monitored_live, shown on the log page and the urgent page. */
export function NotMonitoredNotice() {
  return (
    <p role="note" className="rounded-md border border-border bg-surface p-3 text-sm">
      {adviceText('msg_not_monitored_live')}
    </p>
  )
}

/** The result of a check-in (UX_FLOWS P5): L1 large and high-contrast with the emergency number
 * and "I understand", L2 and L0 calmer. No animation. Shown at once, never delayed (§11.1). */
export function AdviceScreen({
  level,
  messageKeys,
  offline = false,
  onDone,
}: {
  level: Level
  messageKeys: readonly string[]
  offline?: boolean
  onDone: () => void
}) {
  const heading = useRef<HTMLHeadingElement>(null)
  useEffect(() => heading.current?.focus(), [])
  const { main, extra } = adviceParts(messageKeys)
  return (
    <section className="flex flex-col gap-4">
      <Card
        role={level === 'L0' ? 'status' : 'alert'}
        className={cn(
          'flex flex-col gap-4',
          level === 'L1' && 'border-2 border-urgent bg-urgent/10',
          level === 'L2' && 'border-2 border-caution bg-caution/10',
        )}
      >
        <h1
          ref={heading}
          tabIndex={-1}
          className={cn(
            'font-sans',
            level === 'L1' && 'text-3xl text-urgent',
            level === 'L2' && 'text-caution',
          )}
        >
          {LEVEL_HEADING[level]}
        </h1>
        <p className={cn(level === 'L1' && 'text-lg')}>{adviceText(main)}</p>
        {level === 'L1' && <SymptomHelpline which="emergency" />}
        {offline && (
          <p className="text-sm">
            We could not reach Alovia right now. Your answer will be sent when the connection is
            back.
          </p>
        )}
      </Card>
      {extra.map((key) => (
        <Card key={key} className="flex flex-col gap-3">
          <p>{adviceText(key)}</p>
          {key === 'msg_mood_support' && <SymptomHelpline which="mental_health" />}
        </Card>
      ))}
      <Button className="self-start" onClick={onDone}>
        {level === 'L1' ? 'I understand' : 'Done'}
      </Button>
    </section>
  )
}

/** DEC-064: after the pregnancy has ended, the log and urgent pages show the after-pregnancy
 * safety message and helplines instead of the pregnancy form (postpartum is out of scope). */
export function AfterEndNotice({ title }: { title: string }) {
  const home = useJourneyHome()
  return (
    <section className="flex flex-col gap-4">
      <h1 className="font-sans">{title}</h1>
      <Card className="flex flex-col gap-3 border-2 border-caution bg-caution/10">
        <p>
          {home.data
            ? messageText(home.data.messages, 'msg_after_pregnancy_danger_signs')
            : adviceText('msg_after_pregnancy_danger_signs')}
        </p>
        {home.data ? (
          <Helplines helplines={home.data.helplines ?? []} />
        ) : (
          <SymptomHelpline which="emergency" /> // bundled: works even when the backend is down
        )}
      </Card>
    </section>
  )
}

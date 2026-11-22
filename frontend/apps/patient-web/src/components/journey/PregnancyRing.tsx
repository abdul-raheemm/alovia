import { animate, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState, type PointerEvent } from 'react'

import { illustrationAlt, illustrationSrc } from '../../app/journey'
import { angleOf, arcAngles, arcPath, dayAtPoint, MAX_DAY, pointAt } from '../../app/ring'

const R = 140
const STROKE = 22
const ARC_COLOURS = ['var(--color-arc-1)', 'var(--color-arc-2)', 'var(--color-arc-3)']
const RING_LABEL =
  'Pregnancy ring in three parts: first trimester weeks 0 to 13, second trimester weeks 14 to 27, third trimester weeks 28 to 42.'

/** The pregnancy ring (FRONTEND_REDESIGN §7.2, §7.3). Drag the "Wk" marker to preview any week
 * from 0 to 42; nothing is saved (§11 rule 2). The marker is hidden from screen readers and the
 * keyboard (the drag-only exception, PRODUCT.md); every fact is also real text in the headline.
 * The month image always shows today's month, never the previewed one. */
export function PregnancyRing({
  today,
  previewDay,
  onPreview,
  month,
}: {
  today: number
  previewDay: number
  onPreview: (day: number) => void
  month: number
}) {
  const svg = useRef<SVGSVGElement>(null)
  const [dragging, setDragging] = useState(false)
  const reduceMotion = useReducedMotion()
  // §5.4: when the marker moves without a drag ("Back to today") it glides on a short spring;
  // the text above changes at once (§11 rule 10). No spring with reduced motion.
  const [shownDay, setShownDay] = useState(previewDay)
  const shown = useRef(previewDay)
  useEffect(() => {
    if (dragging || reduceMotion) return
    const glide = animate(shown.current, previewDay, {
      type: 'spring',
      stiffness: 400,
      damping: 40,
      onUpdate: (v) => {
        shown.current = v
        setShownDay(v)
      },
    })
    return () => glide.stop()
  }, [previewDay, dragging, reduceMotion])
  const t = (dragging || reduceMotion ? previewDay : shownDay) / 7

  function dayFor(e: PointerEvent) {
    const box = svg.current?.getBoundingClientRect()
    if (!box) return previewDay
    const scale = 320 / box.width
    return dayAtPoint(
      (e.clientX - box.left) * scale,
      (e.clientY - box.top) * scale,
      160,
      160,
      previewDay,
    )
  }
  function release() {
    shown.current = previewDay // the marker stays where the finger let go
    setShownDay(previewDay)
    setDragging(false)
  }
  function move(e: PointerEvent) {
    if (!dragging) return
    const day = dayFor(e)
    if (day === previewDay) return
    // §7.2 haptics: one short pulse per day change, only where supported, never with reduced motion
    if (!reduceMotion && 'vibrate' in navigator) navigator.vibrate(8)
    onPreview(day)
  }

  const [mx, my] = pointAt(angleOf(t), R)
  const [tx, ty] = pointAt(angleOf(today / 7), R)
  return (
    <div
      className="relative mx-auto aspect-square w-full max-w-[300px] lg:max-w-[340px]"
      data-dragging={dragging || undefined}
    >
      <svg
        ref={svg}
        viewBox="0 0 320 320"
        role="img"
        aria-label={RING_LABEL}
        className="absolute inset-0 size-full overflow-visible"
      >
        {([0, 1, 2] as const).map((i) => {
          const [a, b] = arcAngles(i)
          const elapsedEnd = Math.min(b, angleOf(Math.min(today, MAX_DAY) / 7))
          return (
            <g key={i}>
              {/* weeks still to come: same colour at 35 percent (decorative) */}
              <path
                d={arcPath(a, b, R)}
                stroke={ARC_COLOURS[i]}
                strokeOpacity={0.35}
                strokeWidth={STROKE}
                fill="none"
              />
              {elapsedEnd > a && (
                <path
                  d={arcPath(a, elapsedEnd, R)}
                  stroke={ARC_COLOURS[i]}
                  strokeWidth={STROKE}
                  fill="none"
                />
              )}
            </g>
          )
        })}
        {/* today dot: stays at today while the marker is dragged away */}
        <circle
          cx={tx}
          cy={ty}
          r={5}
          fill="var(--color-primary)"
          stroke="var(--color-surface)"
          strokeWidth={2}
        />
        <g
          data-ring-marker=""
          aria-hidden="true"
          onPointerDown={(e) => {
            e.currentTarget.setPointerCapture(e.pointerId)
            setDragging(true)
          }}
          onPointerMove={move}
          onPointerUp={release}
          onPointerCancel={release}
          className="cursor-grab touch-none active:cursor-grabbing"
        >
          {/* 44 px bubble; surface + text tokens (a checked pair in both themes) */}
          <circle
            cx={mx}
            cy={my}
            r={23}
            fill="var(--color-surface)"
            stroke="var(--color-primary)"
            strokeWidth={2}
          />
          <text
            x={mx}
            y={my}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={14}
            fontWeight={700}
            fill="var(--color-text)"
            className="pointer-events-none select-none tabular-nums"
          >
            Wk {Math.floor(previewDay / 7)}
          </text>
        </g>
      </svg>
      {/* centre: today's month image on a disc (white in dark mode too: the artwork has a white
          background and is never inverted, §7.3 "Fit"), and the caption, always today's month */}
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2">
        <div
          key={month}
          className="ring-fade aspect-square w-[47%] overflow-hidden rounded-full bg-surface dark:bg-white"
        >
          <img
            src={illustrationSrc(month)}
            alt={illustrationAlt(month)}
            width={160}
            height={160}
            className="ring-float size-full object-contain p-[6%]"
          />
        </div>
        <p className="text-sm font-semibold">Month {month} · now</p>
      </div>
    </div>
  )
}

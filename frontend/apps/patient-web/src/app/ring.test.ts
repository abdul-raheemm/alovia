import { describe, expect, it } from 'vitest'

import {
  angleOf,
  arcAngles,
  dayAtPoint,
  GAP_DEG,
  MAX_DAY,
  monthOfWeek,
  todayDay,
  trimesterOf,
  weekStartDate,
  weeksAt,
} from './ring'

const MONTHS = (
  [
    [1, 0, 4],
    [2, 5, 8],
    [3, 9, 13],
    [4, 14, 17],
    [5, 18, 22],
    [6, 23, 27],
    [7, 28, 31],
    [8, 32, 35],
    [9, 36, 42],
  ] as [number, number, number][]
).map(([month, week_start, week_end]) => ({ month, week_start, week_end }))

/** A pointer on the ring at an angle (degrees clockwise from 12 o'clock), centre (160, 160). */
function pointer(angle: number): [number, number] {
  const rad = (angle * Math.PI) / 180
  return [160 + 140 * Math.sin(rad), 160 - 140 * Math.cos(rad)]
}

describe('ring geometry (FRONTEND_REDESIGN §7.2)', () => {
  it('three arcs of 14, 14 and 15 week slots with 3 degree gaps fill the circle', () => {
    const [[a0, b0], [a1, b1], [a2, b2]] = [arcAngles(0), arcAngles(1), arcAngles(2)]
    expect(a0).toBeCloseTo(GAP_DEG / 2)
    expect(a1 - b0).toBeCloseTo(GAP_DEG)
    expect(a2 - b1).toBeCloseTo(GAP_DEG)
    expect(360 - b2 + a0).toBeCloseTo(GAP_DEG) // gap at 12 o'clock
    expect(b1 - a1).toBeCloseTo(b0 - a0)
    expect((b2 - a2) / (b0 - a0)).toBeCloseTo(15 / 14)
  })

  it('trimesters: weeks 0-13, 14-27, 28-42', () => {
    expect([0, 13.9, 14, 27.9, 28, 42].map(trimesterOf)).toEqual([0, 0, 1, 1, 2, 2])
  })

  it('angle and weeks are inverse inside the arcs', () => {
    for (const t of [0, 5.5, 13.5, 14, 20, 27.9, 28, 35, 42]) {
      expect(weeksAt(angleOf(t))).toBeCloseTo(t)
    }
  })

  it('an angle inside a gap snaps to the nearer arc end', () => {
    const [, end0] = arcAngles(0)
    const [start1] = arcAngles(1)
    expect(weeksAt(end0 + 1)).toBeCloseTo(14) // end of arc 1 = week 14
    expect(weeksAt(start1 - 1)).toBeCloseTo(14)
  })

  it('a pointer on the ring gives the day; the marker stops at both ends', () => {
    expect(dayAtPoint(...pointer(angleOf(24)), 160, 160, 160)).toBe(168)
    // just left of 12 o'clock is the 42-week end side; coming from week 1 it stays at day 0
    expect(dayAtPoint(...pointer(359), 160, 160, 7)).toBe(0)
    // and just right of 12 o'clock, coming from week 41, it stays at the end
    expect(dayAtPoint(...pointer(1), 160, 160, 41 * 7)).toBe(MAX_DAY)
    // nothing past 42 weeks
    expect(dayAtPoint(...pointer(358), 160, 160, MAX_DAY)).toBe(MAX_DAY)
  })

  it("today's day comes from the home data and is held at 42 weeks", () => {
    expect(todayDay({ completed_weeks: 24, days: 3 })).toBe(171)
    expect(todayDay({ completed_weeks: 44, days: 2 })).toBe(MAX_DAY)
  })

  it('week start date: due date minus 280 days plus 7 per week (the backend rule)', () => {
    expect(weekStartDate('2027-03-01', 40)).toBe('2027-03-01')
    expect(weekStartDate('2027-03-01', 0)).toBe('2026-05-25') // the LMP for this due date
    expect(weekStartDate('2027-03-01', 30)).toBe('2026-12-21')
  })

  it('the month for a week comes from the served month map', () => {
    expect(monthOfWeek(MONTHS, 30)).toBe(7)
    expect(monthOfWeek(MONTHS, 4)).toBe(1)
    expect(monthOfWeek(MONTHS, 42)).toBe(9)
  })
})

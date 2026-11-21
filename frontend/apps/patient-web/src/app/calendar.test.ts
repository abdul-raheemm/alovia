import { describe, expect, it } from 'vitest'

import {
  appointmentWhen,
  clampMonth,
  formatTime,
  isoDay,
  milestoneLabel,
  monthBounds,
  parseDay,
  weekDays,
} from './journey'
import { markerWords, pregnancyWeekOn, warningLevel } from '../components/journey/CalendarMarkers'

describe('calendar helpers', () => {
  it('round-trips local days without a time zone shift', () => {
    expect(isoDay(parseDay('2027-03-01'))).toBe('2027-03-01')
    expect(isoDay(new Date(2026, 11, 31, 23, 59))).toBe('2026-12-31')
  })

  it('gives the first and last day of a month, including February and leap years', () => {
    expect(monthBounds(new Date(2027, 1, 14))).toEqual({ from: '2027-02-01', to: '2027-02-28' })
    expect(monthBounds(new Date(2028, 1, 1))).toEqual({ from: '2028-02-01', to: '2028-02-29' })
    expect(monthBounds(new Date(2026, 11, 31))).toEqual({ from: '2026-12-01', to: '2026-12-31' })
  })

  it('builds the Sunday-to-Saturday week around a day, across a month end', () => {
    const days = weekDays(new Date(2026, 11, 31)).map(isoDay) // a Thursday
    expect(days).toEqual([
      '2026-12-27',
      '2026-12-28',
      '2026-12-29',
      '2026-12-30',
      '2026-12-31',
      '2027-01-01',
      '2027-01-02',
    ])
  })

  it('keeps the shown month inside the navigation range (spec 9.1)', () => {
    const start = '2026-05-10'
    const end = '2027-02-28'
    expect(isoDay(clampMonth(new Date(2026, 2, 5), start, end))).toBe('2026-05-01')
    expect(isoDay(clampMonth(new Date(2027, 5, 5), start, end))).toBe('2027-02-01')
    expect(isoDay(clampMonth(new Date(2026, 8, 17), start, end))).toBe('2026-09-01')
    expect(isoDay(clampMonth(new Date(2026, 8, 17), null, null))).toBe('2026-09-01')
  })

  it('formats local times and appointment moments', () => {
    expect(formatTime('14:30:00')).toBe('2:30 pm')
    expect(formatTime('09:05')).toBe('9:05 am')
    expect(appointmentWhen({ date: '2027-03-01', time: '10:30:00' })).toBe('1 March 2027, 10:30 am')
    expect(appointmentWhen({ date: '2027-03-01', time: null })).toBe('1 March 2027')
  })

  it('labels every milestone kind (spec 6.4)', () => {
    expect(milestoneLabel({ kind: 'new_week', value: 12 })).toBe('Week 12 begins')
    expect(milestoneLabel({ kind: 'new_month', value: 4 })).toBe('Month 4 begins')
    expect(milestoneLabel({ kind: 'new_trimester', value: 2 })).toBe('Trimester 2 begins')
    expect(milestoneLabel({ kind: 'term', value: 37 })).toBe('37 weeks')
    expect(milestoneLabel({ kind: 'due_date', value: 0 })).toBe('Due date')
  })
})

describe('calendar markers (FRONTEND_REDESIGN §7.6)', () => {
  const day = (levels: string[]) => ({ milestones: [], appointments: [], suggested: [], levels })

  it('names the highest warning level of a day; L1 wins over L2', () => {
    expect(warningLevel(day(['L0']))).toBeNull()
    expect(warningLevel(day(['L0', 'L2']))).toBe('L2')
    expect(warningLevel(day(['L2', 'L1']))).toBe('L1')
    expect(markerWords(day(['L0', 'L2']))).toBe(', symptoms logged, Level 2 warning logged')
  })

  it('counts the pregnancy week of a day from the pregnancy start (rows = weeks)', () => {
    expect(pregnancyWeekOn('2026-05-04', '2026-05-04')).toBe(0)
    expect(pregnancyWeekOn('2026-05-04', '2026-05-10')).toBe(0)
    expect(pregnancyWeekOn('2026-05-04', '2026-05-11')).toBe(1)
    expect(pregnancyWeekOn('2026-05-04', '2026-11-23')).toBe(29)
    expect(pregnancyWeekOn('2026-05-04', '2026-05-01')).toBe(-1) // before the start
  })
})

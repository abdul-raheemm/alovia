import { describe, expect, it } from 'vitest'

import { dateRuleText, formatDay, messageText, PENDING_TEXT, weeksLabel } from './journey'

const pregnancy = {
  completed_weeks: 24,
  days: 3,
  days_to_go: 104,
  content_week: 24,
  trimester: 2,
  month: 6,
  is_estimate: true,
}

describe('journey helpers', () => {
  it('writes the header as "N weeks, D days pregnant" and stops at 42 (spec 4.3, 4.5)', () => {
    expect(weeksLabel(pregnancy)).toBe('24 weeks, 3 days pregnant')
    expect(weeksLabel({ ...pregnancy, completed_weeks: 1, days: 1 })).toBe('1 week, 1 day pregnant')
    expect(weeksLabel({ ...pregnancy, completed_weeks: 0, days: 0 })).toBe(
      '0 weeks, 0 days pregnant',
    )
    expect(weeksLabel({ ...pregnancy, completed_weeks: 42, days: 0 })).toBe('42 weeks pregnant')
    expect(weeksLabel({ ...pregnancy, completed_weeks: 44, days: 5 })).toBe('42 weeks pregnant')
  })

  it('formats calendar days without shifting them across time zones', () => {
    expect(formatDay('2027-03-01')).toBe('1 March 2027')
    expect(formatDay('2026-12-31')).toBe('31 December 2026')
  })

  it('shows the placeholder until a doctor approves a message (DEC-041)', () => {
    expect(messageText({ msg_onboarding: null }, 'msg_onboarding')).toBe(PENDING_TEXT)
    expect(messageText({}, 'msg_unknown')).toBe(PENDING_TEXT)
    expect(messageText({ msg_onboarding: 'Approved text' }, 'msg_onboarding')).toBe('Approved text')
  })

  it('maps date rule codes to field messages', () => {
    expect(dateRuleText(undefined)).toBeUndefined()
    expect(dateRuleText('D1')).toBe("This date can't be in the future.")
    expect(dateRuleText('D2')).toBe('Please check this date, or talk to your doctor.')
    expect(dateRuleText('D3')).toBe('Enter a pregnancy age between 0 and 42 weeks.')
  })
})

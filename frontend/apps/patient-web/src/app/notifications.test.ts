import { describe, expect, it } from 'vitest'

import { notificationTarget, notificationText } from './journey'

describe('notification helpers (spec 10.1)', () => {
  it('words week and month notices with their number', () => {
    expect(notificationText({ type: 'new_week', target_ref: '25' })).toBe('Week 25 has started')
    expect(notificationText({ type: 'new_month', target_ref: '7' })).toBe('Month 7 has started')
  })

  it('sends each type to its target', () => {
    expect(notificationTarget({ type: 'new_week', target_ref: '25' })).toBe('/home')
    expect(notificationTarget({ type: 'new_month', target_ref: '7' })).toBe('/months/7')
    expect(notificationTarget({ type: 'appointment_soon', target_ref: 'x' })).toBe('/appointments')
    expect(notificationTarget({ type: 'doctor_note', target_ref: 'x' })).toBe('/doctor-notes')
    expect(notificationTarget({ type: 'dates_updated', target_ref: null })).toBe('/dates')
    expect(notificationTarget({ type: 'result_available', target_ref: 'x' })).toBe('/results')
  })

  it('has calm wording for every type, with no exclamation marks', () => {
    const types = [
      'new_week',
      'new_month',
      'appointment_soon',
      'doctor_note',
      'result_available',
      'genetic_reviewed',
      'dates_updated',
    ]
    for (const type of types) expect(notificationText({ type, target_ref: '1' })).not.toMatch(/!/)
  })
})

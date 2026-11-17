import { ApiError, type Me } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { patientGateStep } from './gate'

const V = '2026-11-v1'
const forbidden = new ApiError(403, 'FORBIDDEN', 'Your account is not set up yet.')

function me(role: string, accepted: boolean): Me {
  return {
    user: { id: 'u', email: 'p@example.test', role },
    patient: role === 'patient' ? { id: 'p', name: 'Test Patient 1' } : null,
    doctor: null,
    consent: { current_version: V, accepted },
  }
}

const base = { pendingCode: null, pendingConsentVersion: null, currentConsentVersion: V }

describe('patientGateStep (UX_FLOWS P1, DEC-036)', () => {
  it('waits while /me is loading', () => {
    expect(patientGateStep({ ...base, me: undefined, meError: null })).toBe('loading')
  })
  it('links the invite when there is no account yet and a code is waiting', () => {
    expect(
      patientGateStep({ ...base, me: undefined, meError: forbidden, pendingCode: 'ABCD2345' }),
    ).toBe('link')
  })
  it('explains when there is no account and no invite code', () => {
    expect(patientGateStep({ ...base, me: undefined, meError: forbidden })).toBe('not-set-up')
  })
  it('shows an error state for other failures', () => {
    const down = new ApiError(503, 'SERVICE_UNAVAILABLE', '')
    expect(patientGateStep({ ...base, me: undefined, meError: down })).toBe('error')
  })
  it('sends doctors and admins away from the patient app', () => {
    expect(patientGateStep({ ...base, me: me('doctor', true), meError: null })).toBe('wrong-app')
    expect(patientGateStep({ ...base, me: me('admin', true), meError: null })).toBe('wrong-app')
  })
  it('records consent ticked at sign-up only for the current version', () => {
    const m = me('patient', false)
    expect(patientGateStep({ ...base, me: m, meError: null, pendingConsentVersion: V })).toBe(
      'consent-auto',
    )
    expect(patientGateStep({ ...base, me: m, meError: null, pendingConsentVersion: 'old' })).toBe(
      'consent-form',
    )
    expect(patientGateStep({ ...base, me: m, meError: null })).toBe('consent-form')
  })
  it('lets a linked patient with consent in', () => {
    expect(patientGateStep({ ...base, me: me('patient', true), meError: null })).toBe('ready')
  })
})

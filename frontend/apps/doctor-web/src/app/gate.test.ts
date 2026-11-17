import { ApiError, type Me } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { doctorGateStep } from './gate'

function me(role: string): Me {
  return {
    user: { id: 'u', email: 'd@example.test', role },
    patient: null,
    doctor: null,
    consent: { current_version: '2026-11-v1', accepted: false },
  }
}

describe('doctorGateStep', () => {
  it('lets doctors and admins in, keeps patients out', () => {
    expect(doctorGateStep(me('doctor'), null)).toBe('ready')
    expect(doctorGateStep(me('admin'), null)).toBe('ready')
    expect(doctorGateStep(me('patient'), null)).toBe('wrong-app')
  })
  it('explains a missing account and shows other errors', () => {
    expect(doctorGateStep(undefined, new ApiError(403, 'FORBIDDEN', ''))).toBe('not-set-up')
    expect(doctorGateStep(undefined, new ApiError(503, 'SERVICE_UNAVAILABLE', ''))).toBe('error')
    expect(doctorGateStep(undefined, null)).toBe('loading')
  })
})

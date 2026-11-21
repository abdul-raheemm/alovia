import { afterEach, describe, expect, it } from 'vitest'

import { clearAllDrafts, clearDraft, loadDraft, saveDraft } from './logDraft'

const DRAFT = {
  warning: { fits: true },
  drafts: { fatigue: { severity: 'mild', flags: {}, puqe: [] } },
}
const T0 = 1_700_000_000_000
const MIN = 60_000

describe('Log draft (DEC-109)', () => {
  afterEach(() => localStorage.clear())

  it('is restored within the time to live', () => {
    saveDraft('p1', DRAFT, T0)
    expect(loadDraft('p1', 30, T0 + 30 * MIN)).toEqual({ ...DRAFT, savedAt: T0 })
  })

  it('is dropped and removed after the time to live', () => {
    saveDraft('p1', DRAFT, T0)
    expect(loadDraft('p1', 30, T0 + 30 * MIN + 1)).toBeNull()
    expect(localStorage.length).toBe(0)
  })

  it('belongs to one patient only', () => {
    saveDraft('p1', DRAFT, T0)
    expect(loadDraft('p2', 30, T0)).toBeNull()
  })

  it('is cleared for one patient, and for everyone on sign-out', () => {
    saveDraft('p1', DRAFT, T0)
    saveDraft('p2', DRAFT, T0)
    localStorage.setItem('alovia-theme', 'dark')
    clearDraft('p1')
    expect(loadDraft('p1', 30, T0)).toBeNull()
    clearAllDrafts()
    expect(loadDraft('p2', 30, T0)).toBeNull()
    expect(localStorage.getItem('alovia-theme')).toBe('dark') // other settings stay
  })

  it('ignores a broken stored value', () => {
    localStorage.setItem('alovia-log-draft:p1', '{not json')
    expect(loadDraft('p1', 30, T0)).toBeNull()
  })
})

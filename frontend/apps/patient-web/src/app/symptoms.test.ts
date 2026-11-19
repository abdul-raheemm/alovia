import { ApiError, type SymptomVocabulary } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { PENDING_TEXT } from './journey'
import {
  adviceParts,
  adviceText,
  cannotReach,
  emptyDraft,
  entryError,
  byWeek,
  LEVEL_HEADING,
  missingFields,
  offlineWarnings,
  toEntry,
} from './symptoms'

type CommonSymptom = SymptomVocabulary['common'][number]
const spec = (over: Partial<CommonSymptom>): CommonSymptom => ({
  id: 'test',
  label: 'Test',
  puqe: false,
  flags: {},
  severity: false,
  duration: false,
  ...over,
})

describe('symptom helpers', () => {
  it('uses the spec level names and pending advice text (DEC-061)', () => {
    expect(LEVEL_HEADING).toEqual({
      L1: 'Go to hospital now',
      L2: 'Contact your doctor today',
      L0: 'Saved',
    })
    expect(adviceText('msg_level1_go_now')).toBe(PENDING_TEXT)
    expect(adviceText('unknown_key')).toBe(PENDING_TEXT)
  })

  it('offers week-gated warning signs from their week, or all when the week is unknown', () => {
    const ids = (week: number | null) => offlineWarnings(week).map((w) => w.id)
    expect(ids(15)).not.toContain('baby_movements_reduced')
    expect(ids(16)).toContain('baby_movements_reduced')
    expect(ids(23)).not.toContain('baby_movements_never_felt')
    expect(ids(24)).toContain('baby_movements_never_felt')
    expect(ids(null)).toHaveLength(15)
  })

  it('treats no answer or a server failure as unreachable, not a validation error', () => {
    expect(cannotReach(new ApiError(0, 'NETWORK_ERROR', ''))).toBe(true)
    expect(cannotReach(new ApiError(503, 'SERVICE_UNAVAILABLE', ''))).toBe(true)
    expect(cannotReach(new ApiError(400, 'VALIDATION_ERROR', ''))).toBe(false)
    expect(cannotReach(new Error('x'))).toBe(false)
  })

  it('maps V1/V2 codes to field messages', () => {
    const fields = { 'entries.1.severity': 'V1', 'entries.0.duration': 'V2' }
    expect(entryError(fields, 1, 'severity')).toBe('Please fill this in.')
    expect(entryError(fields, 0, 'duration')).toBe('Please check this value.')
    expect(entryError(fields, 0, 'severity')).toBeUndefined()
  })

  it('lists missing required details and builds an entry with only the asked fields', () => {
    const headache = spec({
      id: 'headache',
      severity: true,
      duration: true,
      flags: { with_swelling: 'With swelling' },
    })
    const draft = { ...emptyDraft(), severity: 'mild' }
    expect(missingFields(headache, draft)).toEqual(['duration'])
    const done = {
      ...draft,
      duration: 'under_1_hour',
      flags: { with_swelling: true },
      notes: '  ',
    }
    expect(toEntry(headache, done)).toEqual({
      symptom: 'headache',
      severity: 'mild',
      duration: 'under_1_hour',
      with_swelling: true,
    })
    const nausea = spec({ id: 'nausea_vomiting', puqe: true })
    expect(missingFields(nausea, { ...emptyDraft(), puqe: [1, 2, undefined] })).toEqual([
      'puqe_answers',
    ])
    const craving = spec({
      id: 'food_craving',
      text: { field: 'food', label: 'Which food', required: false, max_length: 100 },
    })
    expect(missingFields(craving, emptyDraft())).toEqual([])
    expect(toEntry(craving, { ...emptyDraft(), text: ' Test ' })).toEqual({
      symptom: 'food_craving',
      food: 'Test',
    })
  })
})

describe('history grouping (spec 4.3)', () => {
  it('counts entries per pregnancy week by severity and duration, unknown week last', () => {
    const rows = byWeek([
      { pregnancy_week: 25, severity: 'mild', duration: 'under_1_hour' },
      { pregnancy_week: 24, severity: 'severe', duration: 'under_1_hour' },
      { pregnancy_week: 24, severity: 'severe', duration: 'more_than_1_day' },
      { pregnancy_week: null, severity: null, duration: null },
      { pregnancy_week: 24, severity: null, duration: null },
    ])
    expect(rows.map((r) => [r.week, r.total, r.severe, r.mild, r.logged])).toEqual([
      ['Week 24', 3, 2, 0, 1],
      ['Week 25', 1, 0, 1, 0],
      ['Week unknown', 1, 0, 0, 1],
    ])
    expect(rows[0]?.durations).toEqual({ under_1_hour: 1, more_than_1_day: 1 })
  })
})

describe('advice parts (spec 11.2, V3)', () => {
  it('uses the level message as the advice and lists the others after it', () => {
    expect(adviceParts(['msg_level2_contact_today', 'msg_mood_support'])).toEqual({
      main: 'msg_level2_contact_today',
      extra: ['msg_mood_support'],
    })
  })
  it('shows the safe-fallback message as the advice when the engine failed (V3)', () => {
    expect(adviceParts(['msg_safe_fallback'])).toEqual({ main: 'msg_safe_fallback', extra: [] })
  })
})

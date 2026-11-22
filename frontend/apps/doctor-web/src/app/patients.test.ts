import type { PatientRow } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { patientErrors, toPatientInput } from '../components/PatientForm'
import {
  filterPatients,
  gaLabel,
  geneticLabel,
  inboxTab,
  NO_FILTERS,
  pageOf,
  sortPatients,
} from './patients'

const AT = '2026-11-19T05:00:00Z'

function row(over: Partial<PatientRow>): PatientRow {
  return {
    id: crypto.randomUUID(),
    name: 'Test',
    linked: true,
    ga_weeks: null,
    ga_days: null,
    due_date: null,
    fetal: null,
    maternal: null,
    genetic: null,
    symptom: null,
    unseen_count: 0,
    pregnancy_status: 'active',
    group: 4,
    ...over,
  }
}

describe('patient list filters (§6)', () => {
  const rows = [
    row({
      name: 'Asha Rao',
      fetal: { predicted_class: 'Suspect', created_at: AT },
      unseen_count: 2,
    }),
    row({ name: 'Bina', maternal: { predicted_class: 'High', created_at: AT } }),
    row({
      name: 'Chitra',
      pregnancy_status: 'ended_birth',
      genetic: { review_status: 'pending_review', priority: 'high', created_at: AT },
      symptom: { level: 'L1', created_at: AT },
    }),
  ]
  const names = (f: Partial<typeof NO_FILTERS>) =>
    filterPatients(rows, { ...NO_FILTERS, ...f }).map((r) => r.name)

  it('keeps the server order with no filters', () => {
    expect(names({})).toEqual(['Asha Rao', 'Bina', 'Chitra'])
  })
  it('searches names, ignoring case and spaces', () => {
    expect(names({ search: '  rao ' })).toEqual(['Asha Rao'])
  })
  it('filters by each status column', () => {
    expect(names({ fetal: 'Suspect' })).toEqual(['Asha Rao'])
    expect(names({ maternal: 'High' })).toEqual(['Bina'])
    expect(names({ status: 'ended_birth' })).toEqual(['Chitra'])
    expect(names({ genetic: 'Pending review (high priority)' })).toEqual(['Chitra'])
    expect(names({ genetic: 'None' })).toEqual(['Asha Rao', 'Bina'])
    expect(names({ symptom: 'L1' })).toEqual(['Chitra'])
    expect(names({ unseenOnly: true })).toEqual(['Asha Rao'])
  })
})

describe('labels and links', () => {
  it('names the genetic status and gestational age', () => {
    expect(geneticLabel(null)).toBe('None')
    expect(geneticLabel({ review_status: 'reviewed', priority: 'high', created_at: AT })).toBe(
      'Reviewed',
    )
    expect(gaLabel({ ga_weeks: 24, ga_days: 3 })).toBe('24w 3d')
    expect(gaLabel({ ga_weeks: null, ga_days: null })).toBe('—')
  })
  it('opens the tab that shows an inbox item (§7.2)', () => {
    expect(inboxTab({ type: 'symptom_l1', ref_table: 'symptom_checkins' })).toBe('symptoms')
    expect(inboxTab({ type: 'genetic_pending', ref_table: 'genetic_assessments' })).toBe('genetic')
    expect(inboxTab({ type: 'pregnancy_ended', ref_table: 'pregnancy_date_history' })).toBe(
      'pregnancy',
    )
    expect(inboxTab({ type: 'record_uploaded', ref_table: 'medical_records' })).toBe('records')
  })
})

describe('patient form checks (§8.1, DEC-023)', () => {
  it('needs a name and an adult age when given', () => {
    expect(patientErrors({ name: ' ', age: '', notes: '' })).toHaveProperty('name')
    expect(patientErrors({ name: 'A', age: '17', notes: '' })).toHaveProperty('age')
    expect(patientErrors({ name: 'A', age: '29.5', notes: '' })).toHaveProperty('age')
    expect(patientErrors({ name: 'A', age: '', notes: '' })).toEqual({})
  })
  it('sends trimmed values and null for empty optional fields', () => {
    expect(toPatientInput({ name: ' Asha ', age: '', notes: ' ' })).toEqual({
      name: 'Asha',
      age: null,
      notes: null,
    })
    expect(toPatientInput({ name: 'A', age: '30', notes: 'n' })).toEqual({
      name: 'A',
      age: 30,
      notes: 'n',
    })
  })
})

describe('patient list sort and pages (FRONTEND_REDESIGN §8.3)', () => {
  const a = row({ name: 'Asha', ga_weeks: 30, ga_days: 1, unseen_count: 1 })
  const b = row({ name: 'bina', ga_weeks: 12, ga_days: 0, unseen_count: 3 })
  const c = row({ name: 'Chitra', ga_weeks: null, unseen_count: 0 }) // no dates yet

  it('keeps the server order without a sort', () => {
    expect(sortPatients([c, a, b], null)).toEqual([c, a, b])
  })

  it('sorts by name ignoring case, either way', () => {
    expect(sortPatients([c, b, a], { key: 'name', dir: 'asc' }).map((r) => r.name)).toEqual([
      'Asha',
      'bina',
      'Chitra',
    ])
    expect(sortPatients([a, b, c], { key: 'name', dir: 'desc' })[0]?.name).toBe('Chitra')
  })

  it('puts empty values last in both directions', () => {
    expect(sortPatients([c, a, b], { key: 'ga', dir: 'asc' }).map((r) => r.name)).toEqual([
      'bina',
      'Asha',
      'Chitra',
    ])
    expect(sortPatients([c, a, b], { key: 'ga', dir: 'desc' }).map((r) => r.name)).toEqual([
      'Asha',
      'bina',
      'Chitra',
    ])
  })

  it('pages 25 at a time and keeps the page in range', () => {
    const many = Array.from({ length: 51 }, (_, i) => i)
    expect(pageOf(many, 0)).toMatchObject({ page: 0, pages: 3 })
    expect(pageOf(many, 2).rows).toEqual([50])
    expect(pageOf(many, 9).page).toBe(2) // past the end -> last page
    expect(pageOf([], 0)).toEqual({ rows: [], page: 0, pages: 1 })
  })
})

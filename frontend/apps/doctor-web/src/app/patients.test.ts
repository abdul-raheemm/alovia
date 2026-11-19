import type { PatientRow } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { patientErrors, toPatientInput } from '../components/PatientForm'
import { filterPatients, gaLabel, geneticLabel, inboxTab, NO_FILTERS } from './patients'

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

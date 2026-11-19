import type { PredictionSchema } from '@alovia/shared'
import { describe, expect, it } from 'vitest'

import { buildInput, defaultUnits, outOfRange, shortNumber, toModelUnit } from './predictions'

const HBA1C = {
  feature: 'Blood Glucose(HbA1c mmol/mol)',
  label: 'HbA1c',
  range: { min: 20, max: 120 },
  unit: { name: 'hba1c', model_unit: 'mmol/mol', other_unit: '%', default: '%' },
}
const AGE = { feature: 'Age', label: 'Age (years)', range: { min: 15, max: 48 }, unit: null }
const SCHEMA: PredictionSchema = {
  model: 'maternal',
  groups: [{ label: 'Test', fields: [AGE, HBA1C] }],
  limitation_keys: [],
  messages: {},
  conversions: {
    hba1c: { multiply: 10.93, divide: 1, add: -23.5 },
    glucose: { multiply: 1, divide: 18, add: 0 },
    temperature: { multiply: 9, divide: 5, add: 32 },
  },
}

describe('unit preview (§9.3, §25 test 5)', () => {
  it('converts like the backend', () => {
    expect(Math.round(toModelUnit(7, '%', HBA1C, SCHEMA.conversions.hba1c))).toBe(53)
    expect(toModelUnit(53, 'mmol/mol', HBA1C, SCHEMA.conversions.hba1c)).toBe(53)
    expect(toModelUnit(30, '', AGE)).toBe(30)
    expect(shortNumber(53.009999)).toBe('53.01')
    expect(shortNumber(5)).toBe('5')
  })
  it('flags values outside the training range (§9.4)', () => {
    expect(outOfRange(AGE, 14)).toBe(true)
    expect(outOfRange(AGE, 48)).toBe(false)
  })
})

describe('form input', () => {
  it('starts each switch on its default unit and needs every number', () => {
    expect(defaultUnits(SCHEMA)).toEqual({ hba1c: '%' })
    expect(buildInput(SCHEMA, { Age: '30', [HBA1C.feature]: ' ' }, { hba1c: '%' })).toEqual({
      errors: { [HBA1C.feature]: 'Enter a number.' },
    })
    expect(buildInput(SCHEMA, { Age: '30', [HBA1C.feature]: '7.0' }, { hba1c: '%' })).toEqual({
      body: { values: { Age: 30, [HBA1C.feature]: 7 }, units: { hba1c: '%' } },
    })
  })
})

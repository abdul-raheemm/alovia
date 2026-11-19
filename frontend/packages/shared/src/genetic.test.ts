import { describe, expect, it } from 'vitest'

import {
  chanceLabel,
  emptyGeneticDraft,
  evidenceFor,
  geneticText,
  missingAnswers,
  questionFor,
  toGeneticInput,
  draftFromInputs,
  PENDING_TEXT,
} from './genetic'
import { GENETIC_BUNDLE } from './geneticBundle.generated'

describe('genetic helpers', () => {
  it('uses the spec disclaimer and pending texts', () => {
    expect(geneticText('disclaimer_main')).toBe(
      'This is for knowledge only and is not medical advice. Counselling is recommended.',
    )
    expect(geneticText('msg_needs_testing')).toBe(PENDING_TEXT)
  })

  it('fills the condition into the spec questions', () => {
    expect(questionFor(GENETIC_BUNDLE.previousChildQuestion, 'haemophilia')).toBe(
      'Has a previous child of this couple been diagnosed with haemophilia?',
    )
  })

  it('offers only the evidence allowed with the condition and status (§5.4)', () => {
    const ids = (c: 'haemoglobin_group' | 'haemophilia', s: string) =>
      evidenceFor(c, s).map(([id]) => id)
    expect(ids('haemoglobin_group', 'sickle_carrier')).toContain('sickle_status_card')
    expect(ids('haemoglobin_group', 'beta_thal_carrier')).not.toContain('sickle_status_card')
    expect(ids('haemophilia', 'carrier')).toEqual([
      'test_report',
      'doctor_told',
      'family_history_only',
    ])
    expect(evidenceFor('haemoglobin_group', 'unknown')).toEqual([])
  })

  it('starts the father at unknown except for haemophilia (D14, DEC-069)', () => {
    const d = emptyGeneticDraft()
    expect(d.haemoglobin_group.father.status).toBe('unknown')
    expect(d.marfan.father.status).toBe('unknown')
    expect(d.haemophilia.father.status).toBeUndefined()
    expect(d.haemoglobin_group.mother.status).toBeUndefined()
  })

  it('lists missing answers and sends only what was asked', () => {
    const d = emptyGeneticDraft()
    expect(missingAnswers(d)).toEqual([
      'haemoglobin_group.mother.status',
      'haemoglobin_group.previous_child',
      'haemophilia.entry',
      'marfan.entry',
      'consanguinity',
    ])
    d.haemoglobin_group.mother = { status: 'beta_thal_carrier', evidence: 'hplc_report' }
    d.haemoglobin_group.previous_child = 'no'
    d.haemophilia.entry = 'yes'
    d.marfan.entry = 'no'
    d.consanguinity = 'not_sure'
    expect(missingAnswers(d)).toEqual([
      'haemophilia.mother.status',
      'haemophilia.father.status',
      'haemophilia.previous_child',
    ])
    d.haemophilia.entry = 'no'
    expect(missingAnswers(d)).toEqual([])
    expect(toGeneticInput(d)).toEqual({
      haemoglobin_group: {
        mother: { status: 'beta_thal_carrier', evidence: 'hplc_report' },
        father: { status: 'unknown' },
        previous_child: 'no',
      },
      haemophilia: { entry: 'no' },
      marfan: { entry: 'no' },
      consanguinity: 'not_sure',
    })
  })

  it('never shows 0%', () => {
    expect(chanceLabel('1_in_4')).toBe('1 in 4 (25%)')
    expect(chanceLabel('not_expected')).toBe('not expected')
    expect(Object.values(GENETIC_BUNDLE.chances).join(' ')).not.toMatch(/\b0%/)
  })
})

describe('draftFromInputs (doctor correction, Genetic §10.3)', () => {
  it('round-trips a submitted answer set', () => {
    const input = {
      haemoglobin_group: {
        mother: { status: 'beta_thal_carrier', evidence: 'hplc_report' },
        father: { status: 'unknown' },
        previous_child: 'no',
      },
      haemophilia: { entry: 'no' },
      marfan: { entry: 'no' },
      consanguinity: 'no',
    }
    expect(toGeneticInput(draftFromInputs(input))).toEqual(input)
  })
})

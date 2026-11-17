import { describe, expect, it } from 'vitest'

import {
  CONSENT_VERSION,
  consentParts,
  fullDisclaimer,
  LEGAL_DOCS,
  parseConsentVersion,
  shortDisclaimer,
} from './legal'

describe('legal texts come straight from docs/legal', () => {
  it('reads the consent version (must match the backend, DEC-031)', () => {
    expect(CONSENT_VERSION).toBe('2026-11-v1')
    expect(() => parseConsentVersion('no version here')).toThrow()
  })

  it('splits the consent text into the body and the two checkbox labels, word for word', () => {
    const { body, checkboxes } = consentParts()
    expect(body.startsWith('**Before you continue**')).toBe(true)
    expect(body).not.toContain('- [ ]')
    expect(checkboxes).toEqual([
      'I am 18 years or older.',
      'I have read the Privacy Policy and Terms of Use, and I agree to Alovia storing and using my information as described above.',
    ])
  })

  it('finds both disclaimer texts', () => {
    expect(fullDisclaimer()).toMatch(/^Alovia is a research prototype/)
    expect(shortDisclaimer()).toBe(
      'For knowledge only — not medical advice. Please talk to your doctor.',
    )
  })

  it('has a non-empty document for every legal page', () => {
    expect(LEGAL_DOCS.map((d) => d.path)).toEqual([
      '/privacy',
      '/terms',
      '/disclaimer',
      '/cookies',
      '/consent',
    ])
    for (const doc of LEGAL_DOCS) expect(doc.source.length).toBeGreaterThan(100)
  })
})

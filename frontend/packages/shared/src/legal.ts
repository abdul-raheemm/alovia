/** Legal and credits pages are rendered straight from docs/legal, so the apps always show the
 * same text as the documents (drafts included; placeholders stay visible until filled). */
import consentText from '../../../../docs/legal/CONSENT_TEXT.md?raw'
import cookieNotice from '../../../../docs/legal/COOKIE_NOTICE.md?raw'
import credits from '../../../../docs/legal/CREDITS.md?raw'
import disclaimer from '../../../../docs/legal/MEDICAL_DISCLAIMER.md?raw'
import privacy from '../../../../docs/legal/PRIVACY_POLICY.md?raw'
import terms from '../../../../docs/legal/TERMS_OF_USE.md?raw'

export interface LegalDoc {
  path: string
  title: string
  source: string
}

export const LEGAL_DOCS: LegalDoc[] = [
  { path: '/privacy', title: 'Privacy Policy', source: privacy },
  { path: '/terms', title: 'Terms of Use', source: terms },
  { path: '/disclaimer', title: 'Medical Disclaimer', source: disclaimer },
  { path: '/cookies', title: 'Cookie Notice', source: cookieNotice },
  { path: '/consent', title: 'Consent', source: consentText },
]

export const CREDITS_SOURCE = credits
export const CONSENT_SOURCE = consentText

/** The consent version written in CONSENT_TEXT.md (DEC-031: the backend keeps the same value). */
export function parseConsentVersion(markdown: string): string {
  const match = /\*\*Consent version:\*\* `([^`]+)`/.exec(markdown)
  if (!match?.[1]) throw new Error('Consent version not found in CONSENT_TEXT.md')
  return match[1]
}

export const CONSENT_VERSION = parseConsentVersion(consentText)

/** The short disclaimer line from MEDICAL_DISCLAIMER.md ("Short form" section). */
export function shortDisclaimer(markdown: string = disclaimer): string {
  const match = /\*\*Short form[^*]*\*\*\s*\n"([^"]+)"/.exec(markdown)
  if (!match?.[1]) throw new Error('Short disclaimer not found in MEDICAL_DISCLAIMER.md')
  return match[1]
}

/** The consent screen parts from CONSENT_TEXT.md: the text shown above the boxes and the two
 * checkbox labels, word for word ("[Privacy Policy]" becomes plain text; the page links it). */
export function consentParts(markdown: string = consentText): {
  body: string
  checkboxes: string[]
} {
  const start = markdown.indexOf('**Before you continue**')
  const lines = markdown.slice(start).split('\n')
  const boxes = lines.filter((l) => l.startsWith('- [ ] '))
  const body = lines
    .slice(
      0,
      lines.findIndex((l) => l.startsWith('- [ ] ')),
    )
    .join('\n')
    .trim()
  if (start < 0 || boxes.length !== 2) throw new Error('Unexpected CONSENT_TEXT.md layout')
  return { body, checkboxes: boxes.map((l) => l.slice(6).replace(/\[([^\]]+)\]/g, '$1')) }
}

/** The full medical disclaimer paragraph from MEDICAL_DISCLAIMER.md ("Full text" section). */
export function fullDisclaimer(markdown: string = disclaimer): string {
  const match = /\*\*Full text\*\*\s*\n([^\n]+)/.exec(markdown)
  if (!match?.[1]) throw new Error('Full disclaimer not found in MEDICAL_DISCLAIMER.md')
  return match[1]
}

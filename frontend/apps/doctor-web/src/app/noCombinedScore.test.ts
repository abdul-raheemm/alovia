import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

/** Dashboard spec §1.3 / §25 test 15: no screen shows a combined or weighted risk score.
 * The manual check stays in the review checklist; this catches the wording in code. */
const APPS = resolve(__dirname, '../../..')
const FORBIDDEN = /combined\s+risk|overall\s+risk|weighted\s+risk|risk\s+score|total\s+risk/i

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    if (statSync(path).isDirectory()) return sources(path)
    return /\.(tsx?|css)$/.test(name) && !name.endsWith('.test.ts') ? [path] : []
  })
}

describe('no combined risk score (§25 test 15)', () => {
  it('no source file of either app uses combined-score wording', () => {
    const files = ['doctor-web', 'patient-web'].flatMap((app) => sources(join(APPS, app, 'src')))
    expect(files.length).toBeGreaterThan(40)
    const hits = files.filter((f) => FORBIDDEN.test(readFileSync(f, 'utf-8')))
    expect(hits).toEqual([])
  })
})

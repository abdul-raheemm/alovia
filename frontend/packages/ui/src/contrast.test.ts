import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { describe, expect, it } from 'vitest'

/** FRONTEND_REDESIGN §13 "contrast script passes for all token pairs" and DESIGN_SYSTEM §3.4:
 * read the real tokens.css, resolve each app and theme, and check WCAG 2.1 contrast. */
const CSS = readFileSync(resolve(__dirname, 'styles/tokens.css'), 'utf-8')

/** The custom properties declared in the block that starts with `selector {`. */
function block(selector: string): Record<string, string> {
  // at the start of a line, so `[data-theme='dark']` does not match `[data-app=…][data-theme='dark']`
  const found = CSS.indexOf(`\n${selector} {`)
  if (found < 0) throw new Error(`no block ${selector}`)
  const start = found + 1
  const body = CSS.slice(start, CSS.indexOf('\n}', start))
  return Object.fromEntries(
    [...body.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((m) => [m[1], (m[2] ?? '').trim()]),
  )
}

function colours(app: 'patient' | 'doctor', dark: boolean): (name: string) => string {
  const vars = {
    ...block('@theme'),
    ...block(`[data-app='${app}']`),
    ...(dark ? block("[data-theme='dark']") : {}),
    ...(dark ? block(`[data-app='${app}'][data-theme='dark']`) : {}),
  }
  const get = (name: string): string => {
    const value = vars[name]
    if (!value) throw new Error(`${name} not set for ${app}${dark ? ' dark' : ''}`)
    const ref = /^var\((--[\w-]+)\)$/.exec(value)
    return ref ? get(ref[1] as string) : value
  }
  return get
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }) as [number, number, number]
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function ratio(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p) as [number, number]
  return (x + 0.05) / (y + 0.05)
}

// [foreground, background, minimum]: text 4.5:1, graphics (ring arcs) 3:1
const TEXT: [string, string][] = [
  ['--color-text', '--color-bg'],
  ['--color-text', '--color-surface'],
  ['--color-muted', '--color-bg'],
  ['--color-muted', '--color-surface'],
  ['--color-on-primary', '--color-primary'],
  ['--color-primary', '--color-bg'],
  ['--color-text', '--color-primary-soft'],
  ['--color-urgent', '--color-bg'],
  ['--color-caution', '--color-bg'],
  ['--color-success', '--color-bg'],
]
const ARCS = ['--color-arc-1', '--color-arc-2', '--color-arc-3']

describe('token contrast (WCAG 2.1 AA)', () => {
  for (const app of ['patient', 'doctor'] as const) {
    for (const dark of [false, true]) {
      const c = colours(app, dark)
      it(`${app} ${dark ? 'dark' : 'light'}: text pairs reach 4.5:1`, () => {
        for (const [fg, bg] of TEXT) {
          expect(ratio(c(fg), c(bg)), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5)
        }
      })
    }
    it('patient ring arcs reach 3:1 on bg and surface in both themes', () => {
      for (const dark of [false, true]) {
        const c = colours('patient', dark)
        for (const arc of ARCS) {
          for (const bg of ['--color-bg', '--color-surface']) {
            expect(ratio(c(arc), c(bg)), `${arc} on ${bg}`).toBeGreaterThanOrEqual(3)
          }
        }
      }
    })
  }

  it('matches a ratio recorded in DESIGN_SYSTEM §3.4 (patient light text on bg 13.98)', () => {
    const c = colours('patient', false)
    expect(ratio(c('--color-text'), c('--color-bg'))).toBeCloseTo(13.98, 1)
  })
})

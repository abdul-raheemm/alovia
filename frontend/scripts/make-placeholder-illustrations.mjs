// Writes the 9 placeholder month illustrations (Journey spec §7.1: simple shapes, labelled
// "placeholder", allowed only while show_prototype_banner is true). Replaced in a later task
// by openly licensed drawings recorded in docs/legal/CREDITS.md.
// Run: node scripts/make-placeholder-illustrations.mjs
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const dir = join(import.meta.dirname, '..', 'apps', 'patient-web', 'public', 'illustrations')
mkdirSync(dir, { recursive: true })
for (let month = 1; month <= 9; month++) {
  // a simple growing circle inside an arc — shapes only, nothing anatomical
  const r = 8 + month * 4
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" role="img" aria-label="Placeholder drawing, month ${month}">
  <rect width="160" height="160" rx="24" fill="#EFE9FB"/>
  <circle cx="80" cy="84" r="52" fill="none" stroke="#B9A6F2" stroke-width="3" stroke-dasharray="6 6"/>
  <circle cx="80" cy="84" r="${r}" fill="#6B4FBB" opacity="0.85"/>
  <text x="80" y="24" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#5E5873">Placeholder</text>
  <text x="80" y="150" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#5E5873">Month ${month}</text>
</svg>
`
  writeFileSync(join(dir, `month_${month}.svg`), svg)
}
console.log('wrote 9 placeholder illustrations')

// Renders the app icons (letter mark "A" in white on the primary colour, DESIGN_SYSTEM §2)
// from one SVG with Playwright's Chromium. Run: node scripts/make-icons.mjs
import { chromium } from '@playwright/test'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const APPS = { 'patient-web': '#6B4FBB', 'doctor-web': '#4F3FA8' }
// letter mark only; the maskable icon keeps the letter inside the 80% safe zone
const svg = (
  fill,
  { round = true, letterScale = 0.62 } = {},
) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  ${round ? `<circle cx="50" cy="50" r="50" fill="${fill}"/>` : `<rect width="100" height="100" fill="${fill}"/>`}
  <text x="50" y="50" dy="0.35em" text-anchor="middle" font-family="Arial, Helvetica, sans-serif"
    font-weight="700" font-size="${100 * letterScale}" fill="#FFFFFF">A</text>
</svg>`

const browser = await chromium.launch()
const page = await browser.newPage()
for (const [app, fill] of Object.entries(APPS)) {
  const pub = join(import.meta.dirname, '..', 'apps', app, 'public')
  mkdirSync(join(pub, 'icons'), { recursive: true })
  writeFileSync(join(pub, 'favicon.svg'), svg(fill) + '\n')
  if (app !== 'patient-web') continue // only the patient app is installable (DEC-014)
  const shots = [
    ['icon-192.png', 192, svg(fill)],
    ['icon-512.png', 512, svg(fill)],
    ['icon-maskable-512.png', 512, svg(fill, { round: false, letterScale: 0.5 })],
    ['apple-touch-icon.png', 180, svg(fill, { round: false })],
  ]
  for (const [name, size, markup] of shots) {
    await page.setViewportSize({ width: size, height: size })
    await page.setContent(
      `<html><body style="margin:0;background:transparent">${markup.replace('<svg ', `<svg width="${size}" height="${size}" `)}</body></html>`,
    )
    await page.screenshot({ path: join(pub, 'icons', name), omitBackground: true })
  }
}
await browser.close()
console.log('icons written')

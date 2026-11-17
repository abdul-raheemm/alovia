// Runs a local tool from the frontend folder spelled exactly as on disk. On Windows a terminal
// opened as "c:\..." instead of "C:\..." makes Node load the same package twice, and Vitest then
// fails with "failed to find the current suite". The tool's JS entry is started with Node
// directly (no shell), so arguments are passed through unchanged.
import { spawnSync } from 'node:child_process'
import { realpathSync } from 'node:fs'
import { join } from 'node:path'

const ENTRIES = {
  vitest: 'vitest/vitest.mjs',
  playwright: '@playwright/test/cli.js',
}
const root = realpathSync.native(join(import.meta.dirname, '..'))
const [tool, ...args] = process.argv.slice(2)
const entry = ENTRIES[tool]
if (!entry) throw new Error(`unknown tool "${tool}"; known: ${Object.keys(ENTRIES).join(', ')}`)
const result = spawnSync(process.execPath, [join(root, 'node_modules', entry), ...args], {
  cwd: root,
  stdio: 'inherit',
})
process.exit(result.status ?? 1)

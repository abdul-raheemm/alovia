// npm run gen:api — regenerate packages/shared/src/api-types.ts from the backend's OpenAPI
// schema (API.md §6: frontend types are generated, never written by hand).
import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { join } from 'node:path'

const backend = join(import.meta.dirname, '..', '..', 'backend')
const python = ['Scripts/python.exe', 'bin/python']
  .map((p) => join(backend, '.venv', p))
  .find(existsSync)
if (!python) throw new Error('backend/.venv not found: create it first (see README)')
const schema = join(import.meta.dirname, '..', 'packages', 'shared', 'openapi.json')
execFileSync(python, [join(backend, 'scripts', 'export_openapi.py'), schema], { stdio: 'inherit' })
execFileSync(
  process.execPath,
  [
    join(import.meta.dirname, '..', 'node_modules', 'openapi-typescript', 'bin', 'cli.js'),
    schema,
    '-o',
    join(import.meta.dirname, '..', 'packages', 'shared', 'src', 'api-types.ts'),
  ],
  { stdio: 'inherit' },
)

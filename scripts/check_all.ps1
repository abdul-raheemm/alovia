# Runs every check from docs/TESTING.md §7 and stops at the first failure (exit code 1).
# Usage (from anywhere): powershell -ExecutionPolicy Bypass -File scripts\check_all.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root 'backend\.venv\Scripts\python.exe'
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$strict = @('-W', 'error::DeprecationWarning', '-W', 'error::ResourceWarning',
  '-W', 'error::pytest.PytestUnraisableExceptionWarning')

function Step([string]$name, [string]$dir, [scriptblock]$command) {
  Write-Host "=== $name" -ForegroundColor Cyan
  Push-Location $dir
  try {
    & $command
    if ($LASTEXITCODE -ne 0) { throw "$name failed (exit code $LASTEXITCODE)" }
  } finally {
    Pop-Location
  }
}

try {
  Step 'backend: lint' $backend { & $py -m ruff check . }
  Step 'backend: format' $backend { & $py -m ruff format --check . }
  Step 'backend: types' $backend { & $py -m mypy app tests migrations scripts }
  Step 'backend: tests' $backend { & $py -m pytest -q @strict }
  Step 'frontend: format' $frontend { npm run --silent format:check }
  Step 'frontend: lint' $frontend { npm run --silent lint }
  Step 'frontend: types' $frontend { npm run --silent typecheck }
  Step 'frontend: unit tests' $frontend { npm run --silent test }
  Step 'frontend: build' $frontend { npm run --silent build }
  Step 'frontend: end-to-end + accessibility' $frontend { npm run --silent test:e2e }
} catch {
  Write-Host $_ -ForegroundColor Red
  exit 1
}
Write-Host 'All checks passed.' -ForegroundColor Green

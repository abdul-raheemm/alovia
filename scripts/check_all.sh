#!/usr/bin/env bash
# Runs every check from docs/TESTING.md §7 and stops at the first failure (non-zero exit).
# Usage: bash scripts/check_all.sh
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
py="$root/backend/.venv/bin/python"
[ -x "$py" ] || py="$root/backend/.venv/Scripts/python.exe"

step() { echo "=== $1"; }

cd "$root/backend"
step 'backend: lint';   "$py" -m ruff check .
step 'backend: format'; "$py" -m ruff format --check .
step 'backend: types';  "$py" -m mypy app tests migrations scripts
step 'backend: tests'
"$py" -m pytest -q -W error::DeprecationWarning -W error::ResourceWarning \
  -W error::pytest.PytestUnraisableExceptionWarning

cd "$root/frontend"
step 'frontend: format';     npm run --silent format:check
step 'frontend: lint';       npm run --silent lint
step 'frontend: types';      npm run --silent typecheck
step 'frontend: unit tests'; npm run --silent test
step 'frontend: build';      npm run --silent build
step 'frontend: end-to-end + accessibility'; npm run --silent test:e2e
echo 'All checks passed.'

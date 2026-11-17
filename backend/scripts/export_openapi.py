"""Write the backend's OpenAPI schema for the frontend type generator (`npm run gen:api`).

Uses placeholder settings only; it never reads backend/.env or connects anywhere.
Usage: python scripts/export_openapi.py <out.json>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

settings = Settings(
    _env_file=None,
    supabase_jwks_url="https://example.invalid/auth/v1/.well-known/jwks.json",
    supabase_jwt_issuer="https://example.invalid/auth/v1",
    database_url="postgresql://unused:unused@127.0.0.1:1/unused",
)
schema = create_app(settings).openapi()
Path(sys.argv[1]).write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")

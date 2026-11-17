"""App factory. Run from backend/: uvicorn app.main:create_app --factory --reload"""

import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health
from app.core.config import Settings, get_settings
from app.core.database import make_engine
from app.core.errors import register_error_handlers
from app.core.logging import REQUEST_ID_HEADER, configure_logging, request_context
from app.modules.journey.config import load_journey_config
from app.modules.predictions.risk_model import load_models
from app.modules.users import router as users


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Alovia API", version=__version__)
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)  # connects on first use
    app.state.models = load_models()  # fails fast if a model file is missing (ARCHITECTURE §12)
    app.state.journey_config = load_journey_config()  # fails fast on a wrong config.yaml
    # public signing keys, fetched on first use and cached (app.core.auth)
    app.state.jwks_client = jwt.PyJWKClient(settings.supabase_jwks_url, cache_keys=True)
    register_error_handlers(app)
    app.middleware("http")(request_context)
    # added last so it wraps everything, including the 500 response
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.include_router(health.router)
    app.include_router(users.router)
    return app

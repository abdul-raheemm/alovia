"""App factory. Run with: uvicorn app.main:app --reload (from backend/)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import REQUEST_ID_HEADER, configure_logging, request_context


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Alovia API", version=__version__)
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
    return app


app = create_app()

"""Imports every model module so Base.metadata knows all tables (Alembic env, tests)."""

from app.modules.dashboard import models as dashboard_models
from app.modules.journey import models as journey_models
from app.modules.predictions import models as predictions_models
from app.modules.users import models as users_models

__all__ = ["dashboard_models", "journey_models", "predictions_models", "users_models"]

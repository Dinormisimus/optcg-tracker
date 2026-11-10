from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.leaders import router as leaders_router
from app.routers.matches import router as matches_router
from app.routers.stats import router as stats_router
from app.routers.tournaments import router as tournaments_router

__all__ = [
    "auth_router",
    "health_router",
    "leaders_router",
    "matches_router",
    "stats_router",
    "tournaments_router",
]

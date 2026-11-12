from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.routers import (
    auth_router,
    health_router,
    leaders_router,
    matches_router,
    stats_router,
    tournaments_router,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.ENV == "dev" else None,
    )
    register_error_handlers(app)

    # Nije za prvi dio projekta, ali je korisno za testiranje i razvoj
    # Dodavanje CORS middleware-a samo u razvojnom okruženju
    
    #if settings.ENV == "dev":
    #    app.add_middleware(
    #        CORSMiddleware,
    #        allow_origins=[
    #            "http://localhost:8765",
    #            "http://127.0.0.1:8765",
    #        ],
    #        allow_methods=["GET", "POST", "PATCH", "DELETE"],
    #        allow_headers=["Authorization", "Content-Type"],
    #    )
    

    # Registracija routera za autentifikaciju
    app.include_router(auth_router)
    app.include_router(leaders_router)
    app.include_router(matches_router)
    app.include_router(tournaments_router)
    app.include_router(stats_router)
    app.include_router(health_router)

    return app


# Uvicorn ulazna točka
app = create_app()

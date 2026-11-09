from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.routers import auth_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.ENV == "dev" else None,
    )

    # Registracija routera za autentifikaciju
    app.include_router(auth_router)
    app.include_router(leaders_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        try:
            async with AsyncSessionLocal() as session:
                res = await session.execute(text("SELECT version();"))
                db_version = res.scalar()
            return {"status": "ok", "database": db_version}
        except Exception as e:
            return {"status": "error", "database": str(e)}

    return app


# Uvicorn ulazna točka
app = create_app()
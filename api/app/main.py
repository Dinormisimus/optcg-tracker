from fastapi import FastAPI
from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.ENV == "dev" else None,
    )

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

# Ova linija izvozi instancu 'app' koju Uvicorn traži
app = create_app()
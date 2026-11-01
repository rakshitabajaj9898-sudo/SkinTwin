from sqlalchemy import text
from backend.app.database import engine
from fastapi import FastAPI

from backend.app.routes.consent import router as consent_router
from backend.app.routes.auth import router as auth_router

from backend.app.routes.skin_analysis import router as skin_analysis_router
app.include_router(skin_analysis_router)

app = FastAPI(
    title="SkinTwin API",
    version="2.0.0"
)

app.include_router(consent_router)
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to SkinTwin 2.0!",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "SkinTwin",
        "version": "2.0.0"
    }
@app.get("/health/database")
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "status": "healthy"
        }

    except Exception:
        return {
            "database": "disconnected",
            "status": "unhealthy"
        }

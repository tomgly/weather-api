from fastapi import FastAPI

from app.air_quality import router as air_quality_router
from app.allergy import router as allergy_router
from app.today import router as today_router


app = FastAPI(
    title="Weather API",
    description="A local API for weather, allergy, and air quality data.",
    version="0.1.0",
)


@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "weather-api",
        "version": app.version,
    }


app.include_router(today_router)
app.include_router(allergy_router)
app.include_router(air_quality_router)

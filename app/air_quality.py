from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.client import (
    InvalidLocationError,
    WeatherRequestError,
    fetch_weather_api,
    resolve_geocode,
)


router = APIRouter(
    tags=["Air Quality"],
)


class AirQualityDataError(Exception):
    """Raised when air quality data cannot be read from Weather.com."""


def build_air_quality_response(data: dict[str, Any]) -> dict[str, Any]:
    """Build the air quality response from a Weather.com API payload."""

    try:
        info = data["globalairquality"]

        return {
            "aqi": info["airQualityIndex"],
            "category": info["airQualityCategory"],
        }

    except (KeyError, TypeError) as error:
        raise AirQualityDataError(
            f"Weather.com API returned an unexpected payload: {error}"
        ) from error


@router.get(
    "/air-quality",
    summary="Get current air quality",
)
async def get_air_quality(
    state: str = Query(
        min_length=2,
        max_length=32,
        examples=["ohio"],
    ),
    city: str = Query(
        min_length=1,
        max_length=64,
        examples=["fairborn"],
    ),
) -> dict[str, object]:
    """Return current air quality information for a city."""

    try:
        geocode = await resolve_geocode(state=state, city=city)

        data = await fetch_weather_api(
            "/v3/wx/globalAirQuality",
            geocode,
            scale="EPA",
        )

        return build_air_quality_response(data)

    except InvalidLocationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except WeatherRequestError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    except AirQualityDataError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

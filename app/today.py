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
    tags=["Weather"],
)


class TodayDataError(Exception):
    """Raised when current weather data cannot be read from Weather.com."""


def build_today_response(
    observations: dict[str, Any],
    daily_forecast: dict[str, Any],
) -> dict[str, Any]:
    """Build the /today response from Weather.com API payloads."""

    try:
        today = daily_forecast["daypart"][0]

        return {
            "temperature": observations["temperature"],
            "condition": observations["wxPhraseLong"],
            "feels_like": observations["temperatureFeelsLike"],
            "high": daily_forecast["temperatureMax"][0],
            "low": daily_forecast["temperatureMin"][0],
            "chance_of_rain_percent": max(
                today["precipChance"][0],
                today["precipChance"][1],
            ),
            "precipitation_inches": daily_forecast["qpf"][0],
            "units": {
                "temperature": "F",
                "precipitation": "in",
            },
        }

    except (KeyError, IndexError, TypeError) as error:
        raise TodayDataError(
            f"Weather.com API returned an unexpected payload: {error}"
        ) from error


@router.get(
    "/today",
    summary="Get today's weather",
)
async def get_today(
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
) -> dict[str, Any]:
    """Return current weather conditions for a city."""

    try:
        geocode = await resolve_geocode(state=state, city=city)

        observations = await fetch_weather_api(
            "/v3/wx/observations/current",
            geocode,
            units="e",
        )

        daily_forecast = await fetch_weather_api(
            "/v3/wx/forecast/daily/3day",
            geocode,
            units="e",
        )

        return build_today_response(
            observations,
            daily_forecast,
        )

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

    except TodayDataError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

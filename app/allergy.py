from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.client import (
    InvalidLocationError,
    WeatherRequestError,
    fetch_weather_api,
    normalize_slug,
    resolve_geocode,
)


DAYS_TO_RETURN = 3


router = APIRouter(
    tags=["Allergy"],
)

POLLEN_CATEGORY_FIELDS = {
    "tree": "treePollenCategory",
    "grass": "grassPollenCategory",
    "ragweed": "ragweedPollenCategory",
}


class AllergyDataError(Exception):
    """Raised when allergy data cannot be read from Weather.com."""


def build_allergy_response(pollen: dict[str, Any]) -> dict[str, Any]:
    """Build the pollen forecast from a Weather.com API payload."""

    try:
        forecast = pollen["pollenForecast12hour"]

        day_indices = [
            index
            for index, day_ind in enumerate(forecast["dayInd"])
            if day_ind == "D"
        ][:DAYS_TO_RETURN]

        day_keys = [
            normalize_slug(forecast["daypartName"][index])
            for index in day_indices
        ]

        pollen_by_type = {
            pollen_key: {
                day_key: forecast[field][index]
                for day_key, index in zip(day_keys, day_indices)
            }
            for pollen_key, field in POLLEN_CATEGORY_FIELDS.items()
        }

    except (KeyError, TypeError) as error:
        raise AllergyDataError(
            f"Weather.com API returned an unexpected payload: {error}"
        ) from error

    return {
        "pollen": pollen_by_type,
    }


@router.get(
    "/allergy",
    summary="Get allergy forecast",
)
async def get_allergy(
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
    """Return pollen forecasts for a city."""

    try:
        geocode = await resolve_geocode(state=state, city=city)

        pollen = await fetch_weather_api(
            "/v2/indices/pollen/daypart/3day",
            geocode,
        )

        allergy = build_allergy_response(pollen)

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

    except AllergyDataError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return {
        "allergy": allergy,
    }

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()

BASE_URL = "https://weather.com"
API_BASE_URL = "https://api.weather.com"
API_KEY = os.getenv("WEATHER_API_KEY", "71f92ea9dd2f4790b92ea9dd2f779061")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "20"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
)

GEOCODE_PATTERN = re.compile(
    r'"geocode\\?":\\?"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)'
)


class WeatherClientError(Exception):
    """Base exception for Weather.com client errors."""


class InvalidLocationError(WeatherClientError):
    """Raised when a state or city cannot be resolved to a location."""


class WeatherRequestError(WeatherClientError):
    """Raised when Weather.com cannot be reached or errors."""


def normalize_slug(value: str) -> str:
    """Convert a state or city name into a Weather.com URL slug."""

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")

    if not normalized:
        raise InvalidLocationError("State and city must not be empty.")

    return normalized


def build_location_url(state: str, city: str) -> str:
    """Build the Weather.com city page URL used to resolve a geocode."""

    state_slug = normalize_slug(state)
    city_slug = normalize_slug(city)

    return f"{BASE_URL}/us/{state_slug}/city/{city_slug}/today"


async def resolve_geocode(state: str, city: str) -> str:
    """Resolve a state and city into a 'lat,lon' geocode string."""

    url = build_location_url(state=state, city=city)

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise WeatherRequestError(
                f"Request to Weather.com timed out: {url}"
            ) from error

        except httpx.HTTPStatusError as error:
            raise WeatherRequestError(
                "Weather.com returned "
                f"HTTP {error.response.status_code}: {url}"
            ) from error

        except httpx.RequestError as error:
            raise WeatherRequestError(
                f"Could not connect to Weather.com: {url}"
            ) from error

    match = GEOCODE_PATTERN.search(response.text)

    if match is None:
        raise InvalidLocationError(
            f"Could not resolve a location for state={state!r}, city={city!r}."
        )

    return f"{match.group(1)},{match.group(2)}"


async def fetch_weather_api(
    path: str,
    geocode: str,
    **params: Any,
) -> dict[str, Any]:
    """Call a Weather.com public data API endpoint and return its JSON body."""

    url = f"{API_BASE_URL}{path}"
    query = {
        "geocode": geocode,
        "language": "en-US",
        "format": "json",
        "apiKey": API_KEY,
        **params,
    }

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        try:
            response = await client.get(url, params=query)
            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise WeatherRequestError(
                f"Request to Weather.com API timed out: {url}"
            ) from error

        except httpx.HTTPStatusError as error:
            raise WeatherRequestError(
                "Weather.com API returned "
                f"HTTP {error.response.status_code}: {url}"
            ) from error

        except httpx.RequestError as error:
            raise WeatherRequestError(
                f"Could not connect to Weather.com API: {url}"
            ) from error

    return response.json()

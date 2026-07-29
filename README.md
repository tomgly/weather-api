# Weather API

[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A small local API for current weather, pollen (allergy), and air quality data for US cities, powered by Weather.com's public data API.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/today?state=&city=` | Current temperature, condition, high/low, chance of rain |
| GET | `/allergy?state=&city=` | 3-day tree/grass/ragweed pollen forecast |
| GET | `/air-quality?state=&city=` | Current air quality index and category |
| GET | `/health` | Health check |

Interactive docs are available at `/docs` once the server is running.

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Install dependencies:
   ```
   uv sync
   ```
3. (Optional) Copy `.env.example` to `.env` and set `WEATHER_API_KEY` if Weather.com's key ever rotates (grab a fresh one from the Network tab on any weather.com page).
4. Run the server:
   ```
   uv run uvicorn app.main:app --reload
   ```

### Docker

```
docker compose up -d --build
```

The API is then available at `http://127.0.0.1:8000`.

## Example

```
curl "http://127.0.0.1:8000/today?state=new-york&city=new-york-city"
```

```json
{
  "temperature": 82,
  "condition": "Mostly Cloudy",
  "feels_like": 87,
  "high": 82,
  "low": 68,
  "chance_of_rain_percent": 42,
  "precipitation_inches": 0.0,
  "units": { "temperature": "F", "precipitation": "in" }
}
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

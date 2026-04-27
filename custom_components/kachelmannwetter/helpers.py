"""Helpers to normalize Kachelmann API responses for Home Assistant."""
from __future__ import annotations

from typing import Any
from datetime import datetime, date

# Maps Kachelmann weatherSymbol strings to HA condition strings.
# See: https://developers.home-assistant.io/docs/core/entity/weather#recommended-values-for-state-and-condition
WEATHER_SYMBOL_MAP: dict[str, str] = {
    "sunshine": "sunny",
    "partlycloudy": "partlycloudy",
    "partlycloudy2": "partlycloudy",
    "cloudy": "cloudy",
    "overcast": "cloudy",
    "fog": "fog",
    "rain": "rainy",
    "raindrizzle": "rainy",
    "rainheavy": "pouring",
    "showers": "rainy",
    "showersheavy": "pouring",
    "thunderstorm": "lightning-rainy",
    "severethunderstorm": "lightning-rainy",
    "snow": "snowy",
    "snowheavy": "snowy",
    "snowshowers": "snowy",
    "snowshowersheavy": "snowy",
    "snowrain": "snowy-rainy",
    "snowrainshowers": "snowy-rainy",
    "freezingrain": "exceptional",
    "wind": "windy",
}

# Severity order for picking the "worst" condition of a day.
_CONDITION_SEVERITY: list[str] = [
    "sunny",
    "partlycloudy",
    "cloudy",
    "windy",
    "fog",
    "rainy",
    "pouring",
    "snowy",
    "snowy-rainy",
    "lightning-rainy",
    "exceptional",
]


def safeget(dct: dict | Any, *keys: str) -> Any:
    """Safely traverse nested dicts, returning None on missing keys."""
    for key in keys:
        if not isinstance(dct, dict):
            return None
        dct = dct.get(key)
    return dct


def _safe_avg(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 1) if clean else None


def _safe_max(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return max(clean) if clean else None


def _safe_min(values: list) -> float | None:
    clean = [v for v in values if v is not None]
    return min(clean) if clean else None


def _safe_sum(values: list) -> float:
    return round(sum(v for v in values if v is not None), 1)


def _worst_condition(conditions: set[str | None]) -> str | None:
    """Pick the most severe weather condition from a set."""
    clean = {c for c in conditions if c is not None}
    if not clean:
        return None
    return max(
        clean,
        key=lambda c: _CONDITION_SEVERITY.index(c)
        if c in _CONDITION_SEVERITY
        else 0,
    )


def _to_rfc3339(d: date, hour: int = 12) -> str:
    """Convert a date to RFC 3339 UTC string as required by HA forecasts."""
    return datetime(d.year, d.month, d.day, hour, 0, 0).isoformat() + "+00:00"


# ---------------------------------------------------------------------------
# Current weather normalization
# ---------------------------------------------------------------------------

def normalize_current(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the /current endpoint response."""
    if not data:
        return {}
    return {
        "temperature": safeget(data, "data", "temp", "value"),
        "humidity": safeget(data, "data", "humidityRelative", "value"),
        "pressure": safeget(data, "data", "pressureMsl", "value"),
        "dew_point": safeget(data, "data", "dewpoint", "value"),
        "wind_speed": safeget(data, "data", "windSpeed", "value"),
        "wind_gust": safeget(data, "data", "windGust", "value"),
        "wind_bearing": safeget(data, "data", "windDirection", "value"),
        "cloud_coverage": safeget(data, "data", "cloudCoverage", "value"),
        "cloud_coverage_low": safeget(data, "data", "cloudCoverageLow", "value"),
        "cloud_coverage_medium": safeget(data, "data", "cloudCoverageMedium", "value"),
        "cloud_coverage_high": safeget(data, "data", "cloudCoverageHigh", "value"),
        "precipitation_1h": safeget(data, "data", "prec1h", "value"),
        "snow_height": safeget(data, "data", "snowHeight", "value"),
        "sun_hours": safeget(data, "data", "sunHours", "value"),
        "condition": WEATHER_SYMBOL_MAP.get(
            safeget(data, "data", "weatherSymbol", "value") or ""
        ),
    }


# ---------------------------------------------------------------------------
# Hourly forecast normalization
# ---------------------------------------------------------------------------

def normalize_hourly(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the /advanced/1h endpoint into HA hourly Forecast dicts."""
    if not data:
        return []
    forecasts: list[dict[str, Any]] = []
    for entry in data.get("data", []):
        dt_str = entry.get("dateTime", "")
        symbol = WEATHER_SYMBOL_MAP.get(entry.get("weatherSymbol", ""))
        forecasts.append({
            "datetime": dt_str,
            "condition": symbol,
            "cloud_coverage": entry.get("cloudCoverage"),
            "cloud_coverage_low": entry.get("cloudCoverageLow"),
            "cloud_coverage_medium": entry.get("cloudCoverageMedium"),
            "cloud_coverage_high": entry.get("cloudCoverageHigh"),
            "humidity": entry.get("humidityRelative"),
            "native_dew_point": entry.get("dewpoint"),
            "native_precipitation": entry.get("precCurrent", 0),
            "native_pressure": entry.get("pressureMsl"),
            "native_temperature": entry.get("temp"),
            "native_wind_gust_speed": entry.get("windGust"),
            "native_wind_speed": entry.get("windSpeed"),
            "wind_bearing": entry.get("windDirection"),
        })
    return forecasts


# ---------------------------------------------------------------------------
# Daily forecast normalization (aggregated from 6h data)
# ---------------------------------------------------------------------------

def normalize_daily(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the /advanced/6h endpoint into HA daily Forecast dicts."""
    if not data:
        return []

    daily_data: dict[date, dict[str, Any]] = {}

    for entry in data.get("data", []):
        date_key = datetime.fromisoformat(entry["dateTime"]).date()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "cloud_coverage": [],
                "condition": set(),
                "humidity": [],
                "native_dew_point": [],
                "native_precipitation": [],
                "native_pressure": [],
                "native_temperature": [],
                "native_templow": [],
                "native_wind_gust_speed": [],
                "native_wind_speed": [],
                "wind_bearing": [],
                "global_radiation": [],
                "sun_hours": [],
            }

        d = daily_data[date_key]
        symbol = WEATHER_SYMBOL_MAP.get(entry.get("weatherSymbol", ""))
        if symbol:
            d["condition"].add(symbol)
        d["cloud_coverage"].append(entry.get("cloudCoverage"))
        d["humidity"].append(entry.get("humidityRelative"))
        d["native_dew_point"].append(entry.get("dewpoint"))
        d["native_precipitation"].append(entry.get("prec6h", 0))
        d["native_pressure"].append(entry.get("pressureMsl"))
        d["native_temperature"].append(entry.get("tempMax6h"))
        d["native_templow"].append(entry.get("tempMin6h"))
        d["native_wind_gust_speed"].append(entry.get("windGust"))
        d["native_wind_speed"].append(entry.get("windSpeed"))
        d["wind_bearing"].append(entry.get("windDirection"))
        d["global_radiation"].append(entry.get("globalRadiation"))
        d["sun_hours"].append(entry.get("sunHours"))

    forecasts: list[dict[str, Any]] = []
    for date_key in sorted(daily_data):
        d = daily_data[date_key]
        forecasts.append({
            "datetime": _to_rfc3339(date_key),
            "condition": _worst_condition(d["condition"]),
            "cloud_coverage": _safe_avg(d["cloud_coverage"]),
            "humidity": _safe_avg(d["humidity"]),
            "native_dew_point": _safe_avg(d["native_dew_point"]),
            "native_precipitation": _safe_sum(d["native_precipitation"]),
            "native_pressure": _safe_avg(d["native_pressure"]),
            "native_temperature": _safe_max(d["native_temperature"]),
            "native_templow": _safe_min(d["native_templow"]),
            "native_wind_gust_speed": _safe_max(d["native_wind_gust_speed"]),
            "native_wind_speed": _safe_max(d["native_wind_speed"]),
            "wind_bearing": round(_safe_avg(d["wind_bearing"]))
            if _safe_avg(d["wind_bearing"]) is not None
            else None,
            # Extra data (not standard HA forecast fields, but stored for sensors)
            "_global_radiation": _safe_sum(d["global_radiation"]),
            "_sun_hours": _safe_sum(d["sun_hours"]),
        })
    return forecasts

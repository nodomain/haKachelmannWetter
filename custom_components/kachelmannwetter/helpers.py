"""Helpers to normalize Kachelmann API responses to canonical keys."""
from __future__ import annotations

from typing import Any
from datetime import datetime, date

WEATHER_SYMBOL_DICT = {
    "cloudy": "cloudy",
    "fog": "fog",
    "freezingrain": "exceptional",
    "overcast": "cloudy",
    "partlycloudy": "partlycloudy",
    "partlycloudy2": "partlycloudy",
    "rain": "rainy",
    "raindrizzle": "rainy",
    "rainheavy": "pouring",
    "severethunderstorm": "lightning-rainy",
    "showers": "rainy",
    "showersheavy": "rainy",
    "snow": "snowy",
    "snowheavy": "snowy",
    "snowrain": "snowy-rainy",
    "snowrainshowers": "snowy-rainy",
    "snowshowers": "snowy",
    "snowshowersheavy": "snowy",
    "sunshine": "sunny",
    "thunderstorm": "lightning-rainy",
    "wind": "windy",
}


def safeget(dct, *keys):
    """Safely traverse nested dicts."""
    for key in keys:
        try:
            dct = dct[key]
        except (KeyError, TypeError):
            return None
    return dct


def normalize_current(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize current weather API response to canonical keys."""
    if not data:
        return {}

    out: dict[str, Any] = {}
    out["temperature"] = safeget(data, "data", "temp", "value")
    out["humidity"] = safeget(data, "data", "humidityRelative", "value")
    out["pressure"] = safeget(data, "data", "pressureMsl", "value")
    out["wind_speed"] = safeget(data, "data", "windSpeed", "value")
    out["wind_gust"] = safeget(data, "data", "windGust", "value")
    out["wind_bearing"] = safeget(data, "data", "windDirection", "value")
    out["precipitation_1h"] = safeget(data, "data", "prec1h", "value")
    out["condition"] = WEATHER_SYMBOL_DICT.get(
        safeget(data, "data", "weatherSymbol", "value")
    )
    return out


def _safe_avg(values: list) -> float | None:
    """Return average of non-None values, or None."""
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def _safe_max(values: list) -> float | None:
    """Return max of non-None values, or None."""
    clean = [v for v in values if v is not None]
    return max(clean) if clean else None


def _safe_min(values: list) -> float | None:
    """Return min of non-None values, or None."""
    clean = [v for v in values if v is not None]
    return min(clean) if clean else None


def _safe_sum(values: list) -> float:
    """Return sum of non-None values."""
    return sum(v for v in values if v is not None)


def normalize_forecasts(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize 6h forecast data into daily forecasts for HA."""
    if not data:
        return {}

    out: dict[str, Any] = {"daily": []}
    daily_data: dict[date, dict[str, list]] = {}

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
            }

        d = daily_data[date_key]
        d["cloud_coverage"].append(entry.get("cloudCoverage"))
        symbol = WEATHER_SYMBOL_DICT.get(entry.get("weatherSymbol"))
        if symbol:
            d["condition"].add(symbol)
        d["humidity"].append(entry.get("humidityRelative"))
        d["native_dew_point"].append(entry.get("dewpoint"))
        d["native_precipitation"].append(entry.get("prec6h", 0))
        d["native_pressure"].append(entry.get("pressureMsl"))
        d["native_temperature"].append(entry.get("tempMax6h"))
        d["native_templow"].append(entry.get("tempMin6h"))
        d["native_wind_gust_speed"].append(entry.get("windGust"))
        d["native_wind_speed"].append(entry.get("windSpeed"))
        d["wind_bearing"].append(entry.get("windDirection"))

    # Priority order for picking the "worst" condition of the day
    _condition_severity = list(WEATHER_SYMBOL_DICT.values())

    for date_key in sorted(daily_data):
        d = daily_data[date_key]
        # Pick the most severe condition of the day
        condition = None
        if d["condition"]:
            condition = max(
                d["condition"],
                key=lambda x: _condition_severity.index(x)
                if x in _condition_severity
                else 0,
            )

        # RFC 3339 UTC datetime as required by HA
        dt_str = datetime(
            date_key.year, date_key.month, date_key.day, 12, 0, 0
        ).isoformat() + "+00:00"

        forecast = {
            "datetime": dt_str,
            "condition": condition,
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
        }
        out["daily"].append(forecast)

    return out

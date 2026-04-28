"""Helpers to normalize Kachelmann API responses for Home Assistant."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

# Maps Kachelmann weatherSymbol strings to HA condition strings.
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
    "showers_moderate": "rainy",
    "showers_rain_light": "rainy",
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
    "hail": "hail",
    "wind": "windy",
    "windvariant": "windy-variant",
}

# Severity order for picking the "worst" condition of a day.
_CONDITION_SEVERITY: list[str] = [
    "sunny",
    "partlycloudy",
    "cloudy",
    "windy",
    "windy-variant",
    "fog",
    "rainy",
    "pouring",
    "snowy",
    "snowy-rainy",
    "hail",
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
    clean = {c for c in conditions if c is not None}
    if not clean:
        return None
    return max(
        clean,
        key=lambda c: _CONDITION_SEVERITY.index(c) if c in _CONDITION_SEVERITY else 0,
    )


def _to_rfc3339(d: date, hour: int = 12) -> str:
    return datetime(d.year, d.month, d.day, hour, 0, 0).isoformat() + "+00:00"


def _map_condition(symbol: str | None, is_day: bool | None = None) -> str | None:
    """Map a Kachelmann weatherSymbol to HA condition, respecting day/night."""
    if not symbol:
        return None
    condition = WEATHER_SYMBOL_MAP.get(symbol)
    # Use clear-night instead of sunny when it's nighttime
    if condition == "sunny" and is_day is False:
        return "clear-night"
    return condition


# ---------------------------------------------------------------------------
# Current weather normalization
# ---------------------------------------------------------------------------


def normalize_current(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the /current endpoint response."""
    if not data:
        return {}
    is_day = safeget(data, "data", "isDay", "value")
    return {
        "temperature": safeget(data, "data", "temp", "value"),
        "humidity": safeget(data, "data", "humidityRelative", "value"),
        "pressure": safeget(data, "data", "pressureMsl", "value"),
        "dew_point": safeget(data, "data", "dewpoint", "value"),
        "wind_speed": safeget(data, "data", "windSpeed", "value"),
        "wind_gust": safeget(data, "data", "windGust", "value"),
        "wind_bearing": safeget(data, "data", "windDirection", "value"),
        "cloud_coverage": safeget(data, "data", "cloudCoverage", "value"),
        "precipitation_1h": safeget(data, "data", "prec1h", "value"),
        "snow_height": safeget(data, "data", "snowHeight", "value"),
        "snow_amount": safeget(data, "data", "snowAmount", "value"),
        "sun_hours": safeget(data, "data", "sunHours", "value"),
        "is_day": is_day,
        "condition": _map_condition(safeget(data, "data", "weatherSymbol", "value"), is_day),
        "weather_symbol": safeget(data, "data", "weatherSymbol", "value"),
    }


# ---------------------------------------------------------------------------
# Hourly forecast normalization (from /advanced/1h)
# ---------------------------------------------------------------------------


def normalize_hourly(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the /advanced/1h endpoint into HA hourly Forecast dicts."""
    if not data:
        return []
    forecasts: list[dict[str, Any]] = []
    for entry in data.get("data", []):
        is_day = entry.get("isDay")
        forecasts.append(
            {
                "datetime": entry.get("dateTime", ""),
                "condition": _map_condition(entry.get("weatherSymbol"), is_day),
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
                # Extra fields not in standard HA Forecast but stored for sensors
                "_global_radiation": entry.get("globalRadiation"),
                "_sun_hours": entry.get("sunHours"),
                "_wind_gust_3h": entry.get("windGust3h"),
                "_snow_amount": entry.get("snowAmount"),
                "_snow_height": entry.get("snowHeight"),
                "_is_day": is_day,
            }
        )
    return forecasts


# ---------------------------------------------------------------------------
# Daily forecast normalization (aggregated from /advanced/6h)
# ---------------------------------------------------------------------------


def normalize_daily_from_6h(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the /advanced/6h endpoint into daily aggregated data."""
    if not data:
        return []

    daily_data: dict[date, dict[str, Any]] = {}

    for entry in data.get("data", []):
        date_key = datetime.fromisoformat(entry["dateTime"]).date()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "condition": set(),
                "cloud_coverage": [],
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
        # Always map as daytime for daily forecast — avoids clear-night (moon)
        # leaking into multi-day views when night slots are included
        symbol = _map_condition(entry.get("weatherSymbol"), is_day=True)
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
        forecasts.append(
            {
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
                "wind_bearing": (
                    round(avg) if (avg := _safe_avg(d["wind_bearing"])) is not None else None
                ),
                "_global_radiation": _safe_sum(d["global_radiation"]),
                "_sun_hours": _safe_sum(d["sun_hours"]),
            }
        )
    return forecasts


# ---------------------------------------------------------------------------
# 14-day trend normalization (from /trend14days)
# ---------------------------------------------------------------------------


def normalize_trend14(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the /trend14days endpoint into enriched daily data."""
    if not data:
        return []
    days: list[dict[str, Any]] = []
    for entry in data.get("data", []):
        days.append(
            {
                "date": entry.get("dateTime"),
                "weekday": entry.get("weekday"),
                "is_weekend": entry.get("isWeekend"),
                "temp_max": entry.get("tempMax"),
                "temp_max_low": entry.get("tempMaxLow"),
                "temp_max_high": entry.get("tempMaxHigh"),
                "temp_min": entry.get("tempMin"),
                "temp_min_low": entry.get("tempMinLow"),
                "temp_min_high": entry.get("tempMinHigh"),
                "precipitation": entry.get("prec"),
                "precipitation_low": entry.get("precLow"),
                "precipitation_high": entry.get("precHigh"),
                "precipitation_probability_1mm": entry.get("precProb1mm"),
                "precipitation_probability_10mm": entry.get("precProb10mm"),
                "precipitation_type": entry.get("precType"),
                "precipitation_intensity": entry.get("precIntensity"),
                "precipitation_word": entry.get("precWord"),
                "wind_gust": entry.get("windGust"),
                "wind_gust_low": entry.get("windGustLow"),
                "wind_gust_high": entry.get("windGustHigh"),
                "sun_max_possible": entry.get("sunMaxPos"),
                "sun_hours": entry.get("sunHours"),
                "sun_hours_relative": entry.get("sunHoursRelative"),
                "sun_hours_low": entry.get("sunHoursLow"),
                "sun_hours_high": entry.get("sunHoursHigh"),
                "cloud_coverage_eighths": entry.get("cloudCoverageEighths"),
                "cloud_word": entry.get("cloudWord"),
                "thunderstorm": entry.get("thunderStorm"),
                "condition": _map_condition(entry.get("weatherSymbol"), True),
            }
        )
    return days


# ---------------------------------------------------------------------------
# Astronomy normalization (from /tools/astronomy)
# ---------------------------------------------------------------------------


def normalize_astronomy(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the /tools/astronomy endpoint."""
    if not data:
        return {}
    result: dict[str, Any] = {
        "next_full_moon": data.get("nextFullMoon"),
        "next_new_moon": data.get("nextNewMoon"),
        "days": [],
    }
    for day in data.get("dailyData", []):
        result["days"].append(
            {
                "date": day.get("dateTime"),
                "sunrise": day.get("sunrise"),
                "sunset": day.get("sunset"),
                "transit": day.get("transit"),
                "civil_dawn": day.get("civilDawn"),
                "civil_dusk": day.get("civilDusk"),
                "nautical_dawn": day.get("nauticalDawn"),
                "nautical_dusk": day.get("nauticalDusk"),
                "astronomical_dawn": day.get("astronomicalDawn"),
                "astronomical_dusk": day.get("astronomicalDusk"),
                "moon_illumination": day.get("moonIllumination"),
                "moon_phase": day.get("moonPhase"),
                "moon_rise": day.get("moonRise"),
                "moon_set": day.get("moonSet"),
            }
        )
    return result

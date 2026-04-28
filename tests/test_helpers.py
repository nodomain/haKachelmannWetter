"""Tests for KachelmannWetter helpers."""

from __future__ import annotations

from custom_components.kachelmannwetter.helpers import (
    WEATHER_SYMBOL_MAP,
    _map_condition,
    normalize_astronomy,
    normalize_current,
    normalize_daily_from_6h,
    normalize_hourly,
    normalize_trend14,
    safeget,
)

from .conftest import (
    MOCK_ASTRONOMY,
    MOCK_CURRENT,
    MOCK_FORECAST_1H,
    MOCK_FORECAST_6H,
    MOCK_TREND14,
)


def test_safeget() -> None:
    """Test safeget helper."""
    d = {"a": {"b": {"c": 42}}}
    assert safeget(d, "a", "b", "c") == 42
    assert safeget(d, "a", "x") is None
    assert safeget(d, "z") is None
    assert safeget(None, "a") is None


def test_map_condition_day() -> None:
    """Test condition mapping during daytime."""
    assert _map_condition("sunshine", True) == "sunny"
    assert _map_condition("partlycloudy", True) == "partlycloudy"
    assert _map_condition("rainheavy", True) == "pouring"


def test_map_condition_night() -> None:
    """Test clear-night mapping at nighttime."""
    assert _map_condition("sunshine", False) == "clear-night"
    assert _map_condition("cloudy", False) == "cloudy"


def test_map_condition_unknown() -> None:
    """Test unknown symbol returns None."""
    assert _map_condition("unknown_symbol") is None
    assert _map_condition(None) is None
    assert _map_condition("") is None


def test_normalize_current() -> None:
    """Test current weather normalization."""
    result = normalize_current(MOCK_CURRENT)
    assert result["temperature"] == 18.3
    assert result["humidity"] == 28
    assert result["pressure"] == 1020.1
    assert result["dew_point"] == -0.8
    assert result["wind_speed"] == 2.5
    assert result["condition"] == "partlycloudy"
    assert result["is_day"] is True
    assert result["snow_amount"] == 0


def test_normalize_current_empty() -> None:
    """Test normalization with empty data."""
    assert normalize_current({}) == {}
    assert normalize_current(None) == {}


def test_normalize_hourly() -> None:
    """Test hourly forecast normalization."""
    result = normalize_hourly(MOCK_FORECAST_1H)
    assert len(result) == 1
    assert result[0]["native_temperature"] == 17.8
    assert result[0]["condition"] == "partlycloudy"
    assert result[0]["_global_radiation"] == 91.2
    assert result[0]["cloud_coverage_high"] == 98


def test_normalize_daily() -> None:
    """Test daily forecast normalization from 6h data."""
    result = normalize_daily_from_6h(MOCK_FORECAST_6H)
    assert len(result) == 1
    assert result[0]["native_temperature"] == 17.8
    assert result[0]["native_templow"] == 9.6
    assert result[0]["_global_radiation"] == 500.0
    assert "2026-04-28" in result[0]["datetime"]


def test_normalize_trend14() -> None:
    """Test 14-day trend normalization."""
    result = normalize_trend14(MOCK_TREND14)
    assert len(result) == 1
    assert result[0]["temp_max"] == 19.5
    assert result[0]["precipitation_probability_1mm"] == 0
    assert result[0]["sun_hours_relative"] == 72
    assert result[0]["condition"] == "partlycloudy"


def test_normalize_astronomy() -> None:
    """Test astronomy normalization."""
    result = normalize_astronomy(MOCK_ASTRONOMY)
    assert result["next_full_moon"] == "2026-05-01T19:24:43+02:00"
    assert len(result["days"]) == 1
    assert result["days"][0]["moon_illumination"] == 90
    assert "2026-04-28" in result["days"][0]["sunrise"]


def test_all_weather_symbols_mapped() -> None:
    """Test that all symbols in the map produce valid HA conditions."""
    valid_conditions = {
        "sunny",
        "clear-night",
        "partlycloudy",
        "cloudy",
        "fog",
        "rainy",
        "pouring",
        "snowy",
        "snowy-rainy",
        "lightning-rainy",
        "exceptional",
        "windy",
        "windy-variant",
        "hail",
    }
    for symbol, condition in WEATHER_SYMBOL_MAP.items():
        assert condition in valid_conditions, f"{symbol} -> {condition} not valid"

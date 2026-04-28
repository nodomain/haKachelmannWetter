"""Fixtures for KachelmannWetter tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kachelmannwetter.const import CONF_API_KEY, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture(autouse=True)
def expected_lingering_threads() -> bool:
    """Allow lingering threads created by the coordinator's asyncio.gather."""
    return True


MOCK_API_KEY = "test_api_key_1234567890"
MOCK_LAT = 49.4617
MOCK_LON = 11.1538

MOCK_CONFIG_DATA = {
    CONF_API_KEY: MOCK_API_KEY,
    "latitude": MOCK_LAT,
    "longitude": MOCK_LON,
}

MOCK_CURRENT = {
    "data": {
        "isDay": {"value": True},
        "temp": {"value": 18.3},
        "dewpoint": {"value": -0.8},
        "humidityRelative": {"value": 28},
        "pressureMsl": {"value": 1020.1},
        "windSpeed": {"value": 2.5},
        "windDirection": {"value": 305},
        "windGust": {"value": 5.6},
        "cloudCoverage": {"value": 46},
        "prec1h": {"value": 0},
        "snowHeight": {"value": 0},
        "snowAmount": {"value": 0},
        "sunHours": {"value": 0.91},
        "wmoCode": {"value": 0},
        "weatherSymbol": {"value": "partlycloudy"},
    }
}

MOCK_FORECAST_1H = {
    "data": [
        {
            "dateTime": "2026-04-28T10:00:00+00:00",
            "isDay": True,
            "temp": 17.8,
            "dewpoint": 1.1,
            "pressureMsl": 1019.1,
            "humidityRelative": 33.9,
            "windSpeed": 1.8,
            "windDirection": 37,
            "windGust": 5.6,
            "windGust3h": 5.6,
            "cloudCoverage": 37,
            "cloudCoverageLow": 0,
            "cloudCoverageMedium": 26,
            "cloudCoverageHigh": 98,
            "sunHours": 3.7,
            "globalRadiation": 91.2,
            "precCurrent": 0,
            "prec6h": 0,
            "precTotal": 0,
            "snowAmount": 0,
            "snowAmount6h": 0,
            "snowHeight": 0,
            "wmoCode": 0,
            "weatherSymbol": "partlycloudy",
        }
    ]
}

MOCK_FORECAST_6H = {
    "data": [
        {
            "dateTime": "2026-04-28T16:00:00+00:00",
            "isDay": True,
            "temp": 17.2,
            "tempMin6h": 9.6,
            "tempMax6h": 17.8,
            "dewpoint": 1.1,
            "pressureMsl": 1019.1,
            "humidityRelative": 33.9,
            "windSpeed": 3.4,
            "windDirection": 37,
            "windGust": 5.6,
            "cloudCoverage": 37,
            "cloudCoverageLow": 0,
            "cloudCoverageMedium": 26,
            "cloudCoverageHigh": 98,
            "sunHours": 3.7,
            "globalRadiation": 500.0,
            "precCurrent": 0,
            "prec6h": 0,
            "precTotal": 0,
            "snowAmount": 0,
            "snowAmount6h": 0,
            "snowHeight": 0,
            "wmoCode": 0,
            "weatherSymbol": "partlycloudy",
        }
    ]
}

MOCK_TREND14 = {
    "data": [
        {
            "dateTime": "2026-04-28",
            "isWeekend": False,
            "weekday": "Tue",
            "tempMax": 19.5,
            "tempMaxLow": 16.3,
            "tempMaxHigh": 20.4,
            "tempMin": 9.8,
            "tempMinLow": 5.8,
            "tempMinHigh": 9.8,
            "prec": 0,
            "precLow": 0,
            "precHigh": 0,
            "precProb1mm": 0,
            "precProb10mm": 0,
            "precType": None,
            "precIntensity": None,
            "precWord": None,
            "windGust": 10.7,
            "windGustLow": 9.4,
            "windGustHigh": 12.8,
            "sunMaxPos": 14.5,
            "sunHours": 10.4,
            "sunHoursRelative": 72,
            "sunHoursLow": 7,
            "sunHoursHigh": 12.2,
            "cloudCoverageEighths": 4,
            "cloudWord": "scattered",
            "thunderStorm": None,
            "weatherSymbol": "partlycloudy2",
        }
    ]
}

MOCK_ASTRONOMY = {
    "nextFullMoon": "2026-05-01T19:24:43+02:00",
    "nextNewMoon": "2026-05-16T22:03:07+02:00",
    "dailyData": [
        {
            "dateTime": "2026-04-28",
            "sunrise": "2026-04-28T05:58:11+02:00",
            "sunset": "2026-04-28T20:27:34+02:00",
            "transit": "2026-04-28T13:12:53+02:00",
            "civilDawn": "2026-04-28T05:22:40+02:00",
            "civilDusk": "2026-04-28T21:03:06+02:00",
            "nauticalDawn": "2026-04-28T04:37:39+02:00",
            "nauticalDusk": "2026-04-28T21:48:06+02:00",
            "astronomicalDawn": "2026-04-28T03:45:11+02:00",
            "astronomicalDusk": "2026-04-28T22:40:34+02:00",
            "moonIllumination": 90,
            "moonPhase": 40,
            "moonRise": "2026-04-28T17:20:04+02:00",
            "moonSet": "2026-04-28T04:39:27+02:00",
        }
    ],
}


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    """Mock the KachelmannClient."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        autospec=True,
    ) as mock:
        client = mock.return_value
        client.async_get_current = AsyncMock(return_value=MOCK_CURRENT)
        client.async_get_forecast_1h = AsyncMock(return_value=MOCK_FORECAST_1H)
        client.async_get_forecast_6h = AsyncMock(return_value=MOCK_FORECAST_6H)
        client.async_get_trend14days = AsyncMock(return_value=MOCK_TREND14)
        client.async_get_astronomy = AsyncMock(return_value=MOCK_ASTRONOMY)
        client.rate_limit_remaining = 650
        client.rate_limit_limit = 700
        yield client


@pytest.fixture
def mock_config_entry(hass) -> MockConfigEntry:
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="KachelmannWetter",
        data=MOCK_CONFIG_DATA,
        unique_id=f"{MOCK_LAT}_{MOCK_LON}",
    )
    entry.add_to_hass(hass)
    return entry

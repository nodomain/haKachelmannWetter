"""Tests for KachelmannWetter sensor entities."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_sensors_created(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Test that sensor entities are created."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Check a few key sensors exist
    dew = hass.states.get("sensor.kachelmannwetter_dew_point")
    assert dew is not None
    assert float(dew.state) == -0.8

    precip = hass.states.get("sensor.kachelmannwetter_precipitation_1h")
    assert precip is not None
    assert float(precip.state) == 0.0

    moon = hass.states.get("sensor.kachelmannwetter_moon_illumination")
    assert moon is not None
    assert int(moon.state) == 90


async def test_astronomy_timestamp_sensors(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    """Test that astronomy timestamp sensors return valid datetimes."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    sunrise = hass.states.get("sensor.kachelmannwetter_sunrise")
    assert sunrise is not None
    assert sunrise.state != "unavailable"
    assert "2026-04-28" in sunrise.state

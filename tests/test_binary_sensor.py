"""Tests for KachelmannWetter binary sensor entities."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_binary_sensors_created(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Test that binary sensor entities are created."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    rain = hass.states.get("binary_sensor.kachelmannwetter_rain_expected_3h")
    assert rain is not None
    assert rain.state == "off"  # No rain in mock data

    frost = hass.states.get("binary_sensor.kachelmannwetter_frost_expected_tonight")
    assert frost is not None
    # templow is 9.6 > 0, so no frost
    assert frost.state == "off"

    day = hass.states.get("binary_sensor.kachelmannwetter_daytime")
    assert day is not None
    assert day.state == "on"  # isDay is True in mock

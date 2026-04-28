"""Tests for KachelmannWetter weather entity."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant


async def test_weather_entity_created(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Test weather entity is created with correct state."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("weather.kachelmannwetter")
    assert state is not None
    assert state.state == "partlycloudy"
    assert state.attributes["temperature"] == 18.3
    assert state.attributes["humidity"] == 28
    assert state.attributes["wind_speed"] == 9.0  # 2.5 m/s converted to km/h
    assert state.attributes["attribution"] == "Data provided by KachelmannWetter / Meteologix AG"

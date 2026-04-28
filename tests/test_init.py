"""Tests for KachelmannWetter integration setup."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.kachelmannwetter.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Test successful setup of config entry."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    """Test unloading a config entry."""
    with patch(
        "custom_components.kachelmannwetter.coordinator.KachelmannClient",
        return_value=mock_client,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})

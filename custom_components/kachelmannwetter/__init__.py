"""KachelmannWetter integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import (
    DOMAIN,
    PLATFORMS,
    MANUFACTURER,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    OPTION_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import KachelmannDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KachelmannWetter from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_key = entry.data[CONF_API_KEY]
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    update_interval = entry.options.get(
        OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
    )

    coordinator = KachelmannDataUpdateCoordinator(
        hass,
        config_entry=entry,
        api_key=api_key,
        latitude=latitude,
        longitude=longitude,
        update_interval_seconds=update_interval,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        raise ConfigEntryNotReady from err

    # Use coordinates as device identifier for stable identity across re-adds
    device_id = f"{latitude}_{longitude}"

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device_info": DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="KachelmannWetter",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://kachelmannwetter.com",
        ),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload integration when options change (e.g. update interval)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

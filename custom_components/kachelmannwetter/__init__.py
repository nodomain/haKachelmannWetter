"""KachelmannWetter integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo

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
from .exceptions import InvalidAuth


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
        hass, api_key, latitude, longitude, update_interval_seconds=update_interval
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except InvalidAuth as err:
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device_info": DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KachelmannWetter",
            manufacturer=MANUFACTURER,
            entry_type="service",
            configuration_url="https://kachelmannwetter.com",
        ),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

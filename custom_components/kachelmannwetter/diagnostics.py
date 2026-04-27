"""Diagnostics support for KachelmannWetter."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_API_KEY


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Redact the API key
    config_data = dict(entry.data)
    if CONF_API_KEY in config_data:
        key = config_data[CONF_API_KEY]
        config_data[CONF_API_KEY] = (
            f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        )

    data = coordinator.data or {}

    return {
        "config": config_data,
        "options": dict(entry.options),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "data_summary": {
            "current_weather": data.get("current", {}),
            "forecast_daily_count": len(data.get("forecast_daily", [])),
            "forecast_hourly_count": len(data.get("forecast_hourly", [])),
            "trend14_count": len(data.get("trend14", [])),
            "astronomy_days_count": len(
                data.get("astronomy", {}).get("days", [])
            ),
        },
        "forecast_daily_first": (
            data.get("forecast_daily", [None])[0]
            if data.get("forecast_daily")
            else None
        ),
        "forecast_hourly_first": (
            data.get("forecast_hourly", [None])[0]
            if data.get("forecast_hourly")
            else None
        ),
        "trend14_first": (
            data.get("trend14", [None])[0]
            if data.get("trend14")
            else None
        ),
        "astronomy_today": (
            data.get("astronomy", {}).get("days", [None])[0]
            if data.get("astronomy", {}).get("days")
            else None
        ),
        "astronomy_meta": {
            "next_full_moon": data.get("astronomy", {}).get("next_full_moon"),
            "next_new_moon": data.get("astronomy", {}).get("next_new_moon"),
        },
    }

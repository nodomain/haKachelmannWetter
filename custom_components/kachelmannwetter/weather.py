"""Weather platform for KachelmannWetter integration."""
from __future__ import annotations

from typing import Any
from logging import Logger, getLogger

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME

_LOGGER: Logger = getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug("Adding KachelmannWeather entity for entry %s", entry.entry_id)
    async_add_entities([KachelmannWeather(coordinator, entry)])


class KachelmannWeather(CoordinatorEntity, WeatherEntity):
    """Representation of a KachelmannWetter weather entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter"
    _attr_native_temperature_unit = "°C"
    _attr_native_pressure_unit = "hPa"
    _attr_native_wind_speed_unit = "m/s"
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"

    @property
    def condition(self) -> str | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("condition")

    @property
    def native_temperature(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("temperature")

    @property
    def humidity(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("humidity")

    @property
    def native_pressure(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("pressure")

    @property
    def native_wind_speed(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_speed")

    @property
    def native_wind_gust_speed(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_gust")

    @property
    def wind_bearing(self) -> float | None:
        current = (self.coordinator.data or {}).get("current") or {}
        return current.get("wind_bearing")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        data = (self.coordinator.data or {}).get("forecast") or {}
        return data.get("daily")

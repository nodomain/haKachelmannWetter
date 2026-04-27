"""Weather platform for KachelmannWetter integration."""
from __future__ import annotations

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
    """Set up the KachelmannWetter weather entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KachelmannWeather(data["coordinator"], data["device_info"], entry)])


class KachelmannWeather(CoordinatorEntity, WeatherEntity):
    """Representation of KachelmannWetter weather conditions."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"
    _attr_native_temperature_unit = "°C"
    _attr_native_pressure_unit = "hPa"
    _attr_native_wind_speed_unit = "m/s"
    _attr_native_precipitation_unit = "mm"
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator, device_info, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_device_info = device_info

    def _current(self) -> dict:
        return (self.coordinator.data or {}).get("current") or {}

    # --- Current conditions ---

    @property
    def condition(self) -> str | None:
        return self._current().get("condition")

    @property
    def native_temperature(self) -> float | None:
        return self._current().get("temperature")

    @property
    def humidity(self) -> float | None:
        return self._current().get("humidity")

    @property
    def native_pressure(self) -> float | None:
        return self._current().get("pressure")

    @property
    def native_dew_point(self) -> float | None:
        return self._current().get("dew_point")

    @property
    def cloud_coverage(self) -> int | None:
        return self._current().get("cloud_coverage")

    @property
    def native_wind_speed(self) -> float | None:
        return self._current().get("wind_speed")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._current().get("wind_gust")

    @property
    def wind_bearing(self) -> float | None:
        return self._current().get("wind_bearing")

    # --- Forecasts ---

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast."""
        data = self.coordinator.data or {}
        return data.get("forecast_daily")

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast."""
        data = self.coordinator.data or {}
        return data.get("forecast_hourly")

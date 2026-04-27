"""Weather platform for KachelmannWetter integration."""
from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# Standard HA Forecast keys — used to strip internal _prefixed keys
_FORECAST_KEYS = {
    "datetime", "condition", "cloud_coverage", "humidity",
    "native_dew_point", "native_precipitation", "native_pressure",
    "native_temperature", "native_templow", "native_wind_gust_speed",
    "native_wind_speed", "wind_bearing", "precipitation_probability",
}


def _clean_forecast(raw: list[dict] | None) -> list[Forecast] | None:
    """Strip internal _prefixed keys from forecast dicts."""
    if not raw:
        return None
    return [
        Forecast(**{k: v for k, v in entry.items() if not k.startswith("_")})  # type: ignore[typeddict-item]
        for entry in raw
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the KachelmannWetter weather entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [KachelmannWeather(data["coordinator"], data["device_info"], entry)]
    )


class KachelmannWeather(CoordinatorEntity, WeatherEntity):
    """Representation of KachelmannWetter weather conditions."""

    _attr_has_entity_name = True
    _attr_name = None  # Main feature of device — uses device name
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"
    _attr_native_temperature_unit = "°C"
    _attr_native_pressure_unit = "hPa"
    _attr_native_wind_speed_unit = "m/s"
    _attr_native_precipitation_unit = "mm"
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator, device_info, entry: ConfigEntry) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_device_info = device_info

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        # Notify forecast subscribers that new data is available
        self.hass.async_create_task(
            self.async_update_listeners(("daily", "hourly"))
        )

    def _current(self) -> dict:
        """Return current weather data dict."""
        return (self.coordinator.data or {}).get("current") or {}

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        return self._current().get("condition")

    @property
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current().get("temperature")

    @property
    def humidity(self) -> float | None:
        """Return the current humidity."""
        return self._current().get("humidity")

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure."""
        return self._current().get("pressure")

    @property
    def native_dew_point(self) -> float | None:
        """Return the current dew point."""
        return self._current().get("dew_point")

    @property
    def cloud_coverage(self) -> int | None:
        """Return the current cloud coverage."""
        return self._current().get("cloud_coverage")

    @property
    def native_wind_speed(self) -> float | None:
        """Return the current wind speed."""
        return self._current().get("wind_speed")

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return the current wind gust speed."""
        return self._current().get("wind_gust")

    @property
    def wind_bearing(self) -> float | None:
        """Return the current wind bearing."""
        return self._current().get("wind_bearing")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily forecast with only standard HA keys."""
        data = self.coordinator.data or {}
        return _clean_forecast(data.get("forecast_daily"))

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly forecast with only standard HA keys."""
        data = self.coordinator.data or {}
        return _clean_forecast(data.get("forecast_hourly"))

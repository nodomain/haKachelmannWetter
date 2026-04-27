"""Sensor platform for KachelmannWetter integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from logging import Logger, getLogger

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER: Logger = getLogger(__package__)


@dataclass(frozen=True, kw_only=True)
class KachelmannSensorDescription(SensorEntityDescription):
    """Describe a KachelmannWetter sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


def _get_current(data: dict, key: str) -> Any:
    return data.get("current", {}).get(key)


def _get_daily(data: dict, index: int, key: str) -> Any:
    daily = data.get("forecast_daily", [])
    if len(daily) > index:
        return daily[index].get(key)
    return None


def _get_hourly_now(data: dict, key: str) -> Any:
    """Get a value from the first (nearest) hourly forecast entry."""
    hourly = data.get("forecast_hourly", [])
    if hourly:
        return hourly[0].get(key)
    return None


SENSOR_DESCRIPTIONS: tuple[KachelmannSensorDescription, ...] = (
    # --- Current weather sensors ---
    KachelmannSensorDescription(
        key="dew_point",
        translation_key="dew_point",
        name="Dew point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _get_current(d, "dew_point"),
    ),
    KachelmannSensorDescription(
        key="precipitation_1h",
        translation_key="precipitation_1h",
        name="Precipitation (1h)",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _get_current(d, "precipitation_1h"),
    ),
    KachelmannSensorDescription(
        key="snow_height",
        translation_key="snow_height",
        name="Snow height",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _get_current(d, "snow_height"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_low",
        translation_key="cloud_coverage_low",
        name="Cloud coverage low",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cloud-outline",
        value_fn=lambda d: _get_hourly_now(d, "cloud_coverage_low"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_medium",
        translation_key="cloud_coverage_medium",
        name="Cloud coverage medium",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cloud",
        value_fn=lambda d: _get_hourly_now(d, "cloud_coverage_medium"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_high",
        translation_key="cloud_coverage_high",
        name="Cloud coverage high",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clouds",
        value_fn=lambda d: _get_hourly_now(d, "cloud_coverage_high"),
    ),
    KachelmannSensorDescription(
        key="sun_hours",
        translation_key="sun_hours",
        name="Sunshine duration (1h)",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _get_current(d, "sun_hours"),
    ),
    # --- Today forecast sensors ---
    KachelmannSensorDescription(
        key="global_radiation_today",
        translation_key="global_radiation_today",
        name="Global radiation today",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda d: _get_daily(d, 0, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_today",
        translation_key="sun_hours_today",
        name="Sunshine hours today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _get_daily(d, 0, "_sun_hours"),
    ),
    KachelmannSensorDescription(
        key="wind_gust_max_today",
        translation_key="wind_gust_max_today",
        name="Wind gust max today",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
        value_fn=lambda d: _get_daily(d, 0, "native_wind_gust_speed"),
    ),
    # --- Tomorrow forecast sensors ---
    KachelmannSensorDescription(
        key="global_radiation_tomorrow",
        translation_key="global_radiation_tomorrow",
        name="Global radiation tomorrow",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power-variant",
        value_fn=lambda d: _get_daily(d, 1, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_tomorrow",
        translation_key="sun_hours_tomorrow",
        name="Sunshine hours tomorrow",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny-alert",
        value_fn=lambda d: _get_daily(d, 1, "_sun_hours"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KachelmannWetter sensor entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    device_info = entry_data["device_info"]

    async_add_entities(
        KachelmannSensor(coordinator, device_info, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class KachelmannSensor(CoordinatorEntity, SensorEntity):
    """A KachelmannWetter sensor entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"

    def __init__(
        self,
        coordinator,
        device_info,
        entry: ConfigEntry,
        description: KachelmannSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})

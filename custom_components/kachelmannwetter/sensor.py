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
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPrecipitationDepth,
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


SENSOR_DESCRIPTIONS: tuple[KachelmannSensorDescription, ...] = (
    KachelmannSensorDescription(
        key="precipitation_1h",
        translation_key="precipitation_1h",
        name="Precipitation (1h)",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("current", {}).get("precipitation_1h"),
    ),
    KachelmannSensorDescription(
        key="snow_height",
        translation_key="snow_height",
        name="Snow height",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("current", {}).get("snow_height"),
    ),
    KachelmannSensorDescription(
        key="sun_hours",
        translation_key="sun_hours",
        name="Sunshine duration (1h)",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: d.get("current", {}).get("sun_hours"),
    ),
    KachelmannSensorDescription(
        key="global_radiation_today",
        translation_key="global_radiation_today",
        name="Global radiation (today forecast)",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda d: _today_radiation(d),
    ),
    KachelmannSensorDescription(
        key="sun_hours_today",
        translation_key="sun_hours_today",
        name="Sunshine hours (today forecast)",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _today_sun_hours(d),
    ),
)


def _today_radiation(data: dict) -> float | None:
    """Get today's total global radiation from daily forecast."""
    daily = data.get("forecast_daily", [])
    if daily:
        return daily[0].get("_global_radiation")
    return None


def _today_sun_hours(data: dict) -> float | None:
    """Get today's total sunshine hours from daily forecast."""
    daily = data.get("forecast_daily", [])
    if daily:
        return daily[0].get("_sun_hours")
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KachelmannWetter sensor entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    device_info = entry_data["device_info"]

    entities = [
        KachelmannSensor(coordinator, device_info, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


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

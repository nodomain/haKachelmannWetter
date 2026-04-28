"""Sensor platform for KachelmannWetter integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER: Logger = getLogger(__package__)


@dataclass(frozen=True, kw_only=True)
class KachelmannSensorDescription(SensorEntityDescription):
    """Describe a KachelmannWetter sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


# --- Helper accessors ---


def _cur(data: dict, key: str) -> Any:
    return data.get("current", {}).get(key)


def _daily(data: dict, idx: int, key: str) -> Any:
    d = data.get("forecast_daily", [])
    return d[idx].get(key) if len(d) > idx else None


def _trend(data: dict, idx: int, key: str) -> Any:
    t = data.get("trend14", [])
    return t[idx].get(key) if len(t) > idx else None


def _hourly_now(data: dict, key: str) -> Any:
    h = data.get("forecast_hourly", [])
    return h[0].get(key) if h else None


def _astro_today(data: dict, key: str) -> Any:
    days = data.get("astronomy", {}).get("days", [])
    return days[0].get(key) if days else None


def _astro(data: dict, key: str) -> Any:
    return data.get("astronomy", {}).get(key)


def _parse_ts(val: str | None) -> datetime | None:
    """Parse an ISO timestamp string to a tz-aware datetime for HA TIMESTAMP sensors."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def _astro_today_ts(data: dict, key: str) -> datetime | None:
    return _parse_ts(_astro_today(data, key))


def _astro_ts(data: dict, key: str) -> datetime | None:
    return _parse_ts(_astro(data, key))


# All sensor descriptions. Names come from translations via translation_key,
# icons come from icons.json via translation_key. No hardcoded name= or icon=.

SENSOR_DESCRIPTIONS: tuple[KachelmannSensorDescription, ...] = (
    # ===== Current weather sensors =====
    KachelmannSensorDescription(
        key="dew_point",
        translation_key="dew_point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "dew_point"),
    ),
    KachelmannSensorDescription(
        key="precipitation_1h",
        translation_key="precipitation_1h",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "precipitation_1h"),
    ),
    KachelmannSensorDescription(
        key="snow_height",
        translation_key="snow_height",
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "snow_height"),
    ),
    KachelmannSensorDescription(
        key="snow_amount",
        translation_key="snow_amount",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "snow_amount"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_current",
        translation_key="sun_hours_current",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "sun_hours"),
    ),
    # ===== Cloud coverage from hourly forecast =====
    KachelmannSensorDescription(
        key="cloud_coverage_low",
        translation_key="cloud_coverage_low",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_low"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_medium",
        translation_key="cloud_coverage_medium",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_medium"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_high",
        translation_key="cloud_coverage_high",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_high"),
    ),
    KachelmannSensorDescription(
        key="global_radiation_hourly",
        translation_key="global_radiation_hourly",
        native_unit_of_measurement="Wh/m²",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _hourly_now(d, "_global_radiation"),
    ),
    # ===== Today forecast sensors =====
    KachelmannSensorDescription(
        key="global_radiation_today",
        translation_key="global_radiation_today",
        native_unit_of_measurement="Wh/m²",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _daily(d, 0, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_today",
        translation_key="sun_hours_today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _daily(d, 0, "_sun_hours"),
    ),
    KachelmannSensorDescription(
        key="wind_gust_max_today",
        translation_key="wind_gust_max_today",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _daily(d, 0, "native_wind_gust_speed"),
    ),
    # ===== Tomorrow forecast sensors =====
    KachelmannSensorDescription(
        key="global_radiation_tomorrow",
        translation_key="global_radiation_tomorrow",
        native_unit_of_measurement="Wh/m²",
        value_fn=lambda d: _daily(d, 1, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_tomorrow",
        translation_key="sun_hours_tomorrow",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda d: _daily(d, 1, "_sun_hours"),
    ),
    # ===== 14-day trend sensors =====
    KachelmannSensorDescription(
        key="precipitation_probability_today",
        translation_key="precipitation_probability_today",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _trend(d, 0, "precipitation_probability_1mm"),
    ),
    KachelmannSensorDescription(
        key="precipitation_probability_tomorrow",
        translation_key="precipitation_probability_tomorrow",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: _trend(d, 1, "precipitation_probability_1mm"),
    ),
    KachelmannSensorDescription(
        key="precipitation_today",
        translation_key="precipitation_today",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda d: _trend(d, 0, "precipitation"),
    ),
    KachelmannSensorDescription(
        key="precipitation_tomorrow",
        translation_key="precipitation_tomorrow",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        value_fn=lambda d: _trend(d, 1, "precipitation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_relative_today",
        translation_key="sun_hours_relative_today",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _trend(d, 0, "sun_hours_relative"),
    ),
    KachelmannSensorDescription(
        key="sun_max_possible_today",
        translation_key="sun_max_possible_today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda d: _trend(d, 0, "sun_max_possible"),
    ),
    KachelmannSensorDescription(
        key="wind_gust_trend_today",
        translation_key="wind_gust_trend_today",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _trend(d, 0, "wind_gust"),
    ),
    KachelmannSensorDescription(
        key="wind_gust_trend_tomorrow",
        translation_key="wind_gust_trend_tomorrow",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        value_fn=lambda d: _trend(d, 1, "wind_gust"),
    ),
    # ===== Astronomy sensors =====
    KachelmannSensorDescription(
        key="sunrise",
        translation_key="sunrise",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "sunrise"),
    ),
    KachelmannSensorDescription(
        key="sunset",
        translation_key="sunset",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "sunset"),
    ),
    KachelmannSensorDescription(
        key="solar_transit",
        translation_key="solar_transit",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "transit"),
    ),
    KachelmannSensorDescription(
        key="civil_dawn",
        translation_key="civil_dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "civil_dawn"),
    ),
    KachelmannSensorDescription(
        key="civil_dusk",
        translation_key="civil_dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "civil_dusk"),
    ),
    KachelmannSensorDescription(
        key="nautical_dawn",
        translation_key="nautical_dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today_ts(d, "nautical_dawn"),
    ),
    KachelmannSensorDescription(
        key="nautical_dusk",
        translation_key="nautical_dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today_ts(d, "nautical_dusk"),
    ),
    KachelmannSensorDescription(
        key="astronomical_dawn",
        translation_key="astronomical_dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today_ts(d, "astronomical_dawn"),
    ),
    KachelmannSensorDescription(
        key="astronomical_dusk",
        translation_key="astronomical_dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today_ts(d, "astronomical_dusk"),
    ),
    KachelmannSensorDescription(
        key="moon_illumination",
        translation_key="moon_illumination",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _astro_today(d, "moon_illumination"),
    ),
    KachelmannSensorDescription(
        key="moon_phase",
        translation_key="moon_phase",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _astro_today(d, "moon_phase"),
    ),
    KachelmannSensorDescription(
        key="moon_rise",
        translation_key="moon_rise",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "moon_rise"),
    ),
    KachelmannSensorDescription(
        key="moon_set",
        translation_key="moon_set",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_today_ts(d, "moon_set"),
    ),
    KachelmannSensorDescription(
        key="next_full_moon",
        translation_key="next_full_moon",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_ts(d, "next_full_moon"),
    ),
    KachelmannSensorDescription(
        key="next_new_moon",
        translation_key="next_new_moon",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _astro_ts(d, "next_new_moon"),
    ),
    # ===== Diagnostic =====
    KachelmannSensorDescription(
        key="api_requests_remaining",
        translation_key="api_requests_remaining",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("rate_limit", {}).get("remaining"),
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

    entities: list[SensorEntity] = [
        KachelmannSensor(coordinator, device_info, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    ]
    # Add the 14-day trend overview sensor with all data as attributes
    entities.append(
        KachelmannTrendSensor(coordinator, device_info, entry)
    )
    async_add_entities(entities)


class KachelmannSensor(CoordinatorEntity, SensorEntity):
    """A KachelmannWetter sensor entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"
    entity_description: KachelmannSensorDescription

    def __init__(self, coordinator, device_info, entry, description) -> None:
        """Set up the instance."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})


class KachelmannTrendSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing the full 14-day trend as attributes.

    State: number of forecast days available.
    Attributes: complete trend14 data array, accessible via templates like:
      {{ state_attr('sensor.kachelmannwetter_trend_14day', 'days')[2].temp_max }}
    """

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"
    _attr_translation_key = "trend_14day"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_info, entry: ConfigEntry) -> None:
        """Set up the instance."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_trend_14day"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int | None:
        """Return the number of trend days available."""
        trend = (self.coordinator.data or {}).get("trend14", [])
        return len(trend) if trend else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the full 14-day trend data as attributes."""
        trend = (self.coordinator.data or {}).get("trend14", [])
        if not trend:
            return None
        return {"days": trend}

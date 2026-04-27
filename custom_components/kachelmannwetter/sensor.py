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


SENSOR_DESCRIPTIONS: tuple[KachelmannSensorDescription, ...] = (
    # ===== Current weather sensors =====
    KachelmannSensorDescription(
        key="dew_point",
        translation_key="dew_point",
        name="Dew point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "dew_point"),
    ),
    KachelmannSensorDescription(
        key="precipitation_1h",
        translation_key="precipitation_1h",
        name="Precipitation (1h)",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "precipitation_1h"),
    ),
    KachelmannSensorDescription(
        key="snow_height",
        translation_key="snow_height",
        name="Snow height",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _cur(d, "snow_height"),
    ),
    KachelmannSensorDescription(
        key="snow_amount",
        translation_key="snow_amount",
        name="Fresh snow",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:snowflake",
        value_fn=lambda d: _cur(d, "snow_amount"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_current",
        translation_key="sun_hours_current",
        name="Sunshine duration (1h)",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _cur(d, "sun_hours"),
    ),
    # ===== Cloud coverage from hourly forecast =====
    KachelmannSensorDescription(
        key="cloud_coverage_low",
        translation_key="cloud_coverage_low",
        name="Cloud coverage low",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cloud-outline",
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_low"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_medium",
        translation_key="cloud_coverage_medium",
        name="Cloud coverage medium",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cloud",
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_medium"),
    ),
    KachelmannSensorDescription(
        key="cloud_coverage_high",
        translation_key="cloud_coverage_high",
        name="Cloud coverage high",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clouds",
        value_fn=lambda d: _hourly_now(d, "cloud_coverage_high"),
    ),
    KachelmannSensorDescription(
        key="global_radiation_hourly",
        translation_key="global_radiation_hourly",
        name="Global radiation (current hour)",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda d: _hourly_now(d, "_global_radiation"),
    ),
    # ===== Today forecast sensors (from 6h aggregation) =====
    KachelmannSensorDescription(
        key="global_radiation_today",
        translation_key="global_radiation_today",
        name="Global radiation today",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda d: _daily(d, 0, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_today",
        translation_key="sun_hours_today",
        name="Sunshine hours today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _daily(d, 0, "_sun_hours"),
    ),
    KachelmannSensorDescription(
        key="wind_gust_max_today",
        translation_key="wind_gust_max_today",
        name="Wind gust max today",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
        value_fn=lambda d: _daily(d, 0, "native_wind_gust_speed"),
    ),
    # ===== Tomorrow forecast sensors =====
    KachelmannSensorDescription(
        key="global_radiation_tomorrow",
        translation_key="global_radiation_tomorrow",
        name="Global radiation tomorrow",
        native_unit_of_measurement="Wh/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power-variant",
        value_fn=lambda d: _daily(d, 1, "_global_radiation"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_tomorrow",
        translation_key="sun_hours_tomorrow",
        name="Sunshine hours tomorrow",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny-alert",
        value_fn=lambda d: _daily(d, 1, "_sun_hours"),
    ),
    # ===== 14-day trend sensors =====
    KachelmannSensorDescription(
        key="precipitation_probability_today",
        translation_key="precipitation_probability_today",
        name="Precipitation probability today",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-rainy",
        value_fn=lambda d: _trend(d, 0, "precipitation_probability_1mm"),
    ),
    KachelmannSensorDescription(
        key="precipitation_probability_tomorrow",
        translation_key="precipitation_probability_tomorrow",
        name="Precipitation probability tomorrow",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-rainy",
        value_fn=lambda d: _trend(d, 1, "precipitation_probability_1mm"),
    ),
    KachelmannSensorDescription(
        key="sun_hours_relative_today",
        translation_key="sun_hours_relative_today",
        name="Sunshine relative today",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda d: _trend(d, 0, "sun_hours_relative"),
    ),
    # ===== Astronomy sensors =====
    KachelmannSensorDescription(
        key="sunrise",
        translation_key="sunrise",
        name="Sunrise",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-up",
        value_fn=lambda d: _astro_today(d, "sunrise"),
    ),
    KachelmannSensorDescription(
        key="sunset",
        translation_key="sunset",
        name="Sunset",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-down",
        value_fn=lambda d: _astro_today(d, "sunset"),
    ),
    KachelmannSensorDescription(
        key="solar_transit",
        translation_key="solar_transit",
        name="Solar transit",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:sun-clock",
        value_fn=lambda d: _astro_today(d, "transit"),
    ),
    KachelmannSensorDescription(
        key="civil_dawn",
        translation_key="civil_dawn",
        name="Civil dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-up",
        value_fn=lambda d: _astro_today(d, "civil_dawn"),
    ),
    KachelmannSensorDescription(
        key="civil_dusk",
        translation_key="civil_dusk",
        name="Civil dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-down",
        value_fn=lambda d: _astro_today(d, "civil_dusk"),
    ),
    KachelmannSensorDescription(
        key="nautical_dawn",
        translation_key="nautical_dawn",
        name="Nautical dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-up",
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today(d, "nautical_dawn"),
    ),
    KachelmannSensorDescription(
        key="nautical_dusk",
        translation_key="nautical_dusk",
        name="Nautical dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-down",
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today(d, "nautical_dusk"),
    ),
    KachelmannSensorDescription(
        key="astronomical_dawn",
        translation_key="astronomical_dawn",
        name="Astronomical dawn",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-night",
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today(d, "astronomical_dawn"),
    ),
    KachelmannSensorDescription(
        key="astronomical_dusk",
        translation_key="astronomical_dusk",
        name="Astronomical dusk",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-night",
        entity_registry_enabled_default=False,
        value_fn=lambda d: _astro_today(d, "astronomical_dusk"),
    ),
    KachelmannSensorDescription(
        key="moon_illumination",
        translation_key="moon_illumination",
        name="Moon illumination",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:moon-waning-gibbous",
        value_fn=lambda d: _astro_today(d, "moon_illumination"),
    ),
    KachelmannSensorDescription(
        key="moon_phase",
        translation_key="moon_phase",
        name="Moon phase",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:moon-waning-gibbous",
        value_fn=lambda d: _astro_today(d, "moon_phase"),
    ),
    KachelmannSensorDescription(
        key="moon_rise",
        translation_key="moon_rise",
        name="Moonrise",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:moon-rising",
        value_fn=lambda d: _astro_today(d, "moon_rise"),
    ),
    KachelmannSensorDescription(
        key="moon_set",
        translation_key="moon_set",
        name="Moonset",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:moon-setting",
        value_fn=lambda d: _astro_today(d, "moon_set"),
    ),
    KachelmannSensorDescription(
        key="next_full_moon",
        translation_key="next_full_moon",
        name="Next full moon",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:moon-full",
        value_fn=lambda d: _astro(d, "next_full_moon"),
    ),
    KachelmannSensorDescription(
        key="next_new_moon",
        translation_key="next_new_moon",
        name="Next new moon",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:moon-new",
        value_fn=lambda d: _astro(d, "next_new_moon"),
    ),
    # ===== Rate limit =====
    KachelmannSensorDescription(
        key="api_requests_remaining",
        translation_key="api_requests_remaining",
        name="API requests remaining",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:api",
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

    async_add_entities(
        KachelmannSensor(coordinator, device_info, entry, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class KachelmannSensor(CoordinatorEntity, SensorEntity):
    """A KachelmannWetter sensor entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"

    def __init__(self, coordinator, device_info, entry, description) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})

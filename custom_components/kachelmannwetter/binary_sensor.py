"""Binary sensor platform for KachelmannWetter integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class KachelmannBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a KachelmannWetter binary sensor."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]


def _rain_expected_3h(data: dict) -> bool | None:
    """Check if rain is expected in the next 3 hours from hourly forecast."""
    hourly = data.get("forecast_hourly", [])
    if not hourly:
        return None
    now = datetime.now(UTC)
    cutoff = now + timedelta(hours=3)
    for entry in hourly:
        dt_str = entry.get("datetime", "")
        if not dt_str:
            continue
        try:
            dt = datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            continue
        if dt > cutoff:
            break
        precip = entry.get("native_precipitation")
        if precip is not None and precip > 0:
            return True
        condition = entry.get("condition", "")
        if condition in ("rainy", "pouring", "lightning-rainy", "snowy-rainy"):
            return True
    return False


def _frost_expected_tonight(data: dict) -> bool | None:
    """Check if frost (< 0°C) is expected tonight from daily forecast."""
    daily = data.get("forecast_daily", [])
    if not daily:
        return None
    templow = daily[0].get("native_templow")
    if templow is None:
        return None
    return templow < 0


def _thunderstorm_expected(data: dict) -> bool | None:
    """Check if thunderstorm is expected from trend14 data."""
    trend = data.get("trend14", [])
    if not trend:
        return None
    for day in trend[:2]:
        ts = day.get("thunderstorm")
        if ts is not None and ts:
            return True
    return False


def _is_day(data: dict) -> bool | None:
    """Return whether it's currently daytime."""
    return data.get("current", {}).get("is_day")


# Names and icons come from translations (strings.json) and icons.json
# via translation_key. No hardcoded name= or icon=.

BINARY_SENSOR_DESCRIPTIONS: tuple[KachelmannBinarySensorDescription, ...] = (
    KachelmannBinarySensorDescription(
        key="rain_expected_3h",
        translation_key="rain_expected_3h",
        is_on_fn=_rain_expected_3h,
    ),
    KachelmannBinarySensorDescription(
        key="frost_expected_tonight",
        translation_key="frost_expected_tonight",
        device_class=BinarySensorDeviceClass.COLD,
        is_on_fn=_frost_expected_tonight,
    ),
    KachelmannBinarySensorDescription(
        key="thunderstorm_expected",
        translation_key="thunderstorm_expected",
        device_class=BinarySensorDeviceClass.SAFETY,
        is_on_fn=_thunderstorm_expected,
    ),
    KachelmannBinarySensorDescription(
        key="is_day",
        translation_key="is_day",
        device_class=BinarySensorDeviceClass.LIGHT,
        is_on_fn=_is_day,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KachelmannWetter binary sensor entities."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    device_info = entry_data["device_info"]

    async_add_entities(
        KachelmannBinarySensor(coordinator, device_info, entry, desc)
        for desc in BINARY_SENSOR_DESCRIPTIONS
    )


class KachelmannBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A KachelmannWetter binary sensor entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by KachelmannWetter / Meteologix AG"
    entity_description: KachelmannBinarySensorDescription

    def __init__(self, coordinator, device_info, entry, description) -> None:
        """Set up the instance."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator.data or {})

"""DataUpdateCoordinator for KachelmannWetter."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .client import KachelmannClient
from .const import DEFAULT_UPDATE_INTERVAL
from .exceptions import InvalidAuth, RateLimitError
from .helpers import (
    normalize_astronomy,
    normalize_current,
    normalize_daily_from_6h,
    normalize_hourly,
    normalize_trend14,
)

_LOGGER: Logger = getLogger(__package__)


class KachelmannDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch all data from KachelmannWetter API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_key: str,
        latitude: float,
        longitude: float,
        update_interval_seconds: int | None = None,
    ) -> None:
        """Initialize the coordinator."""
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.client = KachelmannClient(hass, api_key)

        if update_interval_seconds is None:
            update_interval_seconds = DEFAULT_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name="kachelmannwetter",
            config_entry=config_entry,
            update_interval=timedelta(seconds=update_interval_seconds),
        )

    async def _async_update_data(self) -> dict:
        """Fetch all endpoints in parallel and normalize."""
        lat, lon = self.latitude, self.longitude
        _LOGGER.debug("Updating data for configured location")
        try:
            # Fetch all endpoints in parallel
            (
                current_raw,
                forecast_1h_raw,
                forecast_6h_raw,
                trend14_raw,
                astronomy_raw,
            ) = await asyncio.gather(
                self.client.async_get_current(lat, lon),
                self.client.async_get_forecast_1h(lat, lon),
                self.client.async_get_forecast_6h(lat, lon),
                self.client.async_get_trend14days(lat, lon),
                self.client.async_get_astronomy(lat, lon),
            )

            # Normalize
            current = normalize_current(current_raw or {})
            hourly = normalize_hourly(forecast_1h_raw or {})
            daily = normalize_daily_from_6h(forecast_6h_raw or {})
            trend14 = normalize_trend14(trend14_raw or {})
            astronomy = normalize_astronomy(astronomy_raw or {})

            # Enrich daily forecast with trend14 data
            _enrich_daily_with_trend(daily, trend14)

            return {
                "current": current,
                "forecast_hourly": hourly,
                "forecast_daily": daily,
                "trend14": trend14,
                "astronomy": astronomy,
                "rate_limit": {
                    "remaining": self.client.rate_limit_remaining,
                    "limit": self.client.rate_limit_limit,
                },
            }

        except RateLimitError as err:
            retry = err.retry_after
            _LOGGER.warning("Rate limited by Kachelmann API, retry after %s s", retry)
            if retry:
                async_call_later(
                    self.hass,
                    retry,
                    lambda _now: self.async_request_refresh(),
                )
            raise UpdateFailed("Rate limited by Kachelmann API") from err

        except InvalidAuth as err:
            raise ConfigEntryAuthFailed from err

        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err


def _enrich_daily_with_trend(daily: list[dict], trend14: list[dict]) -> None:
    """Merge precipitation_probability from trend14 into daily forecasts."""
    trend_by_date: dict[str, dict] = {}
    for t in trend14:
        d = t.get("date")
        if d:
            trend_by_date[d] = t

    for day in daily:
        dt_str = day.get("datetime", "")
        date_only = dt_str[:10] if dt_str else ""
        trend = trend_by_date.get(date_only, {})
        if trend:
            day["precipitation_probability"] = trend.get("precipitation_probability_1mm")
            day["_precipitation_probability_10mm"] = trend.get("precipitation_probability_10mm")
            day["_precipitation_type"] = trend.get("precipitation_type")
            day["_precipitation_word"] = trend.get("precipitation_word")
            day["_thunderstorm"] = trend.get("thunderstorm")
            day["_sun_hours_relative"] = trend.get("sun_hours_relative")

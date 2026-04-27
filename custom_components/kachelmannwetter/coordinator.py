"""DataUpdateCoordinator for KachelmannWetter."""
from __future__ import annotations

from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_call_later

from .client import KachelmannClient
from .exceptions import RateLimitError, InvalidAuth
from .helpers import normalize_current, normalize_daily, normalize_hourly
from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER: Logger = getLogger(__package__)


class KachelmannDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch current + daily + hourly data from KachelmannWetter API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        latitude: float,
        longitude: float,
        update_interval_seconds: int | None = None,
    ) -> None:
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
            update_interval=timedelta(seconds=update_interval_seconds),
        )

    async def _async_update_data(self) -> dict:
        """Fetch all data from the API and normalize it."""
        _LOGGER.debug("Updating data for %s,%s", self.latitude, self.longitude)
        try:
            current_raw = await self.client.async_get_current(
                self.latitude, self.longitude
            )
            forecast_6h_raw = await self.client.async_get_forecast_6h(
                self.latitude, self.longitude
            )
            forecast_1h_raw = await self.client.async_get_forecast_1h(
                self.latitude, self.longitude
            )

            current = normalize_current(current_raw or {})
            daily = normalize_daily(forecast_6h_raw or {})
            hourly = normalize_hourly(forecast_1h_raw or {})

            return {
                "current": current,
                "forecast_daily": daily,
                "forecast_hourly": hourly,
            }

        except RateLimitError as err:
            retry = err.retry_after
            _LOGGER.warning(
                "Rate limited by Kachelmann API, retry after %s s", retry
            )
            if retry:
                async_call_later(
                    self.hass,
                    retry,
                    lambda _now: self.async_request_refresh(),
                )
            raise UpdateFailed("Rate limited by Kachelmann API") from err

        except InvalidAuth:
            # Let HA trigger reauth flow
            raise

        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

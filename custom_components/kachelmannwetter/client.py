"""Async client for KachelmannWetter API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE
from .exceptions import InvalidAuth, RateLimitError

_LOGGER = logging.getLogger(__name__)


class KachelmannClient:
    """Thin async wrapper around the Kachelmann v02 API."""

    def __init__(self, hass: HomeAssistant, api_key: str) -> None:
        self._session = async_get_clientsession(hass)
        self._api_key = api_key
        self.rate_limit_remaining: int | None = None
        self.rate_limit_limit: int | None = None

    async def _get(self, url: str) -> dict[str, Any]:
        headers = {"X-API-Key": self._api_key}
        _LOGGER.debug("GET %s", url)
        resp = await self._session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        )

        if resp.status == 401:
            raise InvalidAuth("Invalid API key")
        if resp.status == 403:
            raise InvalidAuth("Forbidden — check API location settings")
        if resp.status == 429:
            retry_after = None
            for hdr in ("Retry-After", "x-ratelimit-retry-after"):
                if hdr in resp.headers:
                    try:
                        retry_after = int(resp.headers[hdr])
                    except (ValueError, TypeError):
                        pass
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)

        # Track rate limit from response headers
        if "x-ratelimit-remaining" in resp.headers:
            try:
                self.rate_limit_remaining = int(resp.headers["x-ratelimit-remaining"])
            except (ValueError, TypeError):
                pass
        if "x-ratelimit-limit" in resp.headers:
            try:
                self.rate_limit_limit = int(resp.headers["x-ratelimit-limit"])
            except (ValueError, TypeError):
                pass

        resp.raise_for_status()
        return await resp.json()

    # --- Current Weather ---

    async def async_get_current(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch current weather conditions."""
        return await self._get(f"{API_BASE}/current/{latitude}/{longitude}")

    # --- Forecasts ---

    async def async_get_forecast_1h(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch hourly forecast (24h ahead, advanced parameters)."""
        return await self._get(
            f"{API_BASE}/forecast/{latitude}/{longitude}/advanced/1h"
        )

    async def async_get_forecast_6h(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch 6-hourly forecast (advanced parameters, ~10 days)."""
        return await self._get(
            f"{API_BASE}/forecast/{latitude}/{longitude}/advanced/6h"
        )

    async def async_get_trend14days(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch 14-day trend forecast with precipitation probability."""
        return await self._get(
            f"{API_BASE}/forecast/{latitude}/{longitude}/trend14days"
        )

    # --- Tools ---

    async def async_get_astronomy(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch astronomical data (sun/moon rise/set, moon phase)."""
        return await self._get(
            f"{API_BASE}/tools/astronomy/{latitude}/{longitude}"
        )

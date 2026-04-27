"""Async client for KachelmannWetter API."""
from __future__ import annotations

from typing import Any
import logging

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

    async def _get(self, url: str) -> dict[str, Any]:
        headers = {"X-API-Key": self._api_key}
        _LOGGER.debug("GET %s", url)
        resp = await self._session.get(url, headers=headers)

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

        # Log rate-limit info for debugging
        remaining = resp.headers.get("x-ratelimit-remaining")
        if remaining is not None:
            _LOGGER.debug("Rate limit remaining: %s", remaining)

        resp.raise_for_status()
        return await resp.json()

    async def async_get_current(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch current weather conditions."""
        return await self._get(f"{API_BASE}/current/{latitude}/{longitude}")

    async def async_get_forecast_6h(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch 6-hourly forecast (used for daily aggregation)."""
        return await self._get(
            f"{API_BASE}/forecast/{latitude}/{longitude}/advanced/6h"
        )

    async def async_get_forecast_1h(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        """Fetch hourly forecast (24h ahead)."""
        return await self._get(
            f"{API_BASE}/forecast/{latitude}/{longitude}/advanced/1h"
        )

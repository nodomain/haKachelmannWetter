"""Tests for KachelmannWetter config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kachelmannwetter.const import DOMAIN
from custom_components.kachelmannwetter.exceptions import InvalidAuth

from .conftest import MOCK_CONFIG_DATA, MOCK_CURRENT, MOCK_LAT, MOCK_LON


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """Test successful user config flow."""
    with patch(
        "custom_components.kachelmannwetter.config_flow.KachelmannClient",
    ) as mock_client_cls:
        mock_client_cls.return_value.async_get_current = AsyncMock(return_value=MOCK_CURRENT)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], MOCK_CONFIG_DATA)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == f"KachelmannWetter ({MOCK_LAT}, {MOCK_LON})"
        assert result["data"] == MOCK_CONFIG_DATA


async def test_user_flow_auth_error(hass: HomeAssistant) -> None:
    """Test config flow with invalid API key."""
    with patch(
        "custom_components.kachelmannwetter.config_flow.KachelmannClient",
    ) as mock_client_cls:
        mock_client_cls.return_value.async_get_current = AsyncMock(
            side_effect=InvalidAuth("bad key")
        )

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], MOCK_CONFIG_DATA)
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "auth"}


async def test_user_flow_connect_error(hass: HomeAssistant) -> None:
    """Test config flow with connection error."""
    with patch(
        "custom_components.kachelmannwetter.config_flow.KachelmannClient",
    ) as mock_client_cls:
        mock_client_cls.return_value.async_get_current = AsyncMock(side_effect=Exception("timeout"))

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], MOCK_CONFIG_DATA)
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_duplicate(hass: HomeAssistant) -> None:
    """Test config flow aborts on duplicate location."""
    with patch(
        "custom_components.kachelmannwetter.config_flow.KachelmannClient",
    ) as mock_client_cls:
        mock_client_cls.return_value.async_get_current = AsyncMock(return_value=MOCK_CURRENT)

        # First entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], MOCK_CONFIG_DATA)
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Second entry with same coords
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], MOCK_CONFIG_DATA)
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"

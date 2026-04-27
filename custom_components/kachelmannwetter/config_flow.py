"""Config flow for KachelmannWetter integration."""
from __future__ import annotations

from typing import Any
from logging import Logger, getLogger

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    OPTION_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
)
from .client import KachelmannClient
from .exceptions import InvalidAuth

_LOGGER: Logger = getLogger(__package__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_LATITUDE): vol.Coerce(float),
        vol.Required(CONF_LONGITUDE): vol.Coerce(float),
    }
)


class KachelmannConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KachelmannWetter."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]

            # Set unique ID based on coordinates to prevent duplicates
            unique_id = f"{lat}_{lon}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            client = KachelmannClient(self.hass, api_key)
            try:
                await client.async_get_current(lat, lon)
            except InvalidAuth:
                errors["base"] = "auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"KachelmannWetter ({lat}, {lon})", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=self._get_user_schema(), errors=errors
        )

    def _get_user_schema(self) -> vol.Schema:
        """Return the user schema with home coordinates as defaults."""
        return vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(
                    CONF_LATITUDE, default=self.hass.config.latitude
                ): vol.Coerce(float),
                vol.Required(
                    CONF_LONGITUDE, default=self.hass.config.longitude
                ): vol.Coerce(float),
            }
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            reauth_entry = self._get_reauth_entry()
            client = KachelmannClient(self.hass, api_key)
            try:
                await client.async_get_current(
                    reauth_entry.data[CONF_LATITUDE],
                    reauth_entry.data[CONF_LONGITUDE],
                )
            except InvalidAuth:
                errors["base"] = "auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> KachelmannOptionsFlow:
        """Get the options flow for this handler."""
        return KachelmannOptionsFlow()


class KachelmannOptionsFlow(config_entries.OptionsFlow):
    """Handle options for KachelmannWetter."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            OPTION_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    OPTION_UPDATE_INTERVAL,
                    default=current_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

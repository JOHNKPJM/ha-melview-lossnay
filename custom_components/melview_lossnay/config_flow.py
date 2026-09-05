"""Config flow for Mitsubishi Lossnay via Melview."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MelviewApi, MelviewAuthError, MelviewError
from .const import CONF_APP_VERSION, DEFAULT_APP_VERSION, DOMAIN


class MelviewLossnayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mitsubishi Lossnay."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle initial UI setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            api = MelviewApi(
                async_get_clientsession(self.hass),
                username,
                password,
                DEFAULT_APP_VERSION,
            )

            try:
                await api.async_login()
                units = await api.async_get_units(erv_only=True)
            except MelviewAuthError:
                errors["base"] = "invalid_auth"
            except MelviewError:
                errors["base"] = "cannot_connect"
            else:
                if not units:
                    errors["base"] = "no_erv"
                else:
                    await self.async_set_unique_id(username.lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Mitsubishi Lossnay",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_APP_VERSION: DEFAULT_APP_VERSION,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

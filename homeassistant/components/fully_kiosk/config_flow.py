"""Config flow for Fully Kiosk Browser integration."""
from __future__ import annotations

import asyncio
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
from fullykiosk import FullyKiosk
from fullykiosk.exceptions import FullyKioskError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN, LOGGER


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fully Kiosk Browser."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            fully = FullyKiosk(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                DEFAULT_PORT,
                user_input[CONF_PASSWORD],
            )

            try:
                async with timeout(15):
                    device_info = await fully.getDeviceInfo()
            except (ClientConnectorError, FullyKioskError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device_info["deviceID"])
                self._abort_if_unique_id_configured(updates=user_input)
                return self.async_create_entry(
                    title=device_info["deviceName"], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

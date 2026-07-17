"""Config flow for Cure Afvalbeheer."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class CureAfvalbeheerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cure Afvalbeheer."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Cure Afvalbeheer",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=None,
        )

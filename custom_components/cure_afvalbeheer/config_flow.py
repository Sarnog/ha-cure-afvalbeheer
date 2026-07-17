"""Config flow for Cure Afvalbeheer."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_LOOKAHEAD_DAYS,
    CONF_MUNICIPALITY,
    DEFAULT_LOOKAHEAD_DAYS,
    DOMAIN,
    MUNICIPALITIES,
)

_MUNICIPALITY_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[
            selector.SelectOptionDict(value=slug, label=name)
            for slug, name in MUNICIPALITIES.items()
        ],
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)


class CureAfvalbeheerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cure Afvalbeheer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""

        if user_input is not None:
            municipality = user_input[CONF_MUNICIPALITY]

            await self.async_set_unique_id(municipality)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=MUNICIPALITIES[municipality],
                data={CONF_MUNICIPALITY: municipality},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MUNICIPALITY): _MUNICIPALITY_SELECTOR,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for this handler."""

        return CureOptionsFlow()


class CureOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle an options flow for Cure Afvalbeheer."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_lookahead_days = self.config_entry.options.get(
            CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOOKAHEAD_DAYS, default=current_lookahead_days
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=30,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )

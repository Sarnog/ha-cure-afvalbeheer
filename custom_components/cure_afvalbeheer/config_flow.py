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
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
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

    _pending_municipality: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""

        return await self._async_step_municipality(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle changing the municipality of an existing entry."""

        return await self._async_step_municipality(user_input)

    async def _async_step_municipality(
        self, user_input: dict[str, Any] | None
    ) -> config_entries.ConfigFlowResult:
        """Show/handle the municipality step, shared by user and reconfigure."""

        is_reconfigure = self.source == config_entries.SOURCE_RECONFIGURE

        if user_input is not None:
            municipality = user_input[CONF_MUNICIPALITY]

            if is_reconfigure:
                reconfigure_entry = self._get_reconfigure_entry()

                if municipality == reconfigure_entry.data[CONF_MUNICIPALITY]:
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        title=MUNICIPALITIES[municipality],
                        data={CONF_MUNICIPALITY: municipality},
                    )

                await self.async_set_unique_id(municipality)
                self._abort_if_unique_id_configured()

                self._pending_municipality = municipality

                return await self.async_step_reconfigure_confirm()

            await self.async_set_unique_id(municipality)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=MUNICIPALITIES[municipality],
                data={CONF_MUNICIPALITY: municipality},
            )

        current_municipality = (
            self._get_reconfigure_entry().data[CONF_MUNICIPALITY]
            if is_reconfigure
            else None
        )

        return self.async_show_form(
            step_id="reconfigure" if is_reconfigure else "user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MUNICIPALITY, default=current_municipality
                    ): _MUNICIPALITY_SELECTOR,
                }
            ),
        )

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for confirmation before switching to a different municipality.

        Changing the municipality replaces every sensor and its history
        for this entry, so this is deliberately not applied silently.
        """

        reconfigure_entry = self._get_reconfigure_entry()
        municipality = self._pending_municipality
        assert municipality is not None

        if user_input is not None:
            return self.async_update_reload_and_abort(
                reconfigure_entry,
                unique_id=municipality,
                title=MUNICIPALITIES[municipality],
                data={CONF_MUNICIPALITY: municipality},
            )

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "current": MUNICIPALITIES[reconfigure_entry.data[CONF_MUNICIPALITY]],
                "new": MUNICIPALITIES[municipality],
            },
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
            # NumberSelector always yields a float, regardless of step/mode;
            # coerce back to int here so a stray "10.0" never leaks into
            # storage and breaks anything that expects a plain int (e.g.
            # range() when resolving the forecast window).
            return self.async_create_entry(
                data={
                    CONF_LOOKAHEAD_DAYS: int(user_input[CONF_LOOKAHEAD_DAYS]),
                    CONF_UPDATE_INTERVAL_MINUTES: int(
                        user_input[CONF_UPDATE_INTERVAL_MINUTES]
                    ),
                }
            )

        current_lookahead_days = int(
            self.config_entry.options.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS)
        )
        current_update_interval = int(
            self.config_entry.options.get(
                CONF_UPDATE_INTERVAL_MINUTES, DEFAULT_UPDATE_INTERVAL_MINUTES
            )
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
                    vol.Required(
                        CONF_UPDATE_INTERVAL_MINUTES, default=current_update_interval
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=5,
                            max=1440,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    ),
                }
            ),
        )

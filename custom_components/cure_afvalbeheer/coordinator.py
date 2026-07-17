"""DataUpdateCoordinator for Cure Afvalbeheer."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CureApiClient
from .const import DEFAULT_SCAN_INTERVAL, NAME
from .exceptions import CureApiError
from .logger import LOGGER
from .models import CureData


class CureDataUpdateCoordinator(DataUpdateCoordinator[CureData]):
    """Coordinator for Cure Afvalbeheer."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CureApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialise the coordinator."""

        super().__init__(
            hass,
            logger=LOGGER,
            name=NAME,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

        self.api = api

    async def _async_update_data(self) -> CureData:
        """Fetch the latest data from the Cure website."""

        try:
            return await self.api.fetch_milieustraat()
        except CureApiError as err:
            raise UpdateFailed(str(err)) from err

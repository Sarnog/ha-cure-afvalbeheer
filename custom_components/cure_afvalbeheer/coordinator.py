"""DataUpdateCoordinator for Cure Afvalbeheer."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import CureApiClient


class CureDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for Cure Afvalbeheer."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CureApiClient,
    ) -> None:
        """Initialise the coordinator."""

        super().__init__(
            hass,
            logger=None,
            name="Cure Afvalbeheer",
        )

        self.api = api

"""DataUpdateCoordinator for Cure Afvalbeheer."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CureApiClient
from .const import DOMAIN, ISSUE_NO_LOCATIONS_FOUND, NAME
from .exceptions import CureApiError
from .logger import LOGGER
from .models import CureData
from .parser import location_hint_for


class CureDataUpdateCoordinator(DataUpdateCoordinator[CureData]):
    """Coordinator for Cure Afvalbeheer."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CureApiClient,
        config_entry: ConfigEntry,
        municipality: str,
        update_interval_minutes: int,
    ) -> None:
        """Initialise the coordinator."""

        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{NAME} {municipality}",
            config_entry=config_entry,
            update_interval=timedelta(minutes=update_interval_minutes),
        )

        self.api = api
        self.municipality = municipality

    @property
    def _no_locations_issue_id(self) -> str:
        """Return the repair issue id for this config entry."""

        return f"{ISSUE_NO_LOCATIONS_FOUND}_{self.config_entry.entry_id}"

    async def _async_update_data(self) -> CureData:
        """Fetch the latest data from the Cure website."""

        try:
            data = await self.api.fetch_milieustraat(self.municipality)
        except CureApiError as err:
            raise UpdateFailed(str(err)) from err

        if data.locations:
            ir.async_delete_issue(self.hass, DOMAIN, self._no_locations_issue_id)
            return data

        LOGGER.error(
            "No milieustraten found for %s; the Cure page layout may have changed",
            self.municipality,
        )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._no_locations_issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_NO_LOCATIONS_FOUND,
            translation_placeholders={"municipality": self.municipality},
        )

        if self.data is not None and self.data.locations:
            LOGGER.warning(
                "Keeping last known good locations for %s while the parser "
                "issue persists; still using freshly parsed notices",
                self.municipality,
            )

            # Notices are parsed against this cycle's (empty) locations, so
            # any location-specific hint was lost. Re-resolve it against the
            # locations we are falling back to, otherwise a notice meant for
            # one location would apply to all of them (a missing hint means
            # "applies everywhere", see schedule.py::_notice_applies).
            for notice in data.notices:
                if notice.location_hint is None:
                    notice.location_hint = location_hint_for(
                        notice.title, self.data.locations
                    )

            return CureData(locations=self.data.locations, notices=data.notices)

        return data

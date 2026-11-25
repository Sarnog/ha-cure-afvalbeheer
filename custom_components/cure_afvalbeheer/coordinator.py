"""DataUpdateCoordinator for Cure Afvalbeheer."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import CureApiClient
from .const import (
    DOMAIN,
    ISSUE_NO_LOCATIONS_FOUND,
    ISSUE_NO_OPENING_HOURS_FOUND,
    ISSUE_UNREADABLE_OPENING_HOURS,
    NAME,
)
from .exceptions import CureApiError
from .logger import LOGGER
from .models import CureData, Location
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

    def _issue_id(self, issue: str) -> str:
        """Return the repair issue id for this config entry."""

        return f"{issue}_{self.config_entry.entry_id}"

    def _raise_issue(
        self,
        issue: str,
        severity: ir.IssueSeverity = ir.IssueSeverity.ERROR,
        **placeholders: str,
    ) -> None:
        """Show a repair notification for this config entry."""

        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id(issue),
            is_fixable=False,
            severity=severity,
            translation_key=issue,
            translation_placeholders={"municipality": self.municipality} | placeholders,
        )

    def _clear_issue(self, issue: str) -> None:
        """Remove a repair notification for this config entry."""

        ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(issue))

    def _known_good_hours(self) -> list[Location]:
        """Return the last locations that still had opening hours."""

        if self.data is None:
            return []

        return [location for location in self.data.locations if location.hours]

    async def _async_update_data(self) -> CureData:
        """Fetch the latest data from the Cure website."""

        try:
            data = await self.api.fetch_milieustraat(
                self.municipality, dt_util.now().date()
            )
        except CureApiError as err:
            raise UpdateFailed(str(err)) from err

        self._report_unreadable_hours(data)

        return self._with_known_good_data(data)

    def _report_unreadable_hours(self, data: CureData) -> None:
        """Show a repair notification while part of the hours is unreadable.

        The parser reads what it can and lists what it could not: a line
        that looks like opening hours, a start date it cannot place, or
        hours the page itself says have expired. Any of those means the
        sensors may not match the website, which the user must be told
        rather than left to find out at a closed gate.
        """

        if not data.hours_warnings:
            self._clear_issue(ISSUE_UNREADABLE_OPENING_HOURS)
            return

        self._raise_issue(
            ISSUE_UNREADABLE_OPENING_HOURS,
            ir.IssueSeverity.WARNING,
            details="\n".join(f"- {warning}" for warning in data.hours_warnings),
        )

    def _with_known_good_data(self, data: CureData) -> CureData:
        """Fall back to the last good data for anything this fetch lost.

        Both fallbacks work the same way: a part of the page that parsed
        before and yields nothing now points at a layout change rather
        than at news, and last week's answer beats an answer that is
        plainly wrong. The repair notification stays up either way, so the
        stale data is never silently passed off as current.
        """

        if not data.locations:
            return self._without_locations(data)

        self._clear_issue(ISSUE_NO_LOCATIONS_FOUND)

        return self._with_opening_hours(data)

    def _without_locations(self, data: CureData) -> CureData:
        """Handle a fetch that found no recycling centres at all."""

        LOGGER.error(
            "No milieustraten found for %s; the Cure page layout may have changed",
            self.municipality,
        )

        self._raise_issue(ISSUE_NO_LOCATIONS_FOUND)

        if self.data is None or not self.data.locations:
            return data

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

        return CureData(
            locations=self.data.locations,
            notices=data.notices,
            hours_warnings=data.hours_warnings,
        )

    def _with_opening_hours(self, data: CureData) -> CureData:
        """Handle a fetch whose locations came back without opening hours.

        Empty hours would otherwise read as "closed all week" - the same
        thing a genuinely closed location looks like - which is the one
        wrong answer a visitor cannot tell apart from a right one.
        """

        if all(location.hours for location in data.locations):
            self._clear_issue(ISSUE_NO_OPENING_HOURS_FOUND)

            return data

        LOGGER.error(
            "No opening hours found for %s; the Cure page layout may have changed",
            self.municipality,
        )

        self._raise_issue(ISSUE_NO_OPENING_HOURS_FOUND)

        known_good = {location.name: location for location in self._known_good_hours()}

        if not known_good:
            return data

        LOGGER.warning(
            "Keeping the last known good opening hours for %s while the "
            "parser issue persists",
            self.municipality,
        )

        locations: list[Location] = []

        for location in data.locations:
            previous = known_good.get(location.name)

            if location.hours or previous is None:
                locations.append(location)
                continue

            locations.append(
                Location(
                    name=location.name,
                    address=location.address,
                    hours=previous.hours,
                    scheduled=previous.scheduled,
                )
            )

        return CureData(
            locations=locations,
            notices=data.notices,
            hours_warnings=data.hours_warnings,
        )

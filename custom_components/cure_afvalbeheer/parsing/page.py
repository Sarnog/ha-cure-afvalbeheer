"""One Cure milieustraat page, read as a whole.

CureParser is the single entry point for the rest of the integration. It
owns the parsed HTML and hands it to the reader of each part of the page:
locations, regular_hours and notices. The text-level readers below those
(dates, times, hours_lines, closing_days, heat_protocol, attention) never
see HTML at all.
"""

from __future__ import annotations

from datetime import date

from bs4 import BeautifulSoup

from ..logger import LOGGER
from ..models import CureData, Location, Notice, OpeningHours
from .locations import location_warnings, read_addresses
from .notices import heat_protocol_notice, read_notices
from .regular_hours import RegularHours, read_regular_hours


class CureParser:
    """Parser for one Cure milieustraat page."""

    def __init__(self, html: str) -> None:
        """Parse the HTML once; every reader works on the same tree."""

        LOGGER.debug("Initialising Cure HTML parser")

        self._soup = BeautifulSoup(html, "html.parser")

    # --- Page in general -------------------------------------------------

    # --- Regular opening hours -------------------------------------------

    def _regular_hours(self, today: date | None) -> RegularHours:
        """Read the opening hours section against today (or the system date)."""

        return read_regular_hours(self._soup, today or date.today())

    def opening_hours(self, today: date | None = None) -> list[OpeningHours]:
        """Return the regular opening hours that apply today."""

        return self._regular_hours(today).current

    def hours_warnings(self, today: date | None = None) -> list[str]:
        """Return what in the opening hours section could not be read."""

        return self._regular_hours(today).warnings

    # --- Locations -------------------------------------------------------

    def location_addresses(self) -> list[tuple[str, str | None]]:
        """Return (name, address) for every recycling centre on the page."""

        return read_addresses(self._soup)[0]

    def location_warnings(self) -> list[str]:
        """Return what suggests the locations found are not all there is."""

        return location_warnings(self._soup)

    def parse_locations(self, today: date | None = None) -> list[Location]:
        """Parse all recycling centres."""

        return self._locations(self._regular_hours(today))

    def _locations(self, regular: RegularHours) -> list[Location]:
        """Combine every address with the regular hours of the page."""

        # One set of hours per page: Cure lists them once for every
        # recycling centre of the municipality.
        return [
            Location(
                name=name,
                address=address,
                hours=regular.current,
                scheduled=regular.scheduled,
            )
            for name, address in self.location_addresses()
        ]

    # --- Temporary deviations --------------------------------------------

    def heat_protocol_notice(self, today: date) -> Notice | None:
        """Parse the site-wide heat protocol announcement, if present."""

        return heat_protocol_notice(self._soup, today)

    def notices(
        self,
        locations: list[Location],
        today: date | None = None,
    ) -> list[Notice]:
        """Parse temporary deviations (heat protocol, closures, closing days)."""

        return read_notices(self._soup, locations, today or date.today())[0]

    # --- Everything at once ----------------------------------------------

    def parse(self, today: date | None = None) -> CureData:
        """Parse the complete page.

        Each section is read once: the hours warnings are logged where
        they are found, the other warnings here.
        """

        if today is None:
            today = date.today()

        regular = self._regular_hours(today)
        locations = self._locations(regular)

        notices, notice_warnings = read_notices(self._soup, locations, today)
        found_location_warnings = self.location_warnings()

        for warning in [*found_location_warnings, *notice_warnings]:
            LOGGER.warning("Page content: %s", warning)

        return CureData(
            locations=locations,
            notices=notices,
            warnings=[*found_location_warnings, *regular.warnings, *notice_warnings],
        )

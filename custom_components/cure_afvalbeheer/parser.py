"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

from bs4 import BeautifulSoup

from . import selectors
from .logger import LOGGER
from .models import (
    CureData,
    Location,
    OpeningHours,
)
from .parsers import (
    is_opening_hours_line,
    parse_opening_hours,
)


class CureParser:
    """Parser voor Cure HTML-pagina's."""

    def __init__(self, html: str) -> None:
        """Initialiseer de parser."""

        LOGGER.debug("Initialising Cure HTML parser")

        self._soup = BeautifulSoup(html, "html.parser")

    def page_title(self) -> str:
        """Return the page title."""

        title = selectors.page_title(self._soup)

        LOGGER.debug("Page title: %s", title)

        return title

    def headings(self) -> list[str]:
        """Return all headings."""

        return selectors.all_headings(self._soup)

    def location_name(self) -> str:
        """Return the location name."""

        return selectors.location_name(self._soup)

    def opening_hours_lines(self) -> list[str]:
        """Return only valid opening hours lines."""

        section = selectors.section_with_heading(
            self._soup,
            "Openingstijden",
        )

        if section is None:
            return []

        return [
            line
            for line in selectors.paragraphs(section)
            if is_opening_hours_line(line)
        ]

    def opening_hours(self) -> list[OpeningHours]:
        """Return parsed opening hours."""

        return parse_opening_hours(self.opening_hours_lines())

    def location_addresses(self) -> list[tuple[str, str]]:
        """Parse the recycling centre addresses."""

        section = selectors.address_section(self._soup)

        if section is None:
            return []

        result: list[tuple[str, str]] = []

        current_name: str | None = None

        for element in section.find_all(["h3", "p"]):
            if element.name == "h3":
                current_name = element.get_text(strip=True)

            elif element.name == "p" and current_name:
                address = " ".join(element.stripped_strings)

                result.append(
                    (
                        current_name,
                        address,
                    )
                )

                current_name = None

        return result

    def parse_locations(self) -> list[Location]:
        """Parse all recycling centres."""

        locations: list[Location] = []

        hours = self.opening_hours()

        for name, address in self.location_addresses():
            locations.append(
                Location(
                    name=name,
                    address=address,
                    hours=hours,
                )
            )

        return locations

    def parse(self) -> CureData:
        """Parse the complete page."""

        return CureData(
            locations=self.parse_locations(),
        )

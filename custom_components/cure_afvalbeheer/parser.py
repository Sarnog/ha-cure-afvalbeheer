"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

from datetime import date

from bs4 import BeautifulSoup

from . import selectors
from .logger import LOGGER
from .models import (
    CureData,
    Location,
    Notice,
    OpeningHours,
)
from .notices import parse_closure_notice, parse_heat_protocol_notice
from .parsers import (
    is_opening_hours_line,
    parse_opening_hours,
)


def location_hint_for(heading: str, locations: list[Location]) -> str | None:
    """Return the single location name mentioned in heading, if any.

    Only the heading is checked, not the full notice body: a renovation
    notice for one location often mentions another as the alternative to
    visit instead, which would otherwise be picked up as a false match.
    """

    heading_lower = heading.lower()

    matches = [
        location.name
        for location in locations
        if location.name.removeprefix("Milieustraat ").strip().lower() in heading_lower
    ]

    if len(matches) == 1:
        return matches[0]

    return None


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
        """Parse the recycling centre addresses.

        Municipalities with a single recycling centre sometimes omit the
        repeated h3 location name in the address section entirely (e.g.
        Geldrop-Mierlo has just a heading and one address paragraph, no
        h3). Fall back to the page's own h1 title as the location name
        in that case, since it is otherwise dropped silently.
        """

        section = selectors.address_section(self._soup)

        if section is None:
            return []

        result: list[tuple[str, str]] = []

        current_name: str | None = None

        for element in section.find_all(["h3", "p"]):
            if element.name == "h3":
                current_name = element.get_text(strip=True)

            elif element.name == "p":
                address = " ".join(element.stripped_strings)

                if not address:
                    continue

                result.append(
                    (
                        current_name or self.location_name(),
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

    def notices(
        self,
        locations: list[Location],
        today: date | None = None,
    ) -> list[Notice]:
        """Parse temporary deviations (heat protocol, closures)."""

        if today is None:
            today = date.today()

        result: list[Notice] = []

        heading = selectors.news_heading(self._soup)

        if heading:
            heat_protocol = parse_heat_protocol_notice(heading, today)

            if heat_protocol is not None:
                result.append(heat_protocol)

        closure_section = selectors.closure_notice_section(self._soup)

        if closure_section is not None:
            closure_heading = closure_section.find("h2")

            if closure_heading is not None:
                closure_heading_text = closure_heading.get_text(strip=True)
                body_text = closure_section.get_text(" ", strip=True)

                closure = parse_closure_notice(closure_heading_text, body_text, today)

                if closure is not None:
                    closure.location_hint = location_hint_for(
                        closure_heading_text, locations
                    )
                    result.append(closure)

        return result

    def parse(self) -> CureData:
        """Parse the complete page."""

        locations = self.parse_locations()

        return CureData(
            locations=locations,
            notices=self.notices(locations),
        )

"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

import re
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
from .notices import (
    parse_closing_days,
    parse_closure_notice,
    parse_heat_protocol_notice,
    season_covers,
)
from .parsers import (
    is_opening_hours_line,
    parse_opening_hours,
)


def _mentions_location(heading_lower: str, location: Location) -> bool:
    """Return whether a lower-cased heading names this location."""

    name = location.name.removeprefix("Milieustraat ").strip().lower()

    if not name:
        return False

    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", heading_lower) is not None


def location_hint_for(heading: str, locations: list[Location]) -> str | None:
    """Return the single location name mentioned in heading, if any.

    Only the heading is checked, not the full notice body: a renovation
    notice for one location often mentions another as the alternative to
    visit instead, which would otherwise be picked up as a false match.

    Matching is on whole words. Short location names are ordinary Dutch
    words too - "Acht" sits inside "achter" and "gedacht" - so a plain
    substring test would scope a municipality-wide notice to a single
    location purely on the wording of its heading.
    """

    heading_lower = heading.lower()

    matches = [
        location.name
        for location in locations
        if _mentions_location(heading_lower, location)
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

    def _hours_block(self, today: date) -> list[str]:
        """Return the lines of the opening hours block that applies today.

        A page carrying one block is the ordinary case. Should Cure ever
        split its hours into a summer and a winter set, the heading naming
        the months that cover today decides; picking one by document order
        would mean showing winter hours in August. When several blocks
        apply, or none names a season at all, the first is used and the
        log says so - a wrong guess about which set is current is worth
        knowing about.
        """

        blocks = selectors.blocks_under_heading(self._soup, "Openingstijden")

        if len(blocks) <= 1:
            return blocks[0][1] if blocks else []

        current = [lines for heading, lines in blocks if season_covers(heading, today)]

        if len(current) == 1:
            return current[0]

        LOGGER.warning(
            "Found %d opening hours blocks and could not tell which one "
            "applies today; using the first: %s",
            len(blocks),
            [heading for heading, _ in blocks],
        )

        return blocks[0][1]

    def opening_hours_lines(self, today: date | None = None) -> list[str]:
        """Return only valid opening hours lines.

        Only the lines under the "Openingstijden" heading itself are
        considered: the closing days share one container with them, and a
        dated line from that list ("Zaterdag 26 december: 10:00 tot 14:00")
        would otherwise be filed as that weekday's regular hours.
        """

        if today is None:
            today = date.today()

        return [
            line for line in self._hours_block(today) if is_opening_hours_line(line)
        ]

    def opening_hours(self, today: date | None = None) -> list[OpeningHours]:
        """Return parsed opening hours."""

        return parse_opening_hours(self.opening_hours_lines(today))

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

    def parse_locations(self, today: date | None = None) -> list[Location]:
        """Parse all recycling centres."""

        locations: list[Location] = []

        hours = self.opening_hours(today)

        for name, address in self.location_addresses():
            locations.append(
                Location(
                    name=name,
                    address=address,
                    hours=hours,
                )
            )

        return locations

    def heat_protocol_notice(self, today: date) -> Notice | None:
        """Parse the site-wide heat protocol announcement, if present.

        Both the news block's heading and the news items below it are
        tried, in that order. The heading is the announcement Cure puts in
        front of every visitor, but it is free-form editorial text, while
        the item it links to words the same period more consistently - so
        one reads what the other happens to leave unreadable.

        Only the heading counts as current. The items below it are the
        news archive: they stay on the page for months, so an item saying
        "vandaag" is not saying anything about today.
        """

        heading = selectors.news_heading(self._soup)

        candidates: list[tuple[str, bool]] = [(heading, True)] if heading else []

        candidates += [(text, False) for text in selectors.news_item_texts(self._soup)]

        for text, current in candidates:
            notice = parse_heat_protocol_notice(text, today, current=current)

            if notice is not None:
                return notice

        return None

    def notices(
        self,
        locations: list[Location],
        today: date | None = None,
    ) -> list[Notice]:
        """Parse temporary deviations (heat protocol, closures, closing days)."""

        if today is None:
            today = date.today()

        result: list[Notice] = []

        heat_protocol = self.heat_protocol_notice(today)

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

        # No location hint: the closing days are listed once per
        # municipality page and apply to every recycling centre on it.
        for heading, lines in selectors.closing_days_blocks(self._soup):
            result.extend(parse_closing_days(heading, lines, today))

        return result

    def parse(self, today: date | None = None) -> CureData:
        """Parse the complete page."""

        locations = self.parse_locations(today)

        return CureData(
            locations=locations,
            notices=self.notices(locations, today),
        )

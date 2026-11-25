"""The recycling centres on a page: their names and addresses."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import Location
from . import selectors


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


def read_addresses(
    soup: BeautifulSoup,
) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Return the addresses, and what in the address section did not fit.

    Municipalities with a single recycling centre sometimes omit the
    repeated h3 location name in the address section entirely (e.g.
    Geldrop-Mierlo has just a heading and one address paragraph, no
    h3). The page's own h1 title then serves as the location name,
    since it is otherwise dropped silently.

    A location name directly followed by the next one has no address
    of its own. It used to be dropped without a word; now it is kept
    (without an address) and reported, since a location missing from
    the sensors is just as wrong as wrong opening hours.
    """

    section = selectors.address_section(soup)

    if section is None:
        return [], []

    result: list[tuple[str, str | None]] = []
    warnings: list[str] = []

    current_name: str | None = None

    for element in section.find_all(["h3", "p"]):
        if element.name == "h3":
            if current_name is not None:
                result.append((current_name, None))
                warnings.append(f"Geen adres gevonden voor {current_name}")

            current_name = element.get_text(strip=True)

        elif element.name == "p":
            address = " ".join(element.stripped_strings)

            if not address:
                continue

            result.append(
                (
                    current_name or selectors.location_name(soup),
                    address,
                )
            )

            current_name = None

    if current_name is not None:
        result.append((current_name, None))
        warnings.append(f"Geen adres gevonden voor {current_name}")

    return result, warnings


def location_warnings(soup: BeautifulSoup) -> list[str]:
    """Return what suggests the locations found are not all there is.

    Besides the address section itself, the page names its locations
    elsewhere too, on the site maps ("Plattegrond Milieustraat Acht").
    A location named there but not among the addresses points at a
    layout the address section no longer matches.
    """

    addresses, warnings = read_addresses(soup)

    known = {name.strip().lower() for name, _ in addresses}

    for name in selectors.site_map_location_names(soup):
        if name.lower() not in known:
            warnings.append(f"{name} staat op de pagina, maar niet bij de adressen")

    return warnings

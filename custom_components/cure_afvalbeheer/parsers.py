"""Text parsers for Cure Afvalbeheer."""

from __future__ import annotations

import re

from .exceptions import ParserError
from .logger import LOGGER
from .models import OpeningHours
from .weekday import Weekday

_TIME_RANGE = re.compile(r"(?P<open>\d{2}:\d{2})\s+tot\s+(?P<close>\d{2}:\d{2})")

_DAY_MAPPING = {
    "Maandag": Weekday.MONDAY,
    "Dinsdag": Weekday.TUESDAY,
    "Woensdag": Weekday.WEDNESDAY,
    "Donderdag": Weekday.THURSDAY,
    "Vrijdag": Weekday.FRIDAY,
    "Zaterdag": Weekday.SATURDAY,
    "Zondag": Weekday.SUNDAY,
    "Zon- en feestdagen": Weekday.HOLIDAY,
    "Zon & Feestdagen": Weekday.HOLIDAY,
}


def parse_opening_hours_line(line: str) -> OpeningHours:
    """Parse one opening hours line."""

    LOGGER.debug("Parsing line: %s", line)

    day_name, value = line.split(":", 1)

    day_name = day_name.strip()
    value = value.strip()

    try:
        day = _DAY_MAPPING[day_name]
    except KeyError as err:
        raise ParserError(f"Unknown weekday: {day_name}") from err

    if value.lower() == "gesloten":
        return OpeningHours(
            day=day,
            opens=None,
            closes=None,
            closed=True,
        )

    match = _TIME_RANGE.search(value)

    if not match:
        raise ParserError(f"Cannot parse opening hours line: {line}")

    return OpeningHours(
        day=day,
        opens=match.group("open"),
        closes=match.group("close"),
        closed=False,
    )


def parse_opening_hours(
    lines: list[str],
) -> list[OpeningHours]:
    """Parse multiple opening hours lines."""

    LOGGER.debug(
        "Parsing %d opening hours lines",
        len(lines),
    )

    return [parse_opening_hours_line(line) for line in lines]


def is_opening_hours_line(line: str) -> bool:
    """Return True if the line contains opening hours."""

    if ":" not in line:
        return False

    day, value = line.split(":", 1)

    day = day.strip()

    if day not in _DAY_MAPPING:
        return False

    value = value.strip()

    if value.lower() == "gesloten":
        return True

    return bool(_TIME_RANGE.search(value))

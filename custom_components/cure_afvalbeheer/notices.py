"""Free-text parsing of temporary deviations for Cure Afvalbeheer.

Cure's editors announce temporary deviations (heat protocol, renovations,
closures) as free-text Dutch sentences rather than structured data. The
functions here try to extract a usable Notice from that text and return
None whenever the expected pattern is not found, so an unrecognised or
reworded announcement is silently ignored instead of producing a wrong
result.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from .logger import LOGGER
from .models import Notice

_MONTHS = {
    "januari": 1,
    "februari": 2,
    "maart": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "augustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}

_WEEKDAYS = (
    "maandag",
    "dinsdag",
    "woensdag",
    "donderdag",
    "vrijdag",
    "zaterdag",
    "zondag",
)

_MONTH_PATTERN = "|".join(_MONTHS)
_WEEKDAY_PATTERN = "|".join(_WEEKDAYS)

_TIME_RANGE = re.compile(
    r"(?P<open>\d{2}:\d{2})\s*(?:tot|-|t/m)\s*(?P<close>\d{2}:\d{2})",
    re.IGNORECASE,
)

_EXPLICIT_CLOSURE_DATE = re.compile(
    r"datum sluiting:?\s*(?P<day>\d{2})-(?P<month>\d{2})-(?P<year>\d{4})",
    re.IGNORECASE,
)

_RELATIVE_END_DATE = re.compile(
    rf"tot en met\s+(?:(?:{_WEEKDAY_PATTERN})\s+)?"
    rf"(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH_PATTERN})",
    re.IGNORECASE,
)

_DATED_LIST_ENTRY = re.compile(
    rf"(?:{_WEEKDAY_PATTERN})\s+(?P<day>\d{{1,2}})\s+(?P<month>{_MONTH_PATTERN})\s+(?P<year>\d{{4}})",
    re.IGNORECASE,
)


def parse_time_range(text: str) -> tuple[str, str] | None:
    """Extract an HH:MM-HH:MM time range from free text."""

    match = _TIME_RANGE.search(text)

    if match is None:
        return None

    return match.group("open"), match.group("close")


def parse_relative_end_date(text: str, today: date) -> date | None:
    """Extract a "tot en met <dag> <maand>" end date, inferring the year.

    The year is never written for a "tot en met" end date since it always
    describes a currently active notice. If the resulting date would be
    more than 30 days in the past, assume it rolled over into the next
    year (e.g. a notice made in late December about early January).
    """

    match = _RELATIVE_END_DATE.search(text)

    if match is None:
        return None

    day = int(match.group("day"))
    month = _MONTHS[match.group("month").lower()]

    try:
        result = date(today.year, month, day)
    except ValueError:
        return None

    if (today - result) > timedelta(days=30):
        try:
            result = date(today.year + 1, month, day)
        except ValueError:
            return None

    return result


def parse_explicit_closure_date(text: str) -> date | None:
    """Extract a "Datum sluiting: DD-MM-JJJJ" date."""

    match = _EXPLICIT_CLOSURE_DATE.search(text)

    if match is None:
        return None

    try:
        return date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError:
        return None


def parse_dated_list(text: str) -> list[date]:
    """Extract a list of "<weekday> <dag> <maand> <jaar>" entries."""

    result: list[date] = []

    for match in _DATED_LIST_ENTRY.finditer(text):
        month = _MONTHS[match.group("month").lower()]

        try:
            result.append(
                date(int(match.group("year")), month, int(match.group("day")))
            )
        except ValueError:
            continue

    return result


def parse_heat_protocol_notice(heading: str, today: date) -> Notice | None:
    """Parse the site-wide heat protocol banner, if present."""

    if "hitteprotocol" not in heading.lower():
        return None

    time_range = parse_time_range(heading)
    ends = parse_relative_end_date(heading, today)

    if time_range is None or ends is None:
        LOGGER.debug(
            "Found a hitteprotocol heading but could not parse it: %s", heading
        )
        return None

    opens, closes = time_range

    return Notice(
        reason="hitteprotocol",
        title=heading,
        closed=False,
        opens=opens,
        closes=closes,
        ends=ends,
    )


def parse_closure_notice(heading: str, body_text: str, today: date) -> Notice | None:
    """Parse a municipality-specific closure/renovation notice, if present."""

    if not heading.lower().startswith("let op!"):
        return None

    combined_text = (heading + body_text).lower()
    reason = "verbouwing" if "verbouw" in combined_text else "werkzaamheden"

    explicit_date = parse_explicit_closure_date(body_text)

    if explicit_date is not None:
        return Notice(
            reason=reason,
            title=heading,
            closed=True,
            starts=explicit_date if explicit_date > today else None,
        )

    dated_list = parse_dated_list(body_text)

    if dated_list:
        return Notice(
            reason=reason,
            title=heading,
            closed=True,
            dates=dated_list,
        )

    LOGGER.debug(
        "Found a 'Let op!' notice but could not parse a date from it: %s", heading
    )

    return None

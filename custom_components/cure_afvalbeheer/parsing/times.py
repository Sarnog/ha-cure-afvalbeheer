"""Clock times as Cure writes them, shared by every text parser.

Cure writes clock times as "08:30" on the opening hours lines and as
"08.30" or "8:30" elsewhere, so every parser needs the same two things:
turn a written hour and minute into one "HH:MM" string, and reject numbers
that are not a time at all.
"""

from __future__ import annotations

import re

# The separator between hour and minute, and the one between the two times
# of a range. Both are kept here so the parsers cannot drift apart on which
# spellings they accept.
CLOCK_SEPARATOR = r"[:.]"

RANGE_SEPARATOR = r"(?:tot en met|tot|t/m|[-–—])"


def hhmm(hour: str | int, minute: str | int | None) -> str | None:
    """Return an "HH:MM" time, or None if the numbers are not a time."""

    hours = int(hour)
    minutes = int(minute) if minute is not None else 0

    if hours > 23 or minutes > 59:
        return None

    return f"{hours:02d}:{minutes:02d}"


# A written range of two clock times ("08:30 tot 17:00", "8.30-17.00").
TIME_RANGE = re.compile(
    rf"(?<!\d)(?P<open_hour>\d{{1,2}}){CLOCK_SEPARATOR}(?P<open_minute>\d{{2}})"
    rf"\s*{RANGE_SEPARATOR}\s*"
    rf"(?P<close_hour>\d{{1,2}}){CLOCK_SEPARATOR}(?P<close_minute>\d{{2}})(?!\d)",
    re.IGNORECASE,
)

# A full range ("geopend van 10:00 tot 16:00 uur"). Both numbers have to
# sit right against the separator, which is what keeps a date out of it:
# "geopend van 6 april tot 8 mei" has a month name in the way.
_ADJUSTED_RANGE = re.compile(
    r"\b(?:geopend|open)\s+(?:van|vanaf)\s+"
    r"(?P<open_hour>\d{1,2})(?:[:.](?P<open_minute>\d{2}))?(?!\d)"
    r"\s*(?:uur\s+)?(?:tot(?:\s+en\s+met)?|t/m|[-–—])\s*"
    r"(?P<close_hour>\d{1,2})(?:[:.](?P<close_minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

_OPEN_UNTIL = re.compile(
    r"\b(?:geopend|open)\s+tot\s+(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

# "sluiten ... om 15:00". Cure puts anything between the two - who is
# closing, on what date - so a good few words are allowed to sit there,
# but none of them may be a word for opening: in "sluiten niet, wij openen
# om 09:00" that time is an opening time. Only whole words count, so a
# sentence boundary ends the search either way.
_CLOSES_AT = re.compile(
    r"\bsluit(?:en)?(?:\s+(?!open\w*\b|geopend\b)\w+){0,8}?\s+om\s+"
    r"(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

_OPENS_AT = re.compile(
    r"\b(?:(?:geopend|open)\s+(?:vanaf|om)|vanaf|pas\s+om)\s+"
    r"(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

_TRAILING_HOUR_UNIT = re.compile(r"^\s*uur\b", re.IGNORECASE)


def parse_time_range(text: str) -> tuple[str, str] | None:
    """Extract an HH:MM-HH:MM time range from free text."""

    match = TIME_RANGE.search(text)

    if match is None:
        return None

    opens = hhmm(match.group("open_hour"), match.group("open_minute"))
    closes = hhmm(match.group("close_hour"), match.group("close_minute"))

    if opens is None or closes is None:
        return None

    return opens, closes


def _lone_time(match: re.Match[str], text: str) -> str | None:
    """Return the time a single-time match found, if it is one at all.

    A whole hour only counts as a time when "uur" follows it: "vanaf 10
    uur" is a time, "vanaf 6 april" is a date. A time written with minutes
    needs no such confirmation.
    """

    minute = match.group("minute")

    if minute is None and not _TRAILING_HOUR_UNIT.match(text[match.end() :]):
        return None

    return hhmm(match.group("hour"), minute)


def parse_adjusted_hours(text: str) -> tuple[str | None, str | None]:
    """Extract an announced opening and closing time from free text.

    Returns them as (opens, closes), either of which is None when the text
    does not announce that side - Cure usually names only the closing time
    ("geopend tot 16:00 uur"), leaving the regular opening time in force.
    A full range ("geopend van 10:00 tot 16:00 uur") and a lone opening
    time ("pas vanaf 10:00 uur open") are recognised just as well, as is
    the older closing wording ("sluiten de milieustraten om 16 uur").
    """

    range_match = _ADJUSTED_RANGE.search(text)

    if range_match is not None:
        opens = hhmm(range_match.group("open_hour"), range_match.group("open_minute"))
        closes = hhmm(
            range_match.group("close_hour"), range_match.group("close_minute")
        )

        if opens is not None and closes is not None:
            return opens, closes

    closes = None

    for pattern in (_OPEN_UNTIL, _CLOSES_AT):
        match = pattern.search(text)

        if match is not None:
            closes = _lone_time(match, text)

        if closes is not None:
            break

    match = _OPENS_AT.search(text)

    opens = _lone_time(match, text) if match is not None else None

    return opens, closes

"""Free-text parsing of temporary deviations for Cure Afvalbeheer.

Cure's editors announce temporary deviations (heat protocol, renovations,
closures, the closing days around public holidays) as free-text Dutch
sentences rather than structured data, and reword them freely from year to
year. The functions here try to extract a usable Notice from that text and
return None (or no notices at all) whenever the expected pattern is not
found, so an unrecognised or reworded announcement is silently ignored
instead of producing a wrong result.
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

# One or more day numbers sharing a single month, as Cure writes them in
# the closing days list: "6", "25 en 26", "23 t/m 27". A weekday may be
# repeated before every number ("25 en zaterdag 26 december").
_DAY_SEPARATOR = r"(?:,|&|\ben\b|t/m|tot en met|[-–—])"

_DAY_LIST = (
    rf"\d{{1,2}}"
    rf"(?:\s*{_DAY_SEPARATOR}\s*(?:(?:{_WEEKDAY_PATTERN})\s+)?\d{{1,2}})*"
)

_CLOSING_DAY_DATE = re.compile(
    rf"(?:\b(?:{_WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<days>{_DAY_LIST})\s+"
    rf"(?P<month>{_MONTH_PATTERN})\b"
    rf"(?:\s+(?P<year>\d{{4}})(?!\d))?",
    re.IGNORECASE,
)

_DAY_NUMBER = re.compile(r"\d{1,2}")

# Only these mean "everything in between is included too"; "en" and a
# comma list separate days instead of spanning them.
_RANGE_SEPARATOR = re.compile(r"t/m|tot en met|[-–—]", re.IGNORECASE)

_YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")

_OPEN_UNTIL = re.compile(
    r"\b(?:geopend|open)\s+tot\s+(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?",
    re.IGNORECASE,
)

_CLOSES_AT = re.compile(
    r"\bsluit(?:en)?(?:\s+\w+){0,4}?\s+om\s+(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?",
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


def parse_adjusted_closing_time(text: str) -> str | None:
    """Extract an announced closing time ("geopend tot 16:00 uur").

    Also accepts the older wording ("sluiten de milieustraten om 16 uur"),
    including a whole-hour time without minutes.
    """

    for pattern in (_OPEN_UNTIL, _CLOSES_AT):
        match = pattern.search(text)

        if match is None:
            continue

        hour = int(match.group("hour"))
        minute = int(match.group("minute") or 0)

        if hour > 23 or minute > 59:
            continue

        return f"{hour:02d}:{minute:02d}"

    return None


def _expand_days(days: str) -> list[int]:
    """Expand a day list ("25 en 26", "23 t/m 27") into day numbers."""

    numbers = list(_DAY_NUMBER.finditer(days))

    result: list[int] = []

    for index, number in enumerate(numbers):
        day = int(number.group())

        if index == 0:
            result.append(day)
            continue

        previous = int(numbers[index - 1].group())
        between = days[numbers[index - 1].end() : number.start()]

        if _RANGE_SEPARATOR.search(between) and previous < day:
            result.extend(range(previous + 1, day + 1))
        else:
            result.append(day)

    return result


def _closing_day_date(
    day: int,
    month: int,
    year: int | None,
    today: date,
    heading_year: int | None,
) -> date | None:
    """Build one closing day date, inferring the year when it is missing.

    A year written in the entry itself always wins. Failing that the year
    from the block's own heading is used: it can be out of date, but a
    date in the past simply never applies, which is the safe way to be
    wrong. Only when there is no year anywhere does the entry get read as
    the coming occurrence, the same way an end date is.
    """

    if year is None:
        year = heading_year

    if year is not None:
        try:
            return date(year, month, day)
        except ValueError:
            return None

    try:
        result = date(today.year, month, day)
    except ValueError:
        return None

    if (today - result) > timedelta(days=30):
        try:
            return date(today.year + 1, month, day)
        except ValueError:
            return None

    return result


def _closing_day_dates(text: str, today: date, heading_year: int | None) -> list[date]:
    """Extract every date mentioned in one closing days entry."""

    result: list[date] = []

    for match in _CLOSING_DAY_DATE.finditer(text):
        month = _MONTHS[match.group("month").lower()]
        year = int(match.group("year")) if match.group("year") else None

        for day in _expand_days(match.group("days")):
            resolved = _closing_day_date(day, month, year, today, heading_year)

            if resolved is not None and resolved not in result:
                result.append(resolved)

    return result


def parse_closing_days(heading: str, lines: list[str], today: date) -> list[Notice]:
    """Parse the "Sluitingsdagen" block into notices.

    Every line becomes at most one Notice: a full closure for a listed
    closing day, or a closing time adjustment for a line announcing that
    the recycling centre stays open until some other time than usual.
    Lines without a date (the intro sentence, the house rules that share
    the block) yield nothing, so surrounding prose is ignored rather than
    misread.
    """

    heading_year_match = _YEAR.search(heading)
    heading_year = int(heading_year_match.group()) if heading_year_match else None

    result: list[Notice] = []

    for line in lines:
        dates = _closing_day_dates(line, today, heading_year)

        if not dates:
            continue

        closes = parse_adjusted_closing_time(line)

        if closes is not None:
            result.append(
                Notice(
                    reason="aangepaste sluitingstijd",
                    title=line,
                    closed=False,
                    closes=closes,
                    dates=dates,
                )
            )
            continue

        result.append(
            Notice(
                reason="sluitingsdag",
                title=line,
                closed=True,
                dates=dates,
            )
        )

    if not result:
        LOGGER.debug("Found a closing days block but could not parse it: %s", heading)

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

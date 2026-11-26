"""The list of closing days around public holidays.

Cure lists them once per municipality page under a heading like
"Sluitingsdagen 2026", one line per day or span of days, each saying the
location is closed or open with adjusted hours.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from ..logger import LOGGER
from ..models import Notice
from .dates import MONTH_PATTERN, MONTHS, NUMERIC_DATE, WEEKDAY_PATTERN, YEAR
from .times import parse_adjusted_hours, parse_time_range

# One or more day numbers sharing a single month, as Cure writes them in
# the closing days list: "6", "25 en 26", "23 t/m 27". A weekday may be
# repeated before every number ("25 en zaterdag 26 december").
_DAY_SEPARATOR = r"(?:,|&|\ben\b|t/m|tot en met|[-–—])"

_DAY_LIST = (
    rf"\d{{1,2}}"
    rf"(?:\s*{_DAY_SEPARATOR}\s*(?:(?:{WEEKDAY_PATTERN})\s+)?\d{{1,2}})*"
)

_CLOSING_DAY_DATE = re.compile(
    rf"(?:\b(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<days>{_DAY_LIST})\s+"
    rf"(?P<month>{MONTH_PATTERN})\b"
    rf"(?:\s+(?P<year>\d{{4}})(?!\d))?",
    re.IGNORECASE,
)

_DAY_NUMBER = re.compile(r"\d{1,2}")

# Only these mean "everything in between is included too"; "en" and a
# comma list separate days instead of spanning them.
_RANGE_SEPARATOR = re.compile(r"t/m|tot en met|[-–—]", re.IGNORECASE)

# The same idea between two full dates ("25 december tot en met 4 januari"),
# where a bare dash has to stand on its own to count: the text between two
# dates is ordinary prose, and municipality names such as Geldrop-Mierlo
# carry a hyphen of their own.
_SPANNING_SEPARATOR = re.compile(r"t/m|tot en met|\s[-–—]\s", re.IGNORECASE)

# A closing days list announces days off around a holiday, not a closure of
# months; a range coming out longer than this is read as a misparse.
_MAX_SPAN_DAYS = 31

# Wording that says the location is open rather than shut. Both are whole
# words: "openingstijden" is not a statement that anything is open.
_OPEN_WORDING = re.compile(r"\b(?:geopend|open|opent|openen|opengaan)\b", re.IGNORECASE)

_CLOSED_WORDING = re.compile(r"\b(?:gesloten|dicht|sluit\w*)\b", re.IGNORECASE)


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


def _dates_in_match(
    match: re.Match[str], today: date, heading_year: int | None
) -> list[date]:
    """Return every date one "<dagen> <maand> [jaar]" match stands for."""

    month = MONTHS[match.group("month").lower()]
    year = int(match.group("year")) if match.group("year") else None

    result: list[date] = []

    for day in _expand_days(match.group("days")):
        resolved = _closing_day_date(day, month, year, today, heading_year)

        if resolved is not None:
            result.append(resolved)

    return result


def _a_year_later(dates: list[date]) -> list[date] | None:
    """Return the same dates one year on, or None if a date does not exist."""

    try:
        return [date(day.year + 1, day.month, day.day) for day in dates]
    except ValueError:
        return None


def _span(start: date, dates: list[date], explicit_year: bool) -> list[date]:
    """Return every day of a range running from start into dates.

    Only the two ends of a range spanning two months are written out ("van
    25 december tot en met 4 januari"), so the days in between are filled
    in here. Such a range crosses new year without saying so, which puts
    its end before its start; that end is then read as the next year.

    A range coming out longer than _MAX_SPAN_DAYS is left as its two ends
    alone: only those two dates were actually announced, and reading a
    misparsed line as a closure of months is the more harmful way to be
    wrong.
    """

    if dates[0] < start and not explicit_year:
        shifted = _a_year_later(dates)

        if shifted is not None:
            dates = shifted

    end = dates[0]

    if end < start or (end - start).days > _MAX_SPAN_DAYS:
        LOGGER.debug("Ignoring an implausible closing days range: %s to %s", start, end)

        return dates

    between = [
        start + timedelta(days=offset) for offset in range(1, (end - start).days)
    ]

    return between + dates


def _closing_day_dates(text: str, today: date, heading_year: int | None) -> list[date]:
    """Extract every date one closing days entry stands for.

    A date written in numbers ("06-04-2026") is read first and on its own:
    it carries its own year and cannot be part of a range written the way
    the dates in words are.
    """

    result: list[date] = []

    for match in NUMERIC_DATE.finditer(text):
        try:
            found = date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        except ValueError:
            continue

        if found not in result:
            result.append(found)

    if result:
        return result

    previous_end: int | None = None

    for match in _CLOSING_DAY_DATE.finditer(text):
        dates = _dates_in_match(match, today, heading_year)

        if (
            dates
            and result
            and previous_end is not None
            and _SPANNING_SEPARATOR.search(text[previous_end : match.start()])
        ):
            dates = _span(result[-1], dates, match.group("year") is not None)

        for day in dates:
            if day not in result:
                result.append(day)

        previous_end = match.end()

    return result


def _closing_days_notice(line: str, dates: list[date]) -> Notice | None:
    """Turn one dated closing days entry into a notice.

    A line naming an opening or closing time adjusts that day's hours; one
    naming neither closes it. A line that says the location is open on
    that date but whose times could not be read yields nothing at all,
    since calling it closed would state the opposite of what it says.
    """

    opens, closes = parse_adjusted_hours(line)

    # A bare range behind the date ("Zaterdag 26 december: 10:00 tot
    # 14:00") is as much an opening time as one with "geopend van" in
    # front of it; without this the day would read as closed.
    if opens is None and closes is None:
        opens, closes = parse_time_range(line) or (None, None)

    if opens is not None or closes is not None:
        return Notice(
            reason="aangepaste openingstijden",
            title=line,
            closed=False,
            opens=opens,
            closes=closes,
            dates=dates,
        )

    if _OPEN_WORDING.search(line) and not _CLOSED_WORDING.search(line):
        LOGGER.debug("Skipping a closing days entry with unreadable times: %s", line)

        return None

    return Notice(reason="sluitingsdag", title=line, closed=True, dates=dates)


def parse_closing_days(heading: str, lines: list[str], today: date) -> list[Notice]:
    """Parse the "Sluitingsdagen" block into notices.

    Every line becomes at most one Notice: a full closure for a listed
    closing day, or an hours adjustment for a line announcing different
    opening times on it. Lines without a date (the intro sentence, the
    house rules that share the block) yield nothing, so surrounding prose
    is ignored rather than misread.
    """

    heading_year_match = YEAR.search(heading)
    heading_year = int(heading_year_match.group()) if heading_year_match else None

    result: list[Notice] = []

    for line in lines:
        dates = _closing_day_dates(line, today, heading_year)

        if not dates:
            continue

        notice = _closing_days_notice(line, dates)

        if notice is not None:
            result.append(notice)

    if not result:
        LOGGER.debug("Found a closing days block but could not parse it: %s", heading)

    return result

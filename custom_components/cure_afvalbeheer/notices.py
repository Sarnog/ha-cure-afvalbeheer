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

# The same idea between two full dates ("25 december tot en met 4 januari"),
# where a bare dash has to stand on its own to count: the text between two
# dates is ordinary prose, and municipality names such as Geldrop-Mierlo
# carry a hyphen of their own.
_SPANNING_SEPARATOR = re.compile(r"t/m|tot en met|\s[-–—]\s", re.IGNORECASE)

# A closing days list announces days off around a holiday, not a closure of
# months; a range coming out longer than this is read as a misparse.
_MAX_SPAN_DAYS = 31

_YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")

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

_CLOSES_AT = re.compile(
    r"\bsluit(?:en)?(?:\s+\w+){0,4}?\s+om\s+"
    r"(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

_OPENS_AT = re.compile(
    r"\b(?:(?:geopend|open)\s+(?:vanaf|om)|vanaf|pas\s+om)\s+"
    r"(?P<hour>\d{1,2})(?:[:.](?P<minute>\d{2}))?(?!\d)",
    re.IGNORECASE,
)

_TRAILING_HOUR_UNIT = re.compile(r"^\s*uur\b", re.IGNORECASE)

# Wording that says the location is open rather than shut. Both are whole
# words: "openingstijden" is not a statement that anything is open.
_OPEN_WORDING = re.compile(r"\b(?:geopend|open|opent|openen|opengaan)\b", re.IGNORECASE)

_CLOSED_WORDING = re.compile(r"\b(?:gesloten|dicht|sluit\w*)\b", re.IGNORECASE)


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


def _hhmm(hour: str, minute: str | None) -> str | None:
    """Return an "HH:MM" time, or None if the numbers are not a time."""

    hours = int(hour)
    minutes = int(minute) if minute is not None else 0

    if hours > 23 or minutes > 59:
        return None

    return f"{hours:02d}:{minutes:02d}"


def _lone_time(match: re.Match[str], text: str) -> str | None:
    """Return the time a single-time match found, if it is one at all.

    A whole hour only counts as a time when "uur" follows it: "vanaf 10
    uur" is a time, "vanaf 6 april" is a date. A time written with minutes
    needs no such confirmation.
    """

    minute = match.group("minute")

    if minute is None and not _TRAILING_HOUR_UNIT.match(text[match.end() :]):
        return None

    return _hhmm(match.group("hour"), minute)


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
        opens = _hhmm(range_match.group("open_hour"), range_match.group("open_minute"))
        closes = _hhmm(
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

    month = _MONTHS[match.group("month").lower()]
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
    """Extract every date one closing days entry stands for."""

    result: list[date] = []

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

    heading_year_match = _YEAR.search(heading)
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

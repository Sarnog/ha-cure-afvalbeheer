"""Dates as Cure writes them in free Dutch text.

Notices name their dates in every way a person would: "06-04-2026",
"maandag 6 april", "t/m 12 juni", "vanaf 1 december 2026". The functions
here turn that wording into dates, and return None (or nothing) when the
expected pattern is not there, so reworded text is skipped rather than
misread.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

MONTHS = {
    "januari": 1,
    "jan": 1,
    "februari": 2,
    "feb": 2,
    "maart": 3,
    "mrt": 3,
    "april": 4,
    "apr": 4,
    "mei": 5,
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "augustus": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "oktober": 10,
    "okt": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
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

# Longest first: in an alternation the first match wins, and "januari"
# read as "jan" would leave "uari" behind to break the pattern around it.
MONTH_PATTERN = "|".join(sorted(MONTHS, key=len, reverse=True))
WEEKDAY_PATTERN = "|".join(_WEEKDAYS)

# A date written in numbers ("06-04-2026", "6/4/2026"). The year has to be
# written out in full: two digits leave too much room for a house number or
# a time to be read as a date.
NUMERIC_DATE = re.compile(
    r"(?<!\d)(?P<day>\d{1,2})[-/.](?P<month>\d{1,2})[-/.](?P<year>\d{4})(?!\d)"
)

# Cure labels the date a location closes for good in more than one way,
# and writes the date itself either in numbers or in words.
_EXPLICIT_CLOSURE_DATE = re.compile(
    r"(?:datum\s+(?:van\s+)?sluiting|sluitingsdatum)\s*:?\s*(?P<date>.{0,32})",
    re.IGNORECASE,
)

# Cure words the end of a temporary deviation as "tot en met", "t/m" or
# plain "tot". A bare dash is not accepted here: on its own it reads as
# ordinary punctuation, and only inside a range (below) does it clearly
# separate two dates.
_RELATIVE_END_DATE = re.compile(
    rf"\b(?:tot en met|t/m|tot)\s+(?:(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<day>\d{{1,2}})\s+(?P<month>{MONTH_PATTERN})\b",
    re.IGNORECASE,
)

# One date on its own ("Hitteprotocol 13 augustus"), used only where no
# period was written at all.
SINGLE_DATE = re.compile(
    rf"(?:\b(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<day>\d{{1,2}})\s+(?P<month>{MONTH_PATTERN})\b",
    re.IGNORECASE,
)

# A period written as two dates without years, the way a heading names the
# season it applies to ("Openingstijden winter (1 oktober t/m 31 maart)").
# Both months are spelled out here: without them this is not a season but
# a couple of numbers.
_MONTH_DAY_RANGE = re.compile(
    rf"(?<!\d)(?P<start_day>\d{{1,2}})\s+(?P<start_month>{MONTH_PATTERN})\b"
    rf"\s*(?:tot en met|t/m|tot|[-–—])\s*"
    rf"(?<!\d)(?P<end_day>\d{{1,2}})\s+(?P<end_month>{MONTH_PATTERN})\b",
    re.IGNORECASE,
)

# A period written out with both of its ends ("van 13 t/m 15 augustus",
# "13 tot en met 15 Augustus", "van 30 juli - 2 augustus"). The month is
# usually written behind the end date only, so the start date borrows it.
# Requiring a month behind the end date is what keeps times out of this:
# in "van 08:00 tot 14:00" no month name follows the second number.
_RELATIVE_DATE_RANGE = re.compile(
    rf"(?:\bvan(?:af)?\s+)?(?:(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<start_day>\d{{1,2}})"
    rf"(?:\s+(?P<start_month>{MONTH_PATTERN}))?"
    rf"\s*(?:tot en met|t/m|tot|[-–—])\s*"
    rf"(?:(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?<!\d)(?P<end_day>\d{{1,2}})\s+(?P<end_month>{MONTH_PATTERN})\b",
    re.IGNORECASE,
)

# The dates a closure notice lists in its body ("Dinsdag 30 juni 2026").
# The weekday in front stays required: it is what separates a list of
# closing dates from a date mentioned in passing in the surrounding prose.
# The year behind it does not - Cure leaves it out as often as not.
_DATED_LIST_ENTRY = re.compile(
    rf"(?:{WEEKDAY_PATTERN})\s+(?<!\d)(?P<day>\d{{1,2}})\s+"
    rf"(?P<month>{MONTH_PATTERN})\b(?:\s+(?P<year>\d{{4}})(?!\d))?",
    re.IGNORECASE,
)

YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


def season_covers(text: str, day: date) -> bool | None:
    """Return whether a season named in text is the one day falls in.

    Cure could well split its opening hours into a summer and a winter
    set, naming the months each applies to in the heading. Such a period
    carries no year and may run through new year ("1 oktober t/m 31
    maart"), so only day and month are compared.

    Returns None when the text names no such period at all, which is a
    different answer from "no": the caller can tell "this is the wrong
    season" apart from "this heading says nothing about seasons".
    """

    match = _MONTH_DAY_RANGE.search(text)

    if match is None:
        return None

    start = (MONTHS[match.group("start_month").lower()], int(match.group("start_day")))
    end = (MONTHS[match.group("end_month").lower()], int(match.group("end_day")))

    current = (day.month, day.day)

    if start <= end:
        return start <= current <= end

    # A period running through new year: December is as much part of it as
    # January is.
    return current >= start or current <= end


def parse_numeric_date(text: str) -> date | None:
    """Extract the first date written in numbers, if there is one."""

    match = NUMERIC_DATE.search(text)

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


def relative_date(day: int, month: int, today: date) -> date | None:
    """Build a date from a day and month, inferring the year.

    The year is never written for a currently active notice. If the date
    would land more than 30 days in the past, assume it rolled over into
    the next year (e.g. a notice made in late December about early
    January).
    """

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


def _a_month_earlier(day: date) -> date | None:
    """Return the same day number one month earlier, if it exists."""

    month = day.month - 1 if day.month > 1 else 12
    year = day.year if day.month > 1 else day.year - 1

    try:
        return date(year, month, day.day)
    except ValueError:
        return None


def _a_year_earlier(day: date) -> date | None:
    """Return the same day one year earlier, if it exists.

    29 February does not, three years out of four.
    """

    try:
        return date(day.year - 1, day.month, day.day)
    except ValueError:
        return None


def _range_start(day: int, month: int, end: date, month_written: bool) -> date | None:
    """Build the start date of a range that ends on end.

    The start borrows the end's year, and its month too when the text does
    not write one ("van 13 t/m 15 augustus"). Either can put the start
    behind the end: a range running into a new month ("van 30 t/m 2
    augustus") is one month earlier, one running into a new year ("van 28
    december t/m 4 januari") one year. Anything still out of order after
    that is not read as a start date at all, leaving the notice to apply
    from today - the same as when no start date is written.
    """

    try:
        start = date(end.year, month, day)
    except ValueError:
        return None

    if start <= end:
        return start

    shifted = _a_year_earlier(start) if month_written else _a_month_earlier(start)

    if shifted is None or shifted > end:
        return None

    return shifted


def parse_relative_date_range(
    text: str, today: date
) -> tuple[date | None, date | None]:
    """Extract the period a currently active notice announces.

    Returns it as (starts, ends). Cure writes such a period either with
    both of its ends ("van 13 t/m 15 augustus") or with only the last one
    ("tot en met donderdag 16 juli"); in the latter case starts is None and
    the notice applies from today. Both are None when the text announces no
    period at all.
    """

    match = _RELATIVE_DATE_RANGE.search(text)

    if match is not None:
        end = relative_date(
            int(match.group("end_day")),
            MONTHS[match.group("end_month").lower()],
            today,
        )

        if end is None:
            return None, None

        start_month = match.group("start_month")

        start = _range_start(
            int(match.group("start_day")),
            MONTHS[(start_month or match.group("end_month")).lower()],
            end,
            start_month is not None,
        )

        return start, end

    match = _RELATIVE_END_DATE.search(text)

    if match is None:
        return None, None

    end = relative_date(
        int(match.group("day")),
        MONTHS[match.group("month").lower()],
        today,
    )

    return None, end


def parse_relative_end_date(text: str, today: date) -> date | None:
    """Extract the end date of a currently active notice, if it has one."""

    return parse_relative_date_range(text, today)[1]


def parse_explicit_closure_date(text: str, today: date | None = None) -> date | None:
    """Extract the date behind a "Datum sluiting:" label.

    The date itself is read in numbers ("30-11-2025") or in words ("30
    november 2025"); only the text right behind the label is looked at, so
    a date elsewhere in the notice cannot be mistaken for this one.
    """

    match = _EXPLICIT_CLOSURE_DATE.search(text)

    if match is None:
        return None

    written = match.group("date")

    numeric = parse_numeric_date(written)

    if numeric is not None:
        return numeric

    return _first_written_date(written, today if today is not None else date.today())


def _first_written_date(text: str, today: date) -> date | None:
    """Return the first date written out in words, if there is one."""

    match = SINGLE_DATE.search(text)

    if match is None:
        return None

    month = MONTHS[match.group("month").lower()]
    day = int(match.group("day"))

    year_match = YEAR.search(text[match.end() :])

    if year_match is not None:
        try:
            return date(int(year_match.group()), month, day)
        except ValueError:
            return None

    return relative_date(day, month, today)


def parse_dated_list(text: str, today: date | None = None) -> list[date]:
    """Extract a list of "<weekday> <dag> <maand> [jaar]" entries."""

    if today is None:
        today = date.today()

    result: list[date] = []

    for match in NUMERIC_DATE.finditer(text):
        try:
            result.append(
                date(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            )
        except ValueError:
            continue

    for match in _DATED_LIST_ENTRY.finditer(text):
        month = MONTHS[match.group("month").lower()]
        day = int(match.group("day"))
        year = match.group("year")

        if year is not None:
            try:
                found = date(int(year), month, day)
            except ValueError:
                continue
        else:
            found = relative_date(day, month, today)

        if found is not None and found not in result:
            result.append(found)

    return result


# The words Cure puts in front of the date a new set of regular hours
# starts on ("Vanaf dinsdag 1 december 2026", "Per 1 januari 2027",
# "Met ingang van 01-03-2027"). The date has to follow within a few words,
# which keeps "per bezoek" or "vanaf 10:00" from counting.
_EFFECTIVE_FROM = re.compile(
    r"\b(?:vanaf|per|met ingang van|m\.?\s?i\.?\s?v\.?)\s+(?P<rest>.{0,40})",
    re.IGNORECASE,
)

# The words in front of the last date a set of hours applies to
# ("Openingstijden tot en met 30 november 2026").
_EFFECTIVE_UNTIL = re.compile(
    r"\b(?:tot en met|t/m)\s+(?P<rest>.{0,40})",
    re.IGNORECASE,
)

# A date right at the start of a text, written in words or in numbers,
# with an optional weekday in front of it.
_LEADING_DATE = re.compile(
    rf"^\s*(?:(?:{WEEKDAY_PATTERN})\s+)?"
    rf"(?:\d{{1,2}}\s+(?:{MONTH_PATTERN})\b|\d{{1,2}}[-/.]\d{{1,2}}[-/.]\d{{4}})",
    re.IGNORECASE,
)

# A line that only announces when something starts: the date marker, its
# punctuation and nothing else of substance ("Vanaf 1 december 2026:").
_EFFECTIVE_WORDING = re.compile(
    r"^\s*(?:vanaf|per|met ingang van|m\.?\s?i\.?\s?v\.?)\b", re.IGNORECASE
)


def _date_behind(pattern: re.Pattern[str], text: str, today: date) -> date | None:
    """Return the date written right behind a pattern's words, if any."""

    for match in pattern.finditer(text):
        rest = match.group("rest")

        # Only a date at the very start of the text behind the words
        # counts, so "per bezoek, open 1 december" is not read as one.
        if _LEADING_DATE.match(rest) is None:
            continue

        numeric = parse_numeric_date(rest)

        if numeric is not None:
            return numeric

        written = _first_written_date(rest, today)

        if written is not None:
            return written

    return None


def parse_effective_from(text: str, today: date) -> date | None:
    """Return the date a set of hours starts on ("Vanaf 1 december 2026")."""

    return _date_behind(_EFFECTIVE_FROM, text, today)


def parse_effective_until(text: str, today: date) -> date | None:
    """Return the last date a set of hours applies to ("t/m 30 november")."""

    return _date_behind(_EFFECTIVE_UNTIL, text, today)


def announces_effective_date(text: str) -> bool:
    """Return whether a line opens like a "Vanaf <datum>" announcement.

    Used to notice a start date that is there but could not be read: the
    line clearly means to announce one, so ignoring it silently would be
    the same mistake as missing the new hours themselves.
    """

    return _EFFECTIVE_WORDING.match(text) is not None


def mentions_date(text: str) -> bool:
    """Return whether a text names a date, in words or in numbers."""

    return bool(SINGLE_DATE.search(text) or NUMERIC_DATE.search(text))

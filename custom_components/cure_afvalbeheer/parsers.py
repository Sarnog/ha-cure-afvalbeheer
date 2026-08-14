"""Text parsers for Cure Afvalbeheer.

The opening hours are the one part of the page written as a list of
labelled lines ("Maandag: 08:30 tot 17:00"), so unlike the free-text
notices they are read with a fixed shape: a day label, a colon, and either
a time range or a word meaning closed. Every part of that shape is matched
loosely, because the wording of the label and the punctuation between the
times are the parts Cure changes without warning.
"""

from __future__ import annotations

import re

from .exceptions import ParserError
from .logger import LOGGER
from .models import OpeningHours
from .times import CLOCK_SEPARATOR, RANGE_SEPARATOR, hhmm
from .weekday import Weekday

_TIME_RANGE = re.compile(
    rf"(?<!\d)(?P<open_hour>\d{{1,2}}){CLOCK_SEPARATOR}(?P<open_minute>\d{{2}})"
    rf"\s*{RANGE_SEPARATOR}\s*"
    rf"(?P<close_hour>\d{{1,2}}){CLOCK_SEPARATOR}(?P<close_minute>\d{{2}})(?!\d)",
    re.IGNORECASE,
)

# The days in the order a range runs through them. Sunday closes the week
# here because Cure writes its week that way ("maandag t/m zondag").
_WEEK = (
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
    Weekday.SATURDAY,
    Weekday.SUNDAY,
)

_DAY_NAMES = {
    "maandag": Weekday.MONDAY,
    "ma": Weekday.MONDAY,
    "dinsdag": Weekday.TUESDAY,
    "di": Weekday.TUESDAY,
    "woensdag": Weekday.WEDNESDAY,
    "wo": Weekday.WEDNESDAY,
    "donderdag": Weekday.THURSDAY,
    "do": Weekday.THURSDAY,
    "vrijdag": Weekday.FRIDAY,
    "vr": Weekday.FRIDAY,
    "vrij": Weekday.FRIDAY,
    "zaterdag": Weekday.SATURDAY,
    "za": Weekday.SATURDAY,
    "zat": Weekday.SATURDAY,
    "zondag": Weekday.SUNDAY,
    "zo": Weekday.SUNDAY,
    "zon": Weekday.SUNDAY,
}

# "Zon & Feestdagen", "Zon- en feestdagen", "Zondag en feestdagen": all of
# them label the same line, and what they have in common is the word for a
# public holiday.
_HOLIDAY_WORD = re.compile(r"feestdag", re.IGNORECASE)

_CLOSED_WORD = re.compile(r"\bgesloten\b|\bdicht\b", re.IGNORECASE)

# What separates the two ends of a day range ("maandag t/m vrijdag"), as
# opposed to a list of separate days ("zaterdag en zondag").
_DAY_RANGE = re.compile(rf"\s*{RANGE_SEPARATOR}\s*", re.IGNORECASE)

_DAY_LIST = re.compile(r"\s*(?:,|&|\ben\b|/)\s*", re.IGNORECASE)

_LABEL_NOISE = re.compile(r"[. ]+")


def _normalise(text: str) -> str:
    """Return a day label reduced to lower-case words and spaces."""

    return " ".join(_LABEL_NOISE.sub(" ", text).lower().split())


def _named_day(label: str) -> Weekday | None:
    """Return the weekday one label names, if it names one."""

    return _DAY_NAMES.get(_normalise(label).replace("-", "").strip())


def _day_range(start: Weekday, end: Weekday) -> list[Weekday]:
    """Return every day from start through end, the week's order applying."""

    first = _WEEK.index(start)
    last = _WEEK.index(end)

    if last < first:
        return [start, end]

    return list(_WEEK[first : last + 1])


def days_in_label(label: str) -> list[Weekday]:
    """Return every weekday a day label stands for.

    One label can name a single day ("Maandag"), a range ("Maandag t/m
    vrijdag"), a list ("Zaterdag en zondag") or the public holidays. An
    unreadable label yields nothing, leaving the line to be skipped rather
    than filed under the wrong day.
    """

    normalised = _normalise(label)

    if _HOLIDAY_WORD.search(normalised):
        return [Weekday.HOLIDAY]

    ends = _DAY_RANGE.split(normalised)

    if len(ends) == 2:
        start = _named_day(ends[0])
        end = _named_day(ends[1])

        if start is not None and end is not None:
            return _day_range(start, end)

    days: list[Weekday] = []

    for part in _DAY_LIST.split(normalised):
        day = _named_day(part)

        if day is None:
            return []

        if day not in days:
            days.append(day)

    return days


def parse_time_range(value: str) -> tuple[str, str] | None:
    """Extract an opening and closing time from an opening hours value."""

    match = _TIME_RANGE.search(value)

    if match is None:
        return None

    opens = hhmm(match.group("open_hour"), match.group("open_minute"))
    closes = hhmm(match.group("close_hour"), match.group("close_minute"))

    if opens is None or closes is None:
        return None

    return opens, closes


def _split_line(line: str) -> tuple[str, str] | None:
    """Split an opening hours line into its label and its value.

    The value is whatever the line says about the day: a time range, or a
    word meaning closed. Where that value begins is what splits the line,
    because the colon Cure writes behind the day is not always there - a
    table row puts label and value in separate cells instead, leaving
    "Maandag 08.30 - 17.00" without one. A colon in front of the value
    still wins as the separator, so none of the label is carried into it.
    """

    anchor = _TIME_RANGE.search(line) or _CLOSED_WORD.search(line)

    if anchor is None:
        return None

    colon = line.find(":")

    if colon != -1 and colon < anchor.start():
        return line[:colon].strip(), line[colon + 1 :].strip()

    return line[: anchor.start()].strip(" :-"), line[anchor.start() :].strip()


def parse_opening_hours_line(line: str) -> list[OpeningHours]:
    """Parse one opening hours line into an entry per day it covers.

    Raises:
        ParserError: if the line's label or times cannot be read.
    """

    LOGGER.debug("Parsing line: %s", line)

    parts = _split_line(line)

    if parts is None:
        raise ParserError(f"Cannot parse opening hours line: {line}")

    label, value = parts

    days = days_in_label(label)

    if not days:
        raise ParserError(f"Unknown weekday: {label}")

    if _CLOSED_WORD.search(value):
        return [
            OpeningHours(day=day, opens=None, closes=None, closed=True) for day in days
        ]

    times = parse_time_range(value)

    if times is None:
        raise ParserError(f"Cannot parse opening hours line: {line}")

    opens, closes = times

    return [
        OpeningHours(day=day, opens=opens, closes=closes, closed=False) for day in days
    ]


def parse_opening_hours(lines: list[str]) -> list[OpeningHours]:
    """Parse multiple opening hours lines, skipping any that will not read.

    A line that gets this far has already been accepted by
    `is_opening_hours_line`, so a failure here means the two have drifted
    apart. Dropping that one line and saying so beats letting the
    exception travel up and take the whole update with it - the other six
    days are still perfectly good.
    """

    LOGGER.debug("Parsing %d opening hours lines", len(lines))

    result: list[OpeningHours] = []

    for line in lines:
        try:
            result.extend(parse_opening_hours_line(line))
        except ParserError:
            LOGGER.warning("Skipping an unreadable opening hours line: %s", line)

    return result


def is_opening_hours_line(line: str) -> bool:
    """Return True if the line contains opening hours."""

    parts = _split_line(line)

    if parts is None:
        return False

    label, value = parts

    if not days_in_label(label):
        return False

    if _CLOSED_WORD.search(value):
        return True

    return parse_time_range(value) is not None

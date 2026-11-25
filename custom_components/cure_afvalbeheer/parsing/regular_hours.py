"""The regular weekly opening hours, including announced later sets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from bs4 import BeautifulSoup

from ..logger import LOGGER
from ..models import OpeningHours, ScheduledHours
from ..weekday import Weekday
from . import selectors
from .dates import (
    announces_effective_date,
    parse_effective_from,
    parse_effective_until,
    season_covers,
)
from .hours_lines import is_opening_hours_line, mentions_hours, parse_opening_hours


@dataclass(slots=True)
class RegularHours:
    """What the opening hours section says, and what in it would not read."""

    current: list[OpeningHours]
    scheduled: list[ScheduledHours]
    warnings: list[str]


@dataclass(slots=True)
class _Period:
    """One set of regular hours lines as written on the page."""

    starts: date | None
    ends: date | None
    lines: list[str] = field(default_factory=list)


def _merged(
    previous: list[OpeningHours], changes: list[OpeningHours]
) -> list[OpeningHours]:
    """Return previous hours with every day that changes listed replaced."""

    by_day = {hours.day: hours for hours in previous}

    for hours in changes:
        by_day[hours.day] = hours

    return list(by_day.values())


# How far back an announced change is still compared with the hours found.
_ANNOUNCEMENT_MAX_AGE_DAYS = 31

# The colon behind a heading's introduction ("... milieustraten: Ma t/m
# vr ..."), as opposed to the one inside a time like "10:00".
_INTRODUCTION_COLON = re.compile(r"(?<!\d):(?!\d)")

# What separates the days in a one-line summary ("Ma t/m vr 10:00-17:00,
# za 09:00-17:00, zo gesloten.").
_SUMMARY_SEPARATOR = re.compile(r"[,;]|\.\s")

_DAY_NAMES_NL = {
    Weekday.MONDAY: "maandag",
    Weekday.TUESDAY: "dinsdag",
    Weekday.WEDNESDAY: "woensdag",
    Weekday.THURSDAY: "donderdag",
    Weekday.FRIDAY: "vrijdag",
    Weekday.SATURDAY: "zaterdag",
    Weekday.SUNDAY: "zondag",
    Weekday.HOLIDAY: "feestdagen",
}


def _announced_hours_lines(heading: str, lines: list[str]) -> list[str]:
    """Return the readable opening hours lines of an announcement.

    The heading can carry a summary behind a colon, and the lines below it
    spell the hours out per location; both are read.
    """

    candidates: list[str] = []

    parts = _INTRODUCTION_COLON.split(heading, maxsplit=1)

    if len(parts) == 2:
        candidates.extend(_SUMMARY_SEPARATOR.split(parts[1]))

    candidates.extend(lines)

    return [
        line.strip(" .")
        for line in candidates
        if is_opening_hours_line(line.strip(" ."))
    ]


def _same_hours(first: OpeningHours, second: OpeningHours) -> bool:
    """Return whether two entries say the same about their day."""

    if first.closed or second.closed:
        return first.closed == second.closed

    return (first.opens, first.closes) == (second.opens, second.closes)


def _describe(hours: OpeningHours | None) -> str:
    """Return one day's hours the way the warnings write them."""

    if hours is None:
        return "niets"

    if hours.closed:
        return "gesloten"

    return f"{hours.opens}-{hours.closes}"


def hours_block(soup: BeautifulSoup, today: date) -> tuple[str, list[str]]:
    """Return the opening hours block that applies today.

    A page carrying one block is the ordinary case. Should Cure ever
    split its hours into a summer and a winter set, the heading naming
    the months that cover today decides; picking one by document order
    would mean showing winter hours in August. When several blocks
    apply, or none names a season at all, the first is used and the
    log says so - a wrong guess about which set is current is worth
    knowing about.
    """

    # Headings carrying a start date ("Openingstijden vanaf 1 december
    # 2026") are not seasons but successive sets: _periods reads all of
    # them, so they are joined here into one block, each heading kept
    # as the line that announces its start date.
    all_blocks = selectors.blocks_under_heading(
        soup, "Openingstijden", starting_too=True
    )

    if len(all_blocks) > 1 and any(
        parse_effective_from(heading, today) for heading, _ in all_blocks
    ):
        lines: list[str] = []

        for index, (heading, block_lines) in enumerate(all_blocks):
            if index:
                lines.append(heading)

            lines.extend(block_lines)

        return all_blocks[0][0], lines

    blocks = selectors.blocks_under_heading(soup, "Openingstijden")

    if len(blocks) <= 1:
        return blocks[0] if blocks else ("", [])

    current = [block for block in blocks if season_covers(block[0], today)]

    if len(current) == 1:
        return current[0]

    LOGGER.warning(
        "Found %d opening hours blocks and could not tell which one "
        "applies today; using the first: %s",
        len(blocks),
        [heading for heading, _ in blocks],
    )

    return blocks[0]


def _periods(soup: BeautifulSoup, today: date) -> tuple[list[_Period], list[str]]:
    """Split the opening hours block into sets with their start dates.

    Cure announces new regular hours inside the same block as the
    current ones: "Openingstijden tot en met 30 november 2026", the
    current lines, then "Vanaf dinsdag 1 december 2026:" followed by
    the new lines. Every line announcing a start date opens a new set;
    everything before the first one is the set that applies until
    then. The heading's own dates ("vanaf ...", "tot en met ...")
    belong to that first set.

    Lines that look like hours (a time range, a word meaning closed)
    but cannot be read are returned as warnings rather than dropped
    without a word: that silent drop is exactly how announced hours
    once went missing.
    """

    heading, lines = hours_block(soup, today)

    first = _Period(
        starts=parse_effective_from(heading, today),
        ends=parse_effective_until(heading, today),
    )

    periods = [first]
    warnings: list[str] = []

    for line in lines:
        if is_opening_hours_line(line):
            periods[-1].lines.append(line)
            continue

        starts = parse_effective_from(line, today)

        if starts is not None:
            period = _Period(starts=starts, ends=parse_effective_until(line, today))
            periods.append(period)

            # "Vanaf 1 december: maandag t/m vrijdag 10:00 - 17:00"
            # puts the first line of the new set behind the date.
            _, _, rest = line.partition(":")

            if rest and is_opening_hours_line(rest):
                period.lines.append(rest.strip())

            continue

        if announces_effective_date(line):
            warnings.append(f"Ingangsdatum niet leesbaar: {line}")

        elif mentions_hours(line):
            warnings.append(f"Regel niet leesbaar: {line}")

    return periods, warnings


def read_regular_hours(soup: BeautifulSoup, today: date) -> RegularHours:
    """Return today's regular hours, the announced later sets, and warnings.

    A later set only lists what it says: days it leaves out keep the
    hours of the set before it, since "Vanaf 1 januari: zaterdag
    09:00 - 15:00" changes Saturday and nothing else.
    """

    periods, warnings = _periods(soup, today)

    # Sets without a start date apply from the start; dated ones
    # follow in date order, whatever order the page wrote them in.
    undated = [period for period in periods if period.starts is None]
    dated = sorted(
        (period for period in periods if period.starts is not None),
        key=lambda period: period.starts,
    )

    hours: list[OpeningHours] = []
    current: list[OpeningHours] = []
    current_period: _Period | None = None
    scheduled: list[ScheduledHours] = []

    for period in undated + dated:
        if not period.lines:
            if period.starts is not None:
                warnings.append(
                    "Geen openingstijden gevonden bij ingangsdatum "
                    f"{period.starts.strftime('%d-%m-%Y')}"
                )

            continue

        hours = _merged(hours, parse_opening_hours(period.lines))

        if period.starts is None or period.starts <= today or not current:
            # Started already, or the page knows nothing earlier.
            current = hours
            current_period = period
        else:
            scheduled.append(ScheduledHours(starts=period.starts, hours=hours))

    # "Openingstijden tot en met 30 november" with nothing after it,
    # read in December: the page itself says these hours are over.
    if (
        current_period is not None
        and current_period.ends is not None
        and current_period.ends < today
        and not scheduled
    ):
        warnings.append(
            "Openingstijden waren volgens de website geldig tot en met "
            f"{current_period.ends.strftime('%d-%m-%Y')}; nieuwe "
            "openingstijden niet gevonden"
        )

    warnings.extend(_announcement_mismatches(soup, current, scheduled, today))

    for warning in warnings:
        LOGGER.warning("Opening hours: %s", warning)

    return RegularHours(current=current, scheduled=scheduled, warnings=warnings)


def _announcement_mismatches(
    soup: BeautifulSoup,
    current: list[OpeningHours],
    scheduled: list[ScheduledHours],
    today: date,
) -> list[str]:
    """Check the hours found against announcements elsewhere on the page.

    The same change is usually written twice: in the "Openingstijden"
    block and in an announcement of its own. Reading both and comparing
    them turns a reworded or half-updated page into a warning instead of
    sensors that quietly disagree with what a visitor reads.

    Only announcements starting recently or later are checked: one from
    long ago describes hours that may have changed again since.
    """

    warnings: list[str] = []

    for heading, lines in selectors.announcement_blocks(soup):
        starts = parse_effective_from(heading, today)

        if starts is None or (today - starts).days > _ANNOUNCEMENT_MAX_AGE_DAYS:
            continue

        announced = parse_opening_hours(_announced_hours_lines(heading, lines))

        if not announced:
            # The heading promises hours from a date but none of them
            # could be read, so nothing can be checked.
            warnings.append(f"Aankondiging niet leesbaar: {heading}")
            continue

        expected = current

        for later in scheduled:
            if later.starts <= starts:
                expected = later.hours

        by_day = {hours.day: hours for hours in expected}

        for hours in announced:
            found = by_day.get(hours.day)

            if found is not None and _same_hours(found, hours):
                continue

            warnings.append(
                f"Aankondiging vanaf {starts.strftime('%d-%m-%Y')} noemt "
                f"{_DAY_NAMES_NL[hours.day]} {_describe(hours)}, maar de "
                f"openingstijden zeggen {_describe(found)}"
            )

    return warnings

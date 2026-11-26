"""The heat protocol banner.

On hot days Cure opens earlier and closes earlier, and announces that in
the news block on top of the page ("Hitteprotocol: vandaag geopend van
07:00 tot 13:00").
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from ..logger import LOGGER
from ..models import Notice
from .dates import MONTHS, SINGLE_DATE, parse_relative_date_range, relative_date
from .times import parse_adjusted_hours, parse_time_range

_TODAY_WORDING = re.compile(r"\bvandaag\b", re.IGNORECASE)

# A heat protocol covers a spell of hot days, so its period stays within
# roughly a fortnight; anything longer is read as a stale or misparsed
# banner rather than as adjusted hours to apply.
_MAX_HEAT_PROTOCOL_DAYS = 14


def _heat_protocol_period(
    text: str, today: date, current: bool
) -> tuple[date | None, date | None]:
    """Return the period a heat protocol announcement covers.

    A written-out period is preferred. Failing that, an announcement about
    a single day is read as covering that day alone: one lone date is the
    date it names, and "vandaag" is today - but only where the text is
    known to be current. In an archived news item that word still says
    "today" while meaning a day that has long passed.

    Several dates without a period between them say nothing definite, so
    they yield nothing.
    """

    starts, ends = parse_relative_date_range(text, today)

    if ends is not None:
        return starts, ends

    dates = SINGLE_DATE.findall(text)

    if len(dates) == 1:
        day, month = dates[0]

        single = relative_date(int(day), MONTHS[month.lower()], today)

        return single, single

    if current and not dates and _TODAY_WORDING.search(text):
        return today, today

    return None, None


def parse_heat_protocol_notice(
    heading: str, today: date, *, current: bool = True
) -> Notice | None:
    """Parse the site-wide heat protocol banner, if present.

    Matching is on "hitte" rather than the full word, since the same
    announcement turns up as "hitteprotocol", "hitte-protocol" and
    "hittegolf". That alone is never enough to produce a notice: without
    both a readable period and a readable time, nothing is returned.

    Args:
        heading: the announcement's text.
        today: the date to read a period relative to.
        current: whether the text is known to be up to date. Pass False
            for text that may be months old - an archived news item, say -
            so wording that only makes sense today ("vandaag") is not
            taken at face value.
    """

    if "hitte" not in heading.lower():
        return None

    time_range = parse_time_range(heading) or parse_adjusted_hours(heading)
    starts, ends = _heat_protocol_period(heading, today, current)

    if time_range == (None, None) or ends is None:
        LOGGER.debug(
            "Found a hitteprotocol heading but could not parse it: %s", heading
        )
        return None

    if not _is_plausible_heat_protocol(starts, ends, today):
        LOGGER.debug(
            "Ignoring an implausibly long hitteprotocol period: %s to %s",
            starts,
            ends,
        )
        return None

    opens, closes = time_range

    return Notice(
        reason="hitteprotocol",
        title=heading,
        closed=False,
        opens=opens,
        closes=closes,
        starts=starts,
        ends=ends,
    )


def _is_plausible_heat_protocol(
    starts: date | None, ends: date | None, today: date
) -> bool:
    """Return whether a heat protocol period is short enough to believe.

    A heat protocol lasts days, not months. Without a start date the
    notice applies from today, so an end date far ahead would hold the
    adjusted hours in place for weeks on end - which is what a banner left
    standing after the heat has passed produces, since its end date is then
    read as next year's. Such a period is dropped rather than applied.
    """

    if ends is None:
        return False

    start = starts if starts is not None else today

    return timedelta(0) <= (ends - start) <= timedelta(days=_MAX_HEAT_PROTOCOL_DAYS)


def heat_protocol_unreadable(heading: str, today: date) -> bool:
    """Return whether a heat protocol text exists but cannot be read.

    Separates "there is no heat protocol" and "the heat protocol has
    expired" (both fine to ignore) from "there is one and its times or
    period cannot be read" (which leaves the sensors disagreeing with the
    website).
    """

    if "hitte" not in heading.lower():
        return False

    time_range = parse_time_range(heading) or parse_adjusted_hours(heading)
    _, ends = _heat_protocol_period(heading, today, True)

    return time_range == (None, None) or ends is None

"""Date resolution for Cure Afvalbeheer opening hours."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import Location, Notice, OpeningHours
from .weekday import Weekday


@dataclass(slots=True)
class ResolvedDay:
    """Opening hours for one date, after applying any active notices."""

    date: date
    opens: str | None
    closes: str | None
    closed: bool
    reason: str | None


def hours_for_date(location: Location, day: date) -> OpeningHours | None:
    """Return the opening hours of a location for the given date."""

    weekday = Weekday.from_date(day)

    by_day = {hours.day: hours for hours in location.hours}

    if weekday in by_day:
        return by_day[weekday]

    if weekday is Weekday.SUNDAY:
        return by_day.get(Weekday.HOLIDAY)

    return None


def upcoming_hours(
    location: Location,
    start: date,
    days: int = 6,
) -> list[tuple[date, OpeningHours | None]]:
    """Return the opening hours for a range of dates starting at start."""

    result: list[tuple[date, OpeningHours | None]] = []

    for offset in range(days):
        day = start + timedelta(days=offset)
        result.append((day, hours_for_date(location, day)))

    return result


def _notice_applies(notice: Notice, location: Location, day: date) -> bool:
    """Return whether notice applies to location on day."""

    if notice.location_hint is not None and notice.location_hint != location.name:
        return False

    if notice.dates is not None:
        return day in notice.dates

    if notice.starts is not None and day < notice.starts:
        return False

    return notice.ends is None or day <= notice.ends


def resolve_day(
    location: Location,
    day: date,
    notices: list[Notice],
) -> ResolvedDay:
    """Return the opening hours for location on day, applying any notices.

    A full closure notice takes precedence over an hours-adjusting one
    (e.g. a heat protocol) when both happen to apply on the same day.
    """

    applicable = [
        notice for notice in notices if _notice_applies(notice, location, day)
    ]

    if applicable:
        notice = next((n for n in applicable if n.closed), applicable[0])

        return ResolvedDay(
            date=day,
            opens=notice.opens,
            closes=notice.closes,
            closed=notice.closed,
            reason=notice.reason,
        )

    base = hours_for_date(location, day)

    if base is None:
        return ResolvedDay(date=day, opens=None, closes=None, closed=True, reason=None)

    return ResolvedDay(
        date=day,
        opens=base.opens,
        closes=base.closes,
        closed=base.closed,
        reason=None,
    )


def resolve_upcoming(
    location: Location,
    start: date,
    notices: list[Notice],
    days: int = 6,
) -> list[ResolvedDay]:
    """Return resolved opening hours for a range of dates starting at start."""

    return [
        resolve_day(location, start + timedelta(days=offset), notices)
        for offset in range(days)
    ]

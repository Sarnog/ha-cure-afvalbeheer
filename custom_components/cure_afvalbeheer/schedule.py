"""Date resolution for Cure Afvalbeheer opening hours."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

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

    An hours-adjusting notice only ever narrows a day the regular schedule
    already opens: it never opens a day that is closed anyway - a Sunday
    say, or Christmas Day - and it keeps the regular time for whichever of
    the two it does not announce itself, since Cure usually mentions only
    the earlier closing time. Where several adjust the same day, the one
    closing earliest wins, so the outcome does not depend on the order in
    which the page happened to mention them.
    """

    applicable = [
        notice for notice in notices if _notice_applies(notice, location, day)
    ]

    closure = next((notice for notice in applicable if notice.closed), None)

    if closure is not None:
        return ResolvedDay(
            date=day,
            opens=closure.opens,
            closes=closure.closes,
            closed=True,
            reason=closure.reason,
        )

    base = hours_for_date(location, day)

    if base is None or base.closed:
        return ResolvedDay(date=day, opens=None, closes=None, closed=True, reason=None)

    if applicable:
        notice = min(applicable, key=lambda item: item.closes or "99:99")

        return ResolvedDay(
            date=day,
            opens=notice.opens if notice.opens is not None else base.opens,
            closes=notice.closes if notice.closes is not None else base.closes,
            closed=False,
            reason=notice.reason,
        )

    return ResolvedDay(
        date=day,
        opens=base.opens,
        closes=base.closes,
        closed=False,
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


def _combine(day: date, hhmm: str, now: datetime) -> datetime:
    """Combine a date and an "HH:MM" string into a datetime like now."""

    hour, minute = (int(part) for part in hhmm.split(":"))

    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=now.tzinfo)


def next_open_close(
    upcoming: list[ResolvedDay], now: datetime
) -> tuple[datetime | None, datetime | None]:
    """Return the next (next_open, next_close) timestamps in upcoming.

    Both are computed independently of the current open/closed status: if
    currently open, next_close is today's remaining closing time; if
    currently closed, next_open is the next time it opens. Either value is
    None if no such transition exists within the resolved window.
    """

    next_open: datetime | None = None
    next_close: datetime | None = None

    for day in upcoming:
        if day.closed or day.opens is None or day.closes is None:
            continue

        if next_open is None:
            opens_at = _combine(day.date, day.opens, now)

            if opens_at > now:
                next_open = opens_at

        if next_close is None:
            closes_at = _combine(day.date, day.closes, now)

            if closes_at > now:
                next_close = closes_at

        if next_open is not None and next_close is not None:
            break

    return next_open, next_close

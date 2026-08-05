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


def _deciding_reason(
    notices: list[Notice], opens: str | None, closes: str | None
) -> str | None:
    """Return the reason of the notice that decided the resolved hours.

    The closing time is what a visitor runs into first, so the notice
    behind it is named where several apply; only when none of them
    announced a closing time does the opening side get to name it.
    """

    for notice in notices:
        if closes is not None and notice.closes == closes:
            return notice.reason

    for notice in notices:
        if opens is not None and notice.opens == opens:
            return notice.reason

    return notices[0].reason if notices else None


def resolve_day(
    location: Location,
    day: date,
    notices: list[Notice],
) -> ResolvedDay:
    """Return the opening hours for location on day, applying any notices.

    A full closure notice takes precedence over an hours-adjusting one
    (e.g. a heat protocol) when both happen to apply on the same day.

    An hours-adjusting notice only ever applies to a day the regular
    schedule already opens: it never opens a day that is closed anyway - a
    Sunday say, or Christmas Day. Each side is handled on its own, so a
    notice announcing just one of the two leaves the regular time standing
    for the other; Cure usually mentions only an earlier closing time.
    Where several adjust the same day, the strictest of each side wins -
    the latest opening time and the earliest closing time - so the outcome
    never depends on the order in which the page happened to mention them.
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

    if not applicable:
        return ResolvedDay(
            date=day,
            opens=base.opens,
            closes=base.closes,
            closed=False,
            reason=None,
        )

    announced_opens = [n.opens for n in applicable if n.opens is not None]
    announced_closes = [n.closes for n in applicable if n.closes is not None]

    opens = max(announced_opens) if announced_opens else base.opens
    closes = min(announced_closes) if announced_closes else base.closes

    return ResolvedDay(
        date=day,
        opens=opens,
        closes=closes,
        closed=False,
        reason=_deciding_reason(applicable, opens, closes),
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

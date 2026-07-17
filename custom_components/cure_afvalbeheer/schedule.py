"""Date resolution for Cure Afvalbeheer opening hours."""

from __future__ import annotations

from datetime import date, timedelta

from .models import Location, OpeningHours
from .weekday import Weekday


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

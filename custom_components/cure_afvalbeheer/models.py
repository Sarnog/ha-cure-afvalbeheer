"""Models for Cure Afvalbeheer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .weekday import Weekday


@dataclass(slots=True)
class OpeningHours:
    """Opening hours for one day."""

    day: Weekday
    opens: str | None
    closes: str | None
    closed: bool


@dataclass(slots=True)
class ScheduledHours:
    """Regular opening hours that take effect on a later date.

    Cure announces a change of its regular hours ahead of time ("Vanaf
    dinsdag 1 december 2026: ...") next to the hours that still apply, so
    the new set is kept with the date it starts on rather than replacing
    the current one straight away.
    """

    starts: date
    hours: list[OpeningHours]


@dataclass(slots=True)
class Location:
    """One recycling centre."""

    name: str
    address: str | None
    hours: list[OpeningHours]
    # Announced future sets of regular hours, earliest first.
    scheduled: list[ScheduledHours] = field(default_factory=list)


@dataclass(slots=True)
class Notice:
    """A temporary deviation from the regular weekly schedule."""

    reason: str
    title: str
    closed: bool
    opens: str | None = None
    closes: str | None = None
    starts: date | None = None
    ends: date | None = None
    dates: list[date] | None = None
    location_hint: str | None = None


@dataclass(slots=True)
class CureData:
    """Complete parsed Cure data."""

    locations: list[Location]
    notices: list[Notice] = field(default_factory=list)
    # Everything on the page that clearly meant something (hours, a
    # message, a location) but could not be read, so a reworded or
    # rearranged page is reported instead of ignored.
    warnings: list[str] = field(default_factory=list)

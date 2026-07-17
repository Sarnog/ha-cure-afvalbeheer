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
class Location:
    """One recycling centre."""

    name: str
    address: str | None
    hours: list[OpeningHours]


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

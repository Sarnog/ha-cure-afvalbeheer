"""Models for Cure Afvalbeheer."""

from __future__ import annotations

from dataclasses import dataclass

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
class CureData:
    """Complete parsed Cure data."""

    locations: list[Location]

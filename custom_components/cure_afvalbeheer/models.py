"""Models for Cure Afvalbeheer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class OpeningHours:
    """Opening hours for one day."""

    day: str
    opens: str | None
    closes: str | None
    closed: bool


@dataclass(slots=True)
class Location:
    """One recycling centre."""

    name: str
    hours: list[OpeningHours]


@dataclass(slots=True)
class CureData:
    """Complete parsed Cure data."""

    locations: list[Location]

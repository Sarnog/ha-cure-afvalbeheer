"""Weekday definitions."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

_ISO_WEEKDAYS = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)


class Weekday(StrEnum):
    """Supported weekdays."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    HOLIDAY = "holiday"

    @classmethod
    def from_date(cls, day: date) -> Weekday:
        """Return the Weekday matching the given date."""

        return cls[_ISO_WEEKDAYS[day.weekday()]]

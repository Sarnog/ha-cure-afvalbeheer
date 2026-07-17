"""Weekday definitions."""

from __future__ import annotations

from enum import StrEnum


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

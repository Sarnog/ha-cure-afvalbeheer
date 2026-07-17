"""Diagnostics support for Cure Afvalbeheer."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import CureConfigEntry
from .models import CureData, Location, Notice, OpeningHours


def _serialize_hours(hours: OpeningHours) -> dict[str, Any]:
    """Serialise one day's regular opening hours."""

    return {
        "day": hours.day.value,
        "opens": hours.opens,
        "closes": hours.closes,
        "closed": hours.closed,
    }


def _serialize_location(location: Location) -> dict[str, Any]:
    """Serialise one recycling centre."""

    return {
        "name": location.name,
        "address": location.address,
        "hours": [_serialize_hours(hours) for hours in location.hours],
    }


def _serialize_notice(notice: Notice) -> dict[str, Any]:
    """Serialise one active deviation."""

    return {
        "reason": notice.reason,
        "title": notice.title,
        "closed": notice.closed,
        "opens": notice.opens,
        "closes": notice.closes,
        "starts": notice.starts.isoformat() if notice.starts else None,
        "ends": notice.ends.isoformat() if notice.ends else None,
        "dates": [day.isoformat() for day in notice.dates] if notice.dates else None,
        "location_hint": notice.location_hint,
    }


def _serialize_data(data: CureData) -> dict[str, Any]:
    """Serialise the coordinator's parsed data."""

    return {
        "locations": [_serialize_location(location) for location in data.locations],
        "notices": [_serialize_notice(notice) for notice in data.notices],
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CureConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Nothing here needs redacting: entry.data/options only contain the
    chosen municipality and two numbers, and the coordinator data is
    already public information straight from the Cure website.
    """

    coordinator = entry.runtime_data

    return {
        "entry": {
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "data": _serialize_data(coordinator.data) if coordinator.data else None,
        },
    }

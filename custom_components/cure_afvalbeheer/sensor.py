"""Sensor platform for Cure Afvalbeheer."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from . import CureConfigEntry
from .const import DOMAIN, MANUFACTURER, NAME
from .coordinator import CureDataUpdateCoordinator
from .models import Location, OpeningHours
from .schedule import hours_for_date, upcoming_hours

PARALLEL_UPDATES = 0

_UPCOMING_DAYS = 6


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CureConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = entry.runtime_data

    async_add_entities(
        CureLocationSensor(coordinator, entry, location.name)
        for location in coordinator.data.locations
    )


def _serialize_hours(hours: OpeningHours | None) -> dict[str, Any]:
    """Serialise opening hours for use as an entity attribute."""

    if hours is None:
        return {"closed": True, "opens": None, "closes": None}

    return {
        "closed": hours.closed,
        "opens": hours.opens,
        "closes": hours.closes,
    }


class CureLocationSensor(CoordinatorEntity[CureDataUpdateCoordinator], SensorEntity):
    """Sensor representing one Cure recycling centre."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["open", "closed"]
    _attr_translation_key = "milieustraat"

    def __init__(
        self,
        coordinator: CureDataUpdateCoordinator,
        entry: CureConfigEntry,
        location_name: str,
    ) -> None:
        """Initialise the sensor."""

        super().__init__(coordinator)

        self._location_name = location_name
        self._attr_unique_id = f"{entry.entry_id}_{slugify(location_name)}"
        self._attr_name = location_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
        )

    @property
    def _location(self) -> Location | None:
        """Return the current Location data for this sensor."""

        for location in self.coordinator.data.locations:
            if location.name == self._location_name:
                return location

        return None

    @property
    def native_value(self) -> str | None:
        """Return whether the location is currently open."""

        location = self._location

        if location is None:
            return None

        now = dt_util.now()
        today_hours = hours_for_date(location, now.date())

        if today_hours is None or today_hours.closed:
            return "closed"

        if today_hours.opens is None or today_hours.closes is None:
            return "closed"

        current_time = now.strftime("%H:%M")

        if today_hours.opens <= current_time <= today_hours.closes:
            return "open"

        return "closed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the opening hours attributes for dashboards."""

        location = self._location

        if location is None:
            return {}

        today = dt_util.now().date()

        upcoming = upcoming_hours(location, today, _UPCOMING_DAYS)

        return {
            "today": {
                "date": today.isoformat(),
                **_serialize_hours(upcoming[0][1]),
            },
            "upcoming": [
                {"date": day.isoformat(), **_serialize_hours(hours)}
                for day, hours in upcoming[1:]
            ],
        }

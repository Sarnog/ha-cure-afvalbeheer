"""Sensor platform for Cure Afvalbeheer."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from . import CureConfigEntry
from .const import (
    CONF_LOOKAHEAD_DAYS,
    DEFAULT_LOOKAHEAD_DAYS,
    DOMAIN,
    MANUFACTURER,
    MUNICIPALITIES,
    NAME,
)
from .coordinator import CureDataUpdateCoordinator
from .models import Location
from .schedule import ResolvedDay, next_open_close, resolve_day, resolve_upcoming

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CureConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    coordinator = entry.runtime_data

    # NumberSelector-backed options always come back as float, regardless
    # of step/mode; int() protects against a float leaking into range().
    lookahead_days = int(entry.options.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS))

    known_locations: set[str] = set()

    def _entities_for(location: Location) -> list[SensorEntity]:
        return [
            CureLocationSensor(coordinator, entry, location.name, lookahead_days),
            CureReasonSensor(coordinator, entry, location.name, 0, "vandaag"),
            CureReasonSensor(coordinator, entry, location.name, 1, "morgen"),
            CureNextTransitionSensor(
                coordinator,
                entry,
                location.name,
                lookahead_days,
                "open",
                "volgende open",
            ),
            CureNextTransitionSensor(
                coordinator,
                entry,
                location.name,
                lookahead_days,
                "close",
                "volgende gesloten",
            ),
        ]

    @callback
    def _add_new_locations() -> None:
        """Add entities for any location not seen before.

        Cure occasionally adds a new recycling centre to a municipality
        page. Re-checking on every coordinator update means a new
        location gets its entities without requiring a restart.
        """

        new_locations = [
            location
            for location in coordinator.data.locations
            if location.name not in known_locations
        ]

        if not new_locations:
            return

        known_locations.update(location.name for location in new_locations)

        entities: list[SensorEntity] = []

        for location in new_locations:
            entities.extend(_entities_for(location))

        async_add_entities(entities)

    _add_new_locations()

    entry.async_on_unload(coordinator.async_add_listener(_add_new_locations))


def _serialize_day(day: ResolvedDay, *, include_reason: bool) -> dict[str, Any]:
    """Serialise a resolved day for use as an entity attribute."""

    result = {
        "date": day.date.isoformat(),
        "closed": day.closed,
        "opens": day.opens,
        "closes": day.closes,
    }

    if include_reason:
        result["reason"] = day.reason

    return result


def _device_info(
    coordinator: CureDataUpdateCoordinator, entry: CureConfigEntry
) -> DeviceInfo:
    """Return the device a location's entities should be grouped under."""

    municipality_name = MUNICIPALITIES.get(
        coordinator.municipality, coordinator.municipality
    )

    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{NAME} {municipality_name}",
        manufacturer=MANUFACTURER,
    )


class _CureLocationEntity(CoordinatorEntity[CureDataUpdateCoordinator]):
    """Shared behaviour for entities tied to one Cure location.

    A location can disappear from the municipality page (e.g. a
    recycling centre closes permanently). Rather than deleting anything
    ourselves - a transient fetch hiccup could otherwise wipe an entity's
    history for no reason - such entities simply become unavailable. If
    the location is still gone on the next restart, async_setup_entry
    won't recreate it, and Home Assistant's own entity platform then
    offers the user a way to remove the resulting orphaned entity.
    """

    def __init__(
        self,
        coordinator: CureDataUpdateCoordinator,
        location_name: str,
    ) -> None:
        """Initialise the entity."""

        super().__init__(coordinator)

        self._location_name = location_name

    @property
    def _location(self) -> Location | None:
        """Return the current Location data for this entity."""

        for location in self.coordinator.data.locations:
            if location.name == self._location_name:
                return location

        return None

    @property
    def available(self) -> bool:
        """Return whether the location still exists on the page."""

        return super().available and self._location is not None


class CureLocationSensor(_CureLocationEntity, SensorEntity):
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
        lookahead_days: int,
    ) -> None:
        """Initialise the sensor."""

        super().__init__(coordinator, location_name)

        self._lookahead_days = lookahead_days
        self._attr_unique_id = f"{entry.entry_id}_{slugify(location_name)}"
        self._attr_name = location_name
        self._attr_device_info = _device_info(coordinator, entry)

    @property
    def native_value(self) -> str | None:
        """Return whether the location is currently open."""

        location = self._location

        if location is None:
            return None

        now = dt_util.now()
        today = resolve_day(location, now.date(), self.coordinator.data.notices)

        if today.closed or today.opens is None or today.closes is None:
            return "closed"

        current_time = now.strftime("%H:%M")

        if today.opens <= current_time <= today.closes:
            return "open"

        return "closed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the opening hours attributes for dashboards."""

        location = self._location

        if location is None:
            return {}

        today = dt_util.now().date()

        upcoming = resolve_upcoming(
            location,
            today,
            self.coordinator.data.notices,
            self._lookahead_days + 1,
        )

        return {
            "address": location.address,
            "today": _serialize_day(upcoming[0], include_reason=False),
            "upcoming": [
                _serialize_day(day, include_reason=True) for day in upcoming[1:]
            ],
        }


class CureReasonSensor(_CureLocationEntity, SensorEntity):
    """Sensor exposing the deviation reason for one specific day.

    Two instances are created per location (today/tomorrow) so an
    automation can act a day ahead of a change instead of only once it
    has already taken effect.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CureDataUpdateCoordinator,
        entry: CureConfigEntry,
        location_name: str,
        day_offset: int,
        label: str,
    ) -> None:
        """Initialise the sensor."""

        super().__init__(coordinator, location_name)

        self._day_offset = day_offset
        self._attr_unique_id = (
            f"{entry.entry_id}_{slugify(location_name)}_reden_{label}"
        )
        self._attr_name = f"{location_name} reden {label}"
        self._attr_device_info = _device_info(coordinator, entry)

    @property
    def native_value(self) -> str | None:
        """Return the deviation reason, or an empty string if none."""

        location = self._location

        if location is None:
            return None

        day = dt_util.now().date() + timedelta(days=self._day_offset)
        resolved = resolve_day(location, day, self.coordinator.data.notices)

        return resolved.reason or ""


class CureNextTransitionSensor(_CureLocationEntity, SensorEntity):
    """Sensor exposing the next time a location opens or closes.

    Two instances are created per location (open/close) so the values are
    directly usable in automations and dashboards, rather than buried in
    another sensor's attributes.
    """

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: CureDataUpdateCoordinator,
        entry: CureConfigEntry,
        location_name: str,
        lookahead_days: int,
        transition: Literal["open", "close"],
        label: str,
    ) -> None:
        """Initialise the sensor."""

        super().__init__(coordinator, location_name)

        self._lookahead_days = lookahead_days
        self._transition = transition
        self._attr_unique_id = (
            f"{entry.entry_id}_{slugify(location_name)}_volgende_{transition}"
        )
        self._attr_name = f"{location_name} {label}"
        self._attr_device_info = _device_info(coordinator, entry)

    @property
    def native_value(self) -> datetime | None:
        """Return the next opening or closing timestamp."""

        location = self._location

        if location is None:
            return None

        now = dt_util.now()

        upcoming = resolve_upcoming(
            location,
            now.date(),
            self.coordinator.data.notices,
            self._lookahead_days + 1,
        )

        next_open, next_close = next_open_close(upcoming, now)

        return next_open if self._transition == "open" else next_close

"""Datamodels voor Cure Afvalbeheer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


@dataclass(slots=True)
class OpeningHours:
    """Openingstijden voor één dag."""

    open_time: time | None
    close_time: time | None
    status: str = "closed"


@dataclass(slots=True)
class LocationHours:
    """Alle informatie over één milieustraat."""

    name: str
    address: str = ""
    opening_hours: dict[str, OpeningHours] = field(default_factory=dict)


@dataclass(slots=True)
class NewsItem:
    """Nieuwsbericht dat invloed heeft op openingstijden."""

    title: str
    link: str
    description: str
    published: str
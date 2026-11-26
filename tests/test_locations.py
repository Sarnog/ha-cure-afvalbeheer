"""Tests for parsing/locations.py: the recycling centres on a page."""

from bs4 import BeautifulSoup

from custom_components.cure_afvalbeheer.models import Location
from custom_components.cure_afvalbeheer.parsing.locations import (
    location_hint_for,
    read_addresses,
)


def test_a_location_named_after_the_prefix_alone_never_matches():
    locations = [
        Location(name="Milieustraat ", address=None, hours=[]),
        Location(name="Milieustraat Acht", address=None, hours=[]),
    ]

    assert location_hint_for("Let op! Acht dicht", locations) == "Milieustraat Acht"


def test_read_addresses_strips_names_and_reports_a_missing_last_address():
    soup = BeautifulSoup(
        "<div><h2>Adres Milieustraten Eindhoven</h2>"
        "<h3> Milieustraat Acht </h3><p>Achtseweg Noord 41</p>"
        "<h3>Milieustraat Lodewijkstraat</h3></div>",
        "html.parser",
    )

    assert read_addresses(soup) == (
        [
            ("Milieustraat Acht", "Achtseweg Noord 41"),
            ("Milieustraat Lodewijkstraat", None),
        ],
        ["Geen adres gevonden voor Milieustraat Lodewijkstraat"],
    )


def test_read_addresses_joins_the_lines_of_an_address():
    soup = BeautifulSoup(
        "<div><h2>Adres Milieustraat Valkenswaard</h2>"
        "<h3>Milieustraat Valkenswaard</h3><p>Lissevenweg 1<br>5551 SH</p></div>",
        "html.parser",
    )

    assert read_addresses(soup)[0] == [
        ("Milieustraat Valkenswaard", "Lissevenweg 1 5551 SH")
    ]

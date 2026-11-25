from datetime import date
from pathlib import Path

from custom_components.cure_afvalbeheer.models import CureData, Location
from custom_components.cure_afvalbeheer.parsing.locations import location_hint_for
from custom_components.cure_afvalbeheer.parsing.page import CureParser
from custom_components.cure_afvalbeheer.weekday import Weekday


def test_page_title():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    assert parser.page_title() == "Milieustraat Eindhoven"


def test_headings():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    headings = parser.headings()

    assert len(headings) > 5


def test_opening_hours_lines():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    lines = parser.opening_hours_lines()

    assert len(lines) == 7
    assert lines[0].startswith("Maandag")
    assert lines[-1].startswith("Zon")


def test_location_name():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    assert parser.location_name() == "Milieustraat Eindhoven"


def test_parse_locations():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    locations = parser.parse_locations()

    assert len(locations) == 2

    assert locations[0].name == "Milieustraat Acht"
    assert locations[0].address == "Achtseweg Noord 41 5651 GG Eindhoven"

    assert locations[1].name == "Milieustraat Lodewijkstraat"
    assert locations[1].address == "Lodewijkstraat 9 5652 AC Eindhoven"

    assert len(locations[0].hours) == 7
    assert len(locations[1].hours) == 7


def test_location_addresses():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    addresses = parser.location_addresses()

    assert addresses == [
        (
            "Milieustraat Acht",
            "Achtseweg Noord 41 5651 GG Eindhoven",
        ),
        (
            "Milieustraat Lodewijkstraat",
            "Lodewijkstraat 9 5652 AC Eindhoven",
        ),
    ]


def test_location_addresses_falls_back_to_page_title_without_h3():
    """Some single-location municipalities (e.g. Geldrop-Mierlo) have no
    h3 location name in the address section, only the heading and one
    address paragraph."""

    html = """
    <html>
    <body>
    <h1>Milieustraat Geldrop-Mierlo</h1>
    <section>
        <h2>Adres Milieustraat Geldrop-Mierlo</h2>
        <p>Industriepark 8 5663 PG Geldrop</p>
    </section>
    </body>
    </html>
    """

    parser = CureParser(html)

    assert parser.location_addresses() == [
        (
            "Milieustraat Geldrop-Mierlo",
            "Industriepark 8 5663 PG Geldrop",
        ),
    ]


def test_notices_finds_heat_protocol_and_scoped_closure():
    """The Eindhoven fixture contains both a site-wide heat protocol
    banner and a closure notice naming Lodewijkstraat specifically."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)
    locations = parser.parse_locations()

    notices = parser.notices(locations, today=date(2026, 7, 10))

    heat_protocol = next(n for n in notices if n.reason == "hitteprotocol")
    assert heat_protocol.opens == "08:00"
    assert heat_protocol.closes == "14:00"
    assert heat_protocol.ends == date(2026, 7, 16)
    assert heat_protocol.location_hint is None

    closure = next(n for n in notices if n.reason == "verbouwing")
    assert closure.closed is True
    assert closure.location_hint == "Milieustraat Lodewijkstraat"


def test_heat_protocol_notice_from_the_news_block_heading():
    """The heading Cure puts in front of every visitor is read first."""

    html = Path("tests/fixtures/news_block_heat_protocol.html").read_text(
        encoding="utf-8"
    )

    notice = CureParser(html).heat_protocol_notice(date(2026, 8, 14))

    assert notice is not None
    assert notice.title.startswith("Let op! Hitteprotocol van 13 t/m 15 Augustus!")
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.starts == date(2026, 8, 13)
    assert notice.ends == date(2026, 8, 15)


def test_heat_protocol_notice_falls_back_to_the_news_items():
    """When the editors word the heading in a way that cannot be read, the
    news item it links to still spells the period out."""

    html = (
        Path("tests/fixtures/news_block_heat_protocol.html")
        .read_text(encoding="utf-8")
        .replace(
            "Let op! Hitteprotocol van 13 t/m 15 Augustus! Gewijzigde "
            "openingstijden milieustraten van 08:00 tot 14:00.",
            "Let op! Hitteprotocol deze week!",
        )
    )

    notice = CureParser(html).heat_protocol_notice(date(2026, 8, 14))

    assert notice is not None
    assert notice.title.startswith("Hitteprotocol! 13 tot en met 15 Augustus")
    assert notice.opens == "08:00"
    assert notice.closes == "14:00"
    assert notice.ends == date(2026, 8, 15)


def test_heat_protocol_notice_returns_none_without_one():
    html = Path("tests/fixtures/news_block_heat_protocol.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html.replace("Hitteprotocol", "Zomerweetje"))

    assert parser.heat_protocol_notice(date(2026, 8, 14)) is None


def test_notices_finds_the_closing_days():
    """The closing days apply to every recycling centre on the page."""

    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)
    locations = parser.parse_locations()

    notices = parser.notices(locations, today=date(2026, 7, 10))

    closing_days = [n for n in notices if n.reason == "sluitingsdag"]

    assert [day for notice in closing_days for day in notice.dates or []] == [
        date(2026, 4, 6),
        date(2026, 4, 27),
        date(2026, 5, 14),
        date(2026, 5, 25),
        date(2026, 12, 25),
        date(2026, 12, 26),
        date(2027, 1, 1),
    ]

    assert all(notice.location_hint is None for notice in closing_days)

    adjusted = next(n for n in notices if n.reason == "aangepaste openingstijden")
    assert adjusted.closes == "16:00"
    assert adjusted.dates == [date(2026, 12, 24), date(2026, 12, 31)]


_TWO_LOCATIONS = [
    Location(name="Milieustraat Acht", address=None, hours=[]),
    Location(name="Milieustraat Lodewijkstraat", address=None, hours=[]),
]


def test_location_hint_for_matches_a_named_location():
    result = location_hint_for("Let op! Lodewijkstraat wordt verbouwd", _TWO_LOCATIONS)

    assert result == "Milieustraat Lodewijkstraat"


def test_location_hint_for_ignores_a_location_name_inside_another_word():
    """The name "Acht" also sits inside ordinary words like "achteringang"."""

    result = location_hint_for("Let op! De achteringang is gesloten", _TWO_LOCATIONS)

    assert result is None


def test_location_hint_for_ignores_a_heading_naming_both_locations():
    result = location_hint_for(
        "Let op! Acht en Lodewijkstraat zijn gesloten", _TWO_LOCATIONS
    )

    assert result is None


# A page written the way Cure could just as well have written it: hours in
# a table with a day range, a numeric closing day, and the notice heading
# punctuated differently. Not one word of it is content the parser has not
# been asked for - only the shape and spelling differ.
_REWORDED_PAGE = """
<html><body>
<section data-block="newsBlock">
    <div><h2>Let op: hitte-protocol van 13 t/m 15 augustus,
    milieustraten geopend van 08.00 tot 14.00 uur</h2></div>
</section>
<section>
    <h2>Adressen milieustraten Eindhoven</h2>
    <h3>Milieustraat Acht</h3>
    <p>Achtseweg Noord 41 5651 GG Eindhoven</p>
</section>
<section>
    <h2>Openingstijden milieustraat</h2>
    <table>
        <tr><td>Ma t/m vr</td><td>08.30 - 17.00</td></tr>
        <tr><td>Zaterdag</td><td>10:00 tot 16:00</td></tr>
        <tr><td>Zon &amp; feestdagen</td><td>Gesloten</td></tr>
    </table>
    <h2>Sluitingsdata 2026</h2>
    <ul>
        <li>06-04-2026 (Pasen)</li>
        <li>24 dec 2026: geopend tot 16.00 uur</li>
    </ul>
</section>
</body></html>
"""


def test_parse_a_page_written_differently_throughout():
    parser = CureParser(_REWORDED_PAGE)

    locations = parser.parse_locations()

    assert [location.name for location in locations] == ["Milieustraat Acht"]

    hours = {entry.day: entry for entry in locations[0].hours}

    assert hours[Weekday.MONDAY].opens == "08:30"
    assert hours[Weekday.FRIDAY].closes == "17:00"
    assert hours[Weekday.SATURDAY].opens == "10:00"
    assert hours[Weekday.HOLIDAY].closed

    notices = parser.notices(locations, today=date(2026, 8, 14))

    heat_protocol = next(n for n in notices if n.reason == "hitteprotocol")
    assert heat_protocol.starts == date(2026, 8, 13)
    assert heat_protocol.ends == date(2026, 8, 15)
    assert (heat_protocol.opens, heat_protocol.closes) == ("08:00", "14:00")

    closing_day = next(n for n in notices if n.reason == "sluitingsdag")
    assert closing_day.dates == [date(2026, 4, 6)]

    adjusted = next(n for n in notices if n.reason == "aangepaste openingstijden")
    assert adjusted.dates == [date(2026, 12, 24)]
    assert adjusted.closes == "16:00"


def test_heat_protocol_notice_does_not_read_vandaag_from_a_news_item():
    """The banner heading is current; the archive below it is not."""

    html = (
        Path("tests/fixtures/news_block_heat_protocol.html")
        .read_text(encoding="utf-8")
        .replace(
            "Let op! Hitteprotocol van 13 t/m 15 Augustus! Gewijzigde "
            "openingstijden milieustraten van 08:00 tot 14:00.",
            "Welkom bij Cure",
        )
        .replace(
            "Hitteprotocol! 13 tot en met 15 Augustus aangepaste "
            "openingstijden (08:00 - 14:00) op onze milieustraten",
            "Hitteprotocol! Vandaag geopend van 08:00 tot 14:00 uur",
        )
    )

    assert CureParser(html).heat_protocol_notice(date(2026, 10, 1)) is None


_SEASONAL_PAGE = """
<html><body>
<section><h2>Adres Milieustraat Eindhoven</h2>
<h3>Milieustraat Acht</h3><p>Achtseweg Noord 41</p></section>
<section>
    <h2>Openingstijden winter (1 oktober t/m 31 maart)</h2>
    <p>Maandag: 09:00 tot 16:00</p>
    <h2>Openingstijden zomer (1 april t/m 30 september)</h2>
    <p>Maandag: 08:30 tot 17:00</p>
</section>
</body></html>
"""


def test_opening_hours_picks_the_season_that_covers_today():
    """Two sets side by side must not be picked by document order."""

    parser = CureParser(_SEASONAL_PAGE)

    summer = parser.opening_hours(date(2026, 8, 14))
    winter = parser.opening_hours(date(2026, 1, 14))

    assert (summer[0].opens, summer[0].closes) == ("08:30", "17:00")
    assert (winter[0].opens, winter[0].closes) == ("09:00", "16:00")


def test_opening_hours_falls_back_to_the_first_block_it_cannot_place(caplog):
    """Unplaceable blocks still yield hours, and say so in the log."""

    html = _SEASONAL_PAGE.replace(" (1 oktober t/m 31 maart)", "").replace(
        " (1 april t/m 30 september)", ""
    )

    hours = CureParser(html).opening_hours(date(2026, 8, 14))

    assert (hours[0].opens, hours[0].closes) == ("09:00", "16:00")
    assert "could not tell which one applies today" in caplog.text


def test_parse_returns_cure_data():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    result = parser.parse()

    assert isinstance(result, CureData)

    assert len(result.locations) == 2

    assert result.locations[0].name == "Milieustraat Acht"
    assert result.locations[0].address == "Achtseweg Noord 41 5651 GG Eindhoven"

    assert result.locations[1].name == "Milieustraat Lodewijkstraat"
    assert result.locations[1].address == "Lodewijkstraat 9 5652 AC Eindhoven"


def test_opening_hours():
    html = Path("tests/fixtures/milieustraat_eindhoven.html").read_text(
        encoding="utf-8"
    )

    parser = CureParser(html)

    hours = parser.opening_hours()

    assert len(hours) == 7
    assert hours[0].day is Weekday.MONDAY
    assert hours[-2].day is Weekday.SATURDAY
    assert hours[-1].day is Weekday.HOLIDAY

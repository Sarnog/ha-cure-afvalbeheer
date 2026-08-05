from bs4 import BeautifulSoup

from custom_components.cure_afvalbeheer import selectors

_SINGULAR_ADDRESS_HTML = """
<html>
<body>
<section>
    <h2>Adres Milieustraat Valkenswaard</h2>
    <h3>Milieustraat De Vest</h3>
    <p>De Vest 15 (ingang via De Oase) 5555 XL Valkenswaard</p>
</section>
</body>
</html>
"""


def test_address_section_matches_singular_heading():
    soup = BeautifulSoup(_SINGULAR_ADDRESS_HTML, "html.parser")

    section = selectors.address_section(soup)

    assert section is not None
    assert section.find("h3").get_text(strip=True) == "Milieustraat De Vest"


def test_address_section_returns_none_without_matching_heading():
    soup = BeautifulSoup(
        "<html><body><h2>Openingstijden</h2></body></html>", "html.parser"
    )

    assert selectors.address_section(soup) is None


_NEWS_BLOCK_HTML = """
<html>
<body>
<section data-block="newsBlock">
    <div><h2>Hitteprotocol update! Tot en met donderdag 16 juli</h2></div>
</section>
</body>
</html>
"""


def test_news_heading_returns_heading_text():
    soup = BeautifulSoup(_NEWS_BLOCK_HTML, "html.parser")

    assert (
        selectors.news_heading(soup)
        == "Hitteprotocol update! Tot en met donderdag 16 juli"
    )


def test_news_heading_returns_none_without_block():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")

    assert selectors.news_heading(soup) is None


_MULTIPLE_TEXT_AND_MEDIA_HTML = """
<html>
<body>
<section data-block="textAndMedia">
    <h2>Inpaktips voor vertrek</h2>
    <p>Scheid jouw afval.</p>
</section>
<section data-block="textAndMedia">
    <h2>Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden.</h2>
    <p>Dinsdag 30 juni 2026</p>
</section>
</body>
</html>
"""


def test_closure_notice_section_finds_the_let_op_block():
    soup = BeautifulSoup(_MULTIPLE_TEXT_AND_MEDIA_HTML, "html.parser")

    section = selectors.closure_notice_section(soup)

    assert section is not None
    assert section.find("h2").get_text(strip=True).startswith("Let op!")


def test_closure_notice_section_returns_none_without_active_notice():
    html = """
    <html><body>
    <section data-block="textAndMedia">
        <h2>Inpaktips voor vertrek</h2>
    </section>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    assert selectors.closure_notice_section(soup) is None


def test_closure_notice_section_falls_back_without_data_block_attribute():
    """If Cure drops the data-block attribute, the "Let op!" text still matters."""

    html = """
    <html><body>
    <div class="content-block">
        <h2>Let op! Milieustraat Valkenswaard dicht i.v.m. werkzaamheden.</h2>
        <p>Dinsdag 30 juni 2026</p>
    </div>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    section = selectors.closure_notice_section(soup)

    assert section is not None
    assert section.find("h2").get_text(strip=True).startswith("Let op!")


def test_section_with_heading_matches_case_insensitively():
    html = """
    <html><body>
    <section>
        <h2>openingstijden</h2>
        <p>Ma 08:30 - 17:00</p>
    </section>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    section = selectors.section_with_heading(soup, "Openingstijden")

    assert section is not None
    assert section.find("p").get_text(strip=True) == "Ma 08:30 - 17:00"


_CLOSING_DAYS_HTML = """
<html>
<body>
<section>
<div class="prose">
    <h2>Openingstijden</h2>
    <p>Maandag: 08:30 tot 17:00</p>
    <h2>Sluitingsdagen 2031</h2>
    <p>De milieustraat is gesloten op onderstaande data:</p>
    <ul>
        <li><p>Maandag 6 april 2031 (Pasen)</p></li>
        <li><p>Vrijdag 25 en zaterdag 26 december 2031 (Kerstmis)</p></li>
    </ul>
    <p><strong>Afwijkende openingstijden: geopend tot 16:00 uur.</strong></p>
    <h3>Toegang milieustraat</h3>
    <p>Onze poortmedewerkers zijn opgeleid.</p>
</div>
</section>
<section>
    <h2>Maximale hoeveelheden</h2>
    <p>Maximaal 2 m3 per bezoek.</p>
</section>
</body>
</html>
"""


def test_closing_days_blocks_ignores_the_year_in_the_heading():
    """Cure renames this heading every year, and not always on time."""

    soup = BeautifulSoup(_CLOSING_DAYS_HTML, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert len(blocks) == 1
    assert blocks[0][0] == "Sluitingsdagen 2031"


def test_closing_days_blocks_returns_one_line_per_entry():
    soup = BeautifulSoup(_CLOSING_DAYS_HTML, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert blocks[0][1] == [
        "De milieustraat is gesloten op onderstaande data:",
        "Maandag 6 april 2031 (Pasen)",
        "Vrijdag 25 en zaterdag 26 december 2031 (Kerstmis)",
        "Afwijkende openingstijden: geopend tot 16:00 uur.",
        "Onze poortmedewerkers zijn opgeleid.",
    ]


def test_closing_days_blocks_stops_at_the_next_heading_of_its_own_level():
    soup = BeautifulSoup(_CLOSING_DAYS_HTML, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert "Maximaal 2 m3 per bezoek." not in blocks[0][1]


def test_closing_days_blocks_does_not_pick_up_the_opening_hours_above_it():
    soup = BeautifulSoup(_CLOSING_DAYS_HTML, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert "Maandag: 08:30 tot 17:00" not in blocks[0][1]


def test_closing_days_blocks_reads_two_years_side_by_side():
    """Around the turn of the year the page can carry both lists."""

    html = """
    <html><body>
    <h2>Sluitingsdagen 2031</h2>
    <ul><li>Vrijdag 25 december 2031 (Kerstmis)</li></ul>
    <h2>Sluitingsdagen 2032</h2>
    <ul><li>Donderdag 1 januari 2032 (nieuwjaarsdag)</li></ul>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert [heading for heading, _ in blocks] == [
        "Sluitingsdagen 2031",
        "Sluitingsdagen 2032",
    ]
    assert blocks[0][1] == ["Vrijdag 25 december 2031 (Kerstmis)"]
    assert blocks[1][1] == ["Donderdag 1 januari 2032 (nieuwjaarsdag)"]


def test_closing_days_blocks_falls_back_when_the_heading_is_wrapped():
    """If Cure ever gives the heading a wrapper, it has no content siblings."""

    html = """
    <html><body>
    <div><h2>Sluitingsdagen 2031</h2></div>
    <div><p>Maandag 6 april 2031 (Pasen)</p></div>
    <h2>Maximale hoeveelheden</h2>
    <p>Maximaal 2 m3 per bezoek.</p>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    blocks = selectors.closing_days_blocks(soup)

    assert blocks[0][1] == ["Maandag 6 april 2031 (Pasen)"]


def test_closing_days_blocks_returns_nothing_without_the_heading():
    soup = BeautifulSoup(
        "<html><body><h2>Openingstijden</h2></body></html>", "html.parser"
    )

    assert selectors.closing_days_blocks(soup) == []


def test_section_with_heading_falls_back_to_div_wrapper():
    """If Cure wraps the heading in a <div> instead of <section>, still find it."""

    html = """
    <html><body>
    <div>
        <h2>Openingstijden</h2>
        <p>Ma 08:30 - 17:00</p>
    </div>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    section = selectors.section_with_heading(soup, "Openingstijden")

    assert section is not None
    assert section.find("p").get_text(strip=True) == "Ma 08:30 - 17:00"

import pytest
from bs4 import BeautifulSoup

from custom_components.cure_afvalbeheer.parsing import selectors


def _lines(blocks: list[tuple[str, list[str]]]) -> list[str]:
    """Return the lines of the first block, or none at all."""

    return blocks[0][1] if blocks else []


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


_NEWS_ITEMS_HTML = """
<html>
<body>
<section data-block="newsBlock">
    <div><h2>Let op! Hitteprotocol van 13 t/m 15 Augustus!</h2></div>
    <ul>
        <li>
            <date>13 aug 2026</date>
            <p>Hitteprotocol! 13 tot en met 15 Augustus</p>
            <a href="/nieuws/hitteprotocol/"><span class="sr-only">
            Hitteprotocol! 13 tot en met 15 Augustus</span></a>
        </li>
        <li>
            <date>20 jul 2026</date>
            <p>Problemen notificaties Cure afval app verhelpen</p>
        </li>
    </ul>
</section>
</body>
</html>
"""


def test_news_item_texts_returns_one_line_per_item():
    """The title is repeated for screen readers; only one copy is wanted."""

    soup = BeautifulSoup(_NEWS_ITEMS_HTML, "html.parser")

    assert selectors.news_item_texts(soup) == [
        "Hitteprotocol! 13 tot en met 15 Augustus",
        "Problemen notificaties Cure afval app verhelpen",
    ]


def test_news_item_texts_returns_empty_without_block():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")

    assert selectors.news_item_texts(soup) == []


def test_closure_notice_section_skips_the_news_block():
    """The site-wide banner opens with "Let op!" too, but announces
    adjusted hours rather than a closure."""

    soup = BeautifulSoup(_NEWS_ITEMS_HTML, "html.parser")

    assert selectors.closure_notice_section(soup) is None


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


def test_blocks_under_heading_matches_case_insensitively():
    html = """
    <html><body>
    <section>
        <h2>openingstijden</h2>
        <p>Ma 08:30 - 17:00</p>
    </section>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Ma 08:30 - 17:00"
    ]


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


def test_blocks_under_heading_works_without_a_section_wrapper():
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

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Ma 08:30 - 17:00"
    ]


def test_blocks_under_heading_stops_at_the_next_heading():
    """The opening hours and the closing days share one container."""

    html = """
    <html><body>
    <div>
        <h2>Openingstijden</h2>
        <p>Maandag: 08:30 tot 17:00</p>
        <h2>Sluitingsdagen 2026</h2>
        <p>Zaterdag 26 december 2026: 10:00 tot 14:00</p>
    </div>
    </body></html>
    """

    soup = BeautifulSoup(html, "html.parser")

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Maandag: 08:30 tot 17:00"
    ]


def test_blocks_under_heading_returns_empty_without_the_heading():
    soup = BeautifulSoup("<html><body><p>Niets</p></body></html>", "html.parser")

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == []


# --- Layouts and spellings Cure has not used yet, but readily could ---


_TABLE_HOURS_HTML = """
<html><body>
<section>
    <h2>Openingstijden milieustraat</h2>
    <table>
        <tr><td>Maandag</td><td>08:30 - 17:00</td></tr>
        <tr><td><p>Zaterdag</p></td><td><p>10:00 - 16:00</p></td></tr>
    </table>
    <ul>
        <li>Zon &amp; Feestdagen: Gesloten</li>
    </ul>
</section>
</body></html>
"""


def test_blocks_under_heading_reads_rows_and_list_items_too():
    """Cure can move these lines into a table or a list without rewording."""

    soup = BeautifulSoup(_TABLE_HOURS_HTML, "html.parser")

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Maandag 08:30 - 17:00",
        "Zaterdag 10:00 - 16:00",
        "Zon & Feestdagen: Gesloten",
    ]


def test_blocks_under_heading_accepts_added_words():
    soup = BeautifulSoup(_TABLE_HOURS_HTML, "html.parser")

    blocks = selectors.blocks_under_heading(soup, "Openingstijden")

    assert [heading for heading, _ in blocks] == ["Openingstijden milieustraat"]


def test_blocks_under_heading_prefers_the_exact_heading():
    """A near-match higher up the page must not beat the real heading."""

    html = """
    <html><body>
    <section><h2>Afwijkende openingstijden</h2><p>Op 24 december</p></section>
    <section><h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p></section>
    </body></html>
    """

    blocks = selectors.blocks_under_heading(
        BeautifulSoup(html, "html.parser"), "Openingstijden"
    )

    assert [heading for heading, _ in blocks] == ["Openingstijden"]
    assert _lines(blocks) == ["Maandag: 08:30 tot 17:00"]


def test_blocks_under_heading_returns_every_block_of_its_kind():
    """Summer and winter hours side by side are two blocks, not one."""

    html = """
    <html><body>
    <h2>Openingstijden winter (1 oktober t/m 31 maart)</h2>
    <p>Maandag: 09:00 tot 16:00</p>
    <h2>Openingstijden zomer (1 april t/m 30 september)</h2>
    <p>Maandag: 08:30 tot 17:00</p>
    </body></html>
    """

    blocks = selectors.blocks_under_heading(
        BeautifulSoup(html, "html.parser"), "Openingstijden"
    )

    assert len(blocks) == 2
    assert blocks[0][1] == ["Maandag: 09:00 tot 16:00"]
    assert blocks[1][1] == ["Maandag: 08:30 tot 17:00"]


@pytest.mark.parametrize(
    "heading",
    [
        "Adres Milieustraat Valkenswaard",
        "Adres Milieustraten Eindhoven",
        "adres milieustraat valkenswaard",
        "Adressen milieustraten Eindhoven",
        "Locatie Milieustraat Valkenswaard",
    ],
)
def test_address_section_however_the_heading_is_written(heading):
    soup = BeautifulSoup(
        f"<html><body><section><h2>{heading}</h2>"
        "<p>De Vest 15 5555 XL Valkenswaard</p></section></body></html>",
        "html.parser",
    )

    assert selectors.address_section(soup) is not None


def test_address_section_ignores_an_unrelated_milieustraat_heading():
    soup = BeautifulSoup(
        "<html><body><section><h2>Plattegrond Milieustraat Acht</h2>"
        "<p>Zie de kaart</p></section></body></html>",
        "html.parser",
    )

    assert selectors.address_section(soup) is None


@pytest.mark.parametrize(
    "heading",
    [
        "Sluitingsdagen 2026",
        "Sluitingsdata 2026",
        "sluitingsdagen",
        "Gesloten dagen 2026",
        "Feestdagen 2026",
    ],
)
def test_closing_days_blocks_however_the_heading_is_written(heading):
    soup = BeautifulSoup(
        f"<html><body><div><h2>{heading}</h2>"
        "<p>Maandag 6 april 2026 (Pasen)</p></div></body></html>",
        "html.parser",
    )

    blocks = selectors.closing_days_blocks(soup)

    assert blocks
    assert blocks[0][1] == ["Maandag 6 april 2026 (Pasen)"]


@pytest.mark.parametrize(
    "heading",
    [
        "Let op! Milieustraat dicht",
        "Let op: Milieustraat dicht",
        "LET OP! Milieustraat dicht",
        "Let op, milieustraat dicht",
    ],
)
def test_closure_notice_section_however_the_heading_is_punctuated(heading):
    soup = BeautifulSoup(
        f'<html><body><section data-block="textAndMedia"><h2>{heading}</h2>'
        "<p>Dinsdag 30 juni 2026</p></section></body></html>",
        "html.parser",
    )

    assert selectors.closure_notice_section(soup) is not None


# --- Grenzen, gevonden met mutatietests (mutmut) ---------------------------


def _soup(html: str) -> BeautifulSoup:
    """Parse a snippet the way the integration parses a page."""

    return BeautifulSoup(html, "html.parser")


_NEWS_BLOCK = (
    '<div data-block="newsBlock"><h2>Let op! Gewijzigde openingstijden</h2>'
    "<ul><li><p>Hitteprotocol vandaag</p></li></ul></div>"
)


def test_blocks_under_heading_leaves_a_starting_heading_out_by_default():
    soup = _soup(
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        "<h2>Openingstijden vanaf 1 december</h2><p>Maandag: 10:00 tot 17:00</p>"
    )

    assert [h for h, _ in selectors.blocks_under_heading(soup, "Openingstijden")] == [
        "Openingstijden"
    ]
    assert (
        len(selectors.blocks_under_heading(soup, "Openingstijden", starting_too=True))
        == 2
    )


def test_blocks_under_heading_skips_the_news_block():
    soup = _soup(
        '<div data-block="newsBlock"><h2>Openingstijden</h2><p>nieuws</p></div>'
        "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
    )

    assert selectors.blocks_under_heading(soup, "Openingstijden") == [
        ("Openingstijden", ["Maandag: 08:30 tot 17:00"])
    ]


def test_blocks_under_heading_falls_back_to_a_heading_containing_the_text():
    soup = _soup(
        "<h2>Nieuws</h2><p>iets</p>"
        "<h2>Afwijkende openingstijden</h2><p>Maandag: 10:00 tot 12:00</p>"
    )

    assert selectors.blocks_under_heading(soup, "Openingstijden") == [
        ("Afwijkende openingstijden", ["Maandag: 10:00 tot 12:00"])
    ]


def test_blocks_under_heading_reads_a_list_item_once():
    soup = _soup(
        "<h2>Openingstijden</h2><ul><li><p>Maandag: 08:30 tot 17:00</p></li></ul>"
    )

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Maandag: 08:30 tot 17:00"
    ]


def test_blocks_under_heading_reads_past_a_wrapped_heading():
    """A heading in a wrapper of its own has no content siblings."""

    soup = _soup(
        "<div><h2>Openingstijden</h2></div>"
        "<p>Maandag: 08:30 tot 17:00</p><h2>Adres</h2><p>Straat 1</p>"
    )

    assert _lines(selectors.blocks_under_heading(soup, "Openingstijden")) == [
        "Maandag: 08:30 tot 17:00"
    ]


def test_location_name_is_stripped():
    assert selectors.location_name(_soup("<h1> Milieustraat Acht </h1>")) == (
        "Milieustraat Acht"
    )
    assert selectors.location_name(_soup("<p>geen kop</p>")) == ""


def test_news_item_texts_only_reads_the_news_block():
    soup = _soup(
        "<ul><li><p>Menu-item</p></li></ul>"
        '<div data-block="newsBlock"><h2>Nieuws</h2><ul>'
        "<li><span>zonder titel</span></li><li><p>Hitteprotocol</p></li>"
        "</ul></div>"
    )

    assert selectors.news_item_texts(soup) == ["Hitteprotocol"]


def test_closure_notice_section_prefers_the_tagged_block():
    soup = _soup(
        '<section data-block="textAndMedia"><p>intro</p>'
        "<div><h2>Let op! Sluiting</h2></div></section>"
    )

    assert selectors.closure_notice_section(soup).name == "section"


def test_closure_notice_section_looks_past_a_block_without_heading():
    soup = _soup(
        '<section data-block="textAndMedia"><p>Inpaktips</p></section>'
        '<section data-block="textAndMedia" id="let-op">'
        "<div><h2>Let op! Sluiting</h2></div></section>"
    )

    assert selectors.closure_notice_section(soup).get("id") == "let-op"


def test_closure_notice_section_fallback_skips_other_headings_and_news():
    soup = _soup(
        _NEWS_BLOCK
        + "<section><h2>Inpaktips</h2></section>"
        + '<section id="let-op"><header><h2>Let op! Sluiting</h2></header></section>'
    )

    assert selectors.closure_notice_section(soup).get("id") == "let-op"


@pytest.mark.parametrize("container", ["section", "div", "article"])
def test_closure_notice_section_fallback_returns_the_container(container):
    soup = _soup(
        f'<{container} id="let-op"><header><h2>Let op! Sluiting</h2></header>'
        f"</{container}>"
    )

    assert selectors.closure_notice_section(soup).get("id") == "let-op"


def test_plain_text_joins_and_trims_every_piece():
    heading = _soup("<h2> Let\xa0<b>op!</b> <span>Sluiting </span></h2>").h2

    assert selectors._plain_text(heading) == "Let op! Sluiting"


def test_lines_of_skips_comments():
    paragraph = _soup("<p>Maandag<!-- verborgen --> 10:00 - 12:00</p>").p

    assert selectors._lines_of(paragraph) == ["Maandag 10:00 - 12:00"]


def test_announcement_blocks_skip_regular_hours_and_news():
    soup = _soup(
        _NEWS_BLOCK
        + "<h2>Openingstijden</h2><p>Maandag: 08:30 tot 17:00</p>"
        + "<h2>Adres</h2><p>Straat 1</p>"
        + "<h2>Vanaf 1 december geopend van 10:00 tot 17:00</h2><p>Alle dagen</p>"
    )

    assert selectors.announcement_blocks(soup) == [
        ("Vanaf 1 december geopend van 10:00 tot 17:00", ["Alle dagen"])
    ]


def test_blocks_with_heading_skips_news_footer_and_empty_headings():
    soup = _soup(
        _NEWS_BLOCK
        + '<div data-block="footerContent"><h3>Contact</h3></div>'
        + "<footer><h3>Links</h3></footer>"
        + "<h2> </h2>"
        + "<h2>Let op!</h2><p>Gesloten op 1 mei</p>"
    )

    assert selectors.blocks_with_heading(soup) == [("Let op!", ["Gesloten op 1 mei"])]


def test_plain_text_replaces_an_inner_non_breaking_space():
    assert selectors._plain_text(_soup("<h2>Let\xa0op!</h2>").h2) == "Let op!"


def test_lines_of_joins_the_pieces_of_one_line_with_spaces():
    paragraph = _soup("<p>Maandag<b>10:00</b>-12:00<br>Dinsdag</p>").p

    assert selectors._lines_of(paragraph) == ["Maandag 10:00 -12:00", "Dinsdag"]

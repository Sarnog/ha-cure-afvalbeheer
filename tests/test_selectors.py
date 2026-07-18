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

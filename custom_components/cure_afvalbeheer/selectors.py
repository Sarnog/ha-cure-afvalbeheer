"""Selectors voor Cure HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag


def page_title(soup: BeautifulSoup) -> str:
    """Return de paginatitel."""

    if soup.title:
        return soup.title.get_text(strip=True)

    return ""


def headings(soup: BeautifulSoup) -> list[Tag]:
    """Return alle headings."""

    return soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
        ]
    )


def main_content(soup: BeautifulSoup) -> Tag | None:
    """Return the main page content."""

    return soup.find("main")


def all_headings(soup: BeautifulSoup) -> list[str]:
    """Return all heading text."""

    result: list[str] = []

    for heading in headings(soup):
        text = heading.get_text(" ", strip=True)

        if text:
            result.append(text)

    return result


def section_with_heading(
    soup: BeautifulSoup,
    heading: str,
) -> Tag | None:
    """Return the section that contains the given heading."""

    for h2 in soup.find_all("h2"):
        text = h2.get_text(" ", strip=True)

        if text == heading:
            return h2.find_parent("section")

    return None


def paragraphs(section: Tag) -> list[str]:
    """Return all paragraph text."""

    result: list[str] = []

    for paragraph in section.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        if text:
            result.append(text)

    return result


def location_name(soup: BeautifulSoup) -> str:
    """Return the location name."""

    heading = soup.find("h1")

    if heading is None:
        return ""

    return heading.get_text(strip=True)


def address_section(soup) -> Tag | None:
    """Return the section containing the recycling centre addresses."""

    heading = soup.find("h2", string="Adres Milieustraten Eindhoven")

    if heading is None:
        return None

    return heading.parent

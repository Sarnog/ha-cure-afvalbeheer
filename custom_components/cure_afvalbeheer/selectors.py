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


def all_tables(soup: BeautifulSoup) -> list[Tag]:
    """Return all tables."""

    return soup.find_all("table")


def all_headings(soup: BeautifulSoup) -> list[str]:
    """Return all heading text."""

    result: list[str] = []

    for heading in headings(soup):
        text = heading.get_text(" ", strip=True)

        if text:
            result.append(text)

    return result


def first_table(soup: BeautifulSoup) -> Tag | None:
    """Return the first table on the page."""

    tables = all_tables(soup)

    if not tables:
        return None

    return tables[0]

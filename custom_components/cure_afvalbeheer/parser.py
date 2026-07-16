"""Parser voor Cure Afvalbeheer."""

from __future__ import annotations

from bs4 import BeautifulSoup

from .logger import LOGGER


class CureParser:
    """Parser voor Cure HTML-pagina's."""

    def __init__(self, html: str) -> None:
        """Initialiseer de parser."""

        LOGGER.debug("Initialising Cure HTML parser")

        self._soup = BeautifulSoup(html, "html.parser")

    def page_title(self) -> str:
        """Return the page title."""

        title = ""
        
        if self._soup.title:
            title = self._soup.title.get_text(strip=True)
        
        LOGGER.debug("Page title: %s", title)
        
        return title

    def parse(self) -> list:
        """Dummy parser."""

        return []
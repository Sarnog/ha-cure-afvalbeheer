"""Custom exceptions for Cure Afvalbeheer."""


class ParserError(Exception):
    """Raised when the Cure HTML cannot be parsed."""


class CureApiError(Exception):
    """Error communicating with the Cure website."""

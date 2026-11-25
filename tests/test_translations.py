"""Guard the translation files against drifting apart."""

import json
from pathlib import Path

_COMPONENT = Path("custom_components/cure_afvalbeheer")


def _load(name: str) -> dict:
    """Read one translation file."""

    return json.loads((_COMPONENT / name).read_text(encoding="utf-8"))


def _keys(data: dict, prefix: str = "") -> set[str]:
    """Return every key path in a nested translation dict."""

    result: set[str] = set()

    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        result.add(path)

        if isinstance(value, dict):
            result |= _keys(value, path)

    return result


def test_strings_match_the_dutch_translation():
    """strings.json is the Dutch source text, so nl.json must equal it."""

    assert _load("strings.json") == _load("translations/nl.json")


def test_english_translation_has_the_same_keys():
    """A key missing in en.json shows up as a raw key in the English UI."""

    assert _keys(_load("translations/en.json")) == _keys(_load("strings.json"))

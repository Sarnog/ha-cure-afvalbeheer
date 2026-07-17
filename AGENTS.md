🇳🇱 [Nederlands](#ai-ontwikkelinstructies) | 🇬🇧 [English](#ai-development-instructions)

---

# AI-ontwikkelinstructies

Dit project volgt de Home Assistant-ontwikkelrichtlijnen.

## Algemene regels

Gebruik altijd:

- Python type hints
- Ruff-compatibele code
- Google-stijl docstrings
- logging

Gebruik nooit:

- print()
- requests
- blokkerende I/O

---

## Home Assistant

Gebruik:

- ConfigEntry
- Config Flow
- DataUpdateCoordinator
- SensorEntity
- DeviceInfo

Gebruik geen verouderde Home Assistant-API's.

Gebruik Home Assistant-acties (geïntroduceerd in HA 2024.8) in plaats van
legacy service calls voor nieuwe functionaliteit.

---

## Parser

Gebruik BeautifulSoup voor HTML-parsing.

HTML-selectors moeten geïmplementeerd worden in `selectors.py`.

`parser.py` mag geen CSS-selectors of HTML-traversal-logica bevatten.

---

## Models

Gebruik alleen:

```python
@dataclass(slots=True)
```

Models bevatten alleen data.

Geen parslogica.

Geen Home Assistant-imports.

---

## Codestijl

- Maximale regellengte: 88 tekens
- Dubbele aanhalingstekens
- Ruff-compliant
- Imports gesorteerd door Ruff

---

## Logging

Gebruik altijd:

```python
LOGGER.debug(...)
LOGGER.info(...)
LOGGER.warning(...)
LOGGER.error(...)
```

Gebruik nooit `print()`.

---

## Async

Alle netwerkcommunicatie moet asynchroon zijn.

Gebruik `aiohttp`.

Gebruik nooit `requests`.

---

## Testen

Elke nieuwe feature moet minstens één pytest-test bevatten.

Tests mogen nooit afhankelijk zijn van live internettoegang.

Gebruik fixtures waar mogelijk.

---

## Git-workflow

Voor elke feature:

1. Ontwerp
2. Implementatie
3. Test
4. Commit

Elke commit moet de repository in een werkende staat achterlaten.

---

## Architectuur

Het project volgt deze architectuur:

Internet
↓
HTTP-client
↓
Selectors
↓
Parser
↓
Models
↓
Coordinator
↓
Entiteiten

Elke laag heeft één verantwoordelijkheid.

---

## Doel

Bouw een hoogwaardige Home Assistant custom-integratie die geschikt is voor
publicatie via HACS en de Home Assistant Integration Quality Scale volgt.

---

# AI Development Instructions

This project follows the Home Assistant Development Guidelines.

## General Rules

Always use:

- Python type hints
- Ruff compatible code
- Google-style docstrings
- logging

Never use:

- print()
- requests
- blocking I/O

---

## Home Assistant

Use:

- ConfigEntry
- Config Flow
- DataUpdateCoordinator
- SensorEntity
- DeviceInfo

Do not use deprecated Home Assistant APIs.

Use Home Assistant actions (introduced in HA 2024.8) instead of legacy service calls for new functionality.

---

## Parser

Use BeautifulSoup for HTML parsing.

HTML selectors must be implemented in `selectors.py`.

`parser.py` must not contain CSS selectors or HTML traversal logic.

---

## Models

Use only:

```python
@dataclass(slots=True)
```

Models contain data only.

No parsing logic.

No Home Assistant imports.

---

## Code Style

- Maximum line length: 88 characters
- Double quotes
- Ruff compliant
- Imports sorted by Ruff

---

## Logging

Always use:

```python
LOGGER.debug(...)
LOGGER.info(...)
LOGGER.warning(...)
LOGGER.error(...)
```

Never use `print()`.

---

## Async

All network communication must be asynchronous.

Use `aiohttp`.

Never use `requests`.

---

## Testing

Every new feature should include at least one pytest test.

Tests must never depend on live internet access.

Use fixtures whenever possible.

---

## Git Workflow

For every feature:

1. Design
2. Implementation
3. Test
4. Commit

Each commit should leave the repository in a working state.

---

## Architecture

The project follows this architecture:

Internet
↓
HTTP Client
↓
Selectors
↓
Parser
↓
Models
↓
Coordinator
↓
Entities

Each layer has a single responsibility.

---

## Goal

Create a high-quality Home Assistant custom integration that is suitable for publication via HACS and follows the Home Assistant Integration Quality Scale.

# Cure Afvalbeheer voor Home Assistant

Een custom Home Assistant integratie voor Cure Afvalbeheer.

## Doel

Deze integratie toont de actuele openingstijden van alle milieustraten in Eindhoven.

Daarnaast worden tijdelijke wijzigingen automatisch verwerkt, zoals:

- aangepaste openingstijden vanwege hitte
- tijdelijke sluitingen
- verbouwingen
- overige mededelingen

Alle informatie wordt rechtstreeks opgehaald vanaf de officiële Cure-website.

## Features

### Versie 1.0

- Config Flow
- DataUpdateCoordinator
- Openingstijden van alle Eindhovense milieustraten
- Actuele status (Open / Gesloten)
- Volgende wijziging
- Device in Home Assistant

### Versie 1.1

- RSS nieuws
- Tijdelijke sluitingen
- Hitteprotocol
- Attributen voor dashboards

### Versie 1.2

- Kalender met komende dagen
- Markdown-vriendelijke attributen
- Handmatige refresh action

## Installatie

Via HACS:

1. Voeg deze repository toe als Custom Repository.
2. Installeer de integratie.
3. Herstart Home Assistant.
4. Voeg de integratie toe via Apparaten & Diensten.

## Ondersteunde locaties

- Acht
- Lodewijkstraat
- Achtseweg Noord (indien toegevoegd)
- Nieuwe locaties worden automatisch ontdekt.

## Architectuur

Zie:

- ARCHITECTURE.md
- AGENTS.md

## Ontwikkeling

Gebruik:

- Python 3.13
- Ruff
- pytest
- Home Assistant development guidelines

## Licentie

MIT
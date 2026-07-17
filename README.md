# Cure Afvalbeheer voor Home Assistant

Een custom Home Assistant integratie voor Cure Afvalbeheer.

## Doel

Deze integratie toont de actuele openingstijden van de milieustraten van een
Cure-gemeente naar keuze (Eindhoven, Valkenswaard of Geldrop-Mierlo).

Daarnaast worden tijdelijke afwijkingen van de reguliere openingstijden verwerkt,
zoals:

- aangepaste openingstijden vanwege het hitteprotocol
- tijdelijke sluitingen (bijvoorbeeld wegens werkzaamheden)
- verbouwingen

Alle informatie wordt rechtstreeks opgehaald vanaf de officiële Cure-website —
er is geen los RSS-abonnement nodig.

## Features

### v0.1.0

- Config Flow: kies een Cure-gemeente; voeg dezelfde of een andere gemeente
  desgewenst nogmaals toe voor meerdere devices.
- Options Flow: aantal vooruitkijkdagen instelbaar (standaard 5), ook na
  installatie te wijzigen.
- DataUpdateCoordinator haalt live de milieustraat-pagina van de gekozen
  gemeente op.
- Eén sensor per milieustraat: actuele status (Open/Gesloten) en `today`/
  `upcoming`-attributen voor gebruik in een markdown-kaart.
- Home Assistant brand-assets voorbereid (zie `brands/`).

### v0.2.0

- Tijdelijke afwijkingen (hitteprotocol, verbouwing, sluiting) worden uit de
  pagina zelf geparst en passen de sensor-status/attributen automatisch aan,
  inclusief een `reason`-attribuut dat aangeeft waarom er wordt afgeweken van
  het reguliere rooster.

Zie ROADMAP.md voor wat er nog gepland staat.

## Installatie

Via HACS:

1. Voeg deze repository toe als Custom Repository.
2. Installeer de integratie.
3. Herstart Home Assistant.
4. Voeg de integratie toe via Apparaten & Diensten en kies een gemeente.

## Ondersteunde gemeentes

- Eindhoven
- Valkenswaard
- Geldrop-Mierlo

Milieustraat-locaties binnen een gemeente worden automatisch ontdekt uit de
pagina; er is geen aparte configuratie per locatie nodig.

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

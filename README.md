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
  pagina zelf geparst en passen de sensor-status/attributen automatisch aan.

### v0.3.0

- Twee losse "reden"-sensoren per milieustraat (vandaag/morgen) in plaats van
  een verstopt attribuut, zodat je automatiseringen al één dag vooruit kunt
  laten waarschuwen voor een afwijking.
- Nieuwe milieustraten die Cure aan een gemeentepagina toevoegt verschijnen
  automatisch, zonder herstart. Verdwijnt een milieustraat permanent, dan
  worden de bijbehorende sensoren `unavailable`; blijft die na een herstart
  nog steeds weg, dan biedt Home Assistant zelf een verwijderoptie aan.

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

## Gebruik in het dashboard

Elke milieustraat krijgt drie sensoren:

- **`sensor.<device>_<milieustraat>`** — status `open`/`closed`, met `today`
  en `upcoming` (de ingestelde vooruitkijkdagen) als attributen.
- **`sensor.<device>_<milieustraat>_reden_vandaag`** en
  **`..._reden_morgen`** — leeg (`""`) als er geen afwijking is, anders de
  reden (`hitteprotocol`, `verbouwing`, `werkzaamheden`).

Zoek je eigen entity-ID's op via **Ontwikkelaarshulpmiddelen → Staten** — de
onderstaande voorbeelden gebruiken die van "Milieustraat Acht" in Eindhoven
(`sensor.cure_afvalbeheer_eindhoven_milieustraat_acht`) ter illustratie.

### Voorbeeld: markdown-kaart

```yaml
type: markdown
content: >
  {% set sensor = 'sensor.cure_afvalbeheer_eindhoven_milieustraat_acht' %}
  {% set vandaag = state_attr(sensor, 'today') %}
  {% set upcoming = state_attr(sensor, 'upcoming') %}
  {% set afwijkingen = upcoming | selectattr('reason') | list %}

  <h2 style="text-align: center;">Milieustraat Acht</h2>

  **Vandaag:** {% if vandaag.closed %}Gesloten{% else %}Geopend tot {{ vandaag.closes }}{% endif %}

  {% if afwijkingen %}
  <ha-icon icon="mdi:alert" style="color: darkorange;"></ha-icon> **Afwijkingen voor de komende dagen:**
  {% else %}
  **Openingstijden de komende dagen:**
  {% endif %}

  {% for dag in upcoming %}
  - {{ dag.date }}: {% if dag.closed %}Gesloten{% else %}Open van {{ dag.opens }} tot {{ dag.closes }}{% endif %}{% if dag.reason %} — {{ dag.reason }}{% endif %}
  {% endfor %}
```

De kop staat gecentreerd (zelfde stijl als een `##`-kop, alleen via `<h2>` zodat
`text-align` werkt binnen de markdown-kaart). De tweede kop wisselt
automatisch tussen "Afwijkingen voor de komende dagen" (met een
waarschuwingsdriehoek, `mdi:alert`, in donkeroranje) en "Openingstijden de
komende dagen" — afhankelijk van of er in de ingestelde vooruitkijkperiode een
`reason` voorkomt. De lijst daaronder toont per dag de tijden, met de reden
erachter zodra die dag afwijkt.

### Voorbeeld: automatisering (waarschuw al één dag vooraf)

Dit is precies waarom er een aparte "reden morgen"-sensor bestaat: de
melding komt binnen zodra Cure de wijziging aankondigt, niet pas op de dag
zelf.

```yaml
automation:
  - alias: "Cure: waarschuwing voor afwijking morgen"
    trigger:
      - trigger: state
        entity_id: sensor.cure_afvalbeheer_eindhoven_milieustraat_acht_reden_morgen
    condition:
      - condition: template
        value_template: >
          {{ trigger.from_state.state == '' and trigger.to_state.state != '' }}
    action:
      - action: notify.notify
        data:
          title: "Milieustraat Acht"
          message: >
            Morgen wijkt de milieustraat af van de normale openingstijden:
            {{ trigger.to_state.state }}.
```

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

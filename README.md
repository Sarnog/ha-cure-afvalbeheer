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

Vereist de HACS-frontendkaart **[card-mod](https://github.com/thomasloven/lovelace-card-mod)**
— HA's markdown-kaart filtert het `style`-attribuut uit HTML (sanitizer), dus
de opmaak (kop centreren, icoon-kleur/animatie) wordt hier via `card_mod`
toegepast in plaats van inline.

Pas **twee plekken** aan naar je eigen situatie:
1. De entity-ID op de regel `{%- set sensor = ... -%}` — vervang
   `<sensor.milieustraat_naam>` door je eigen sensor (op te zoeken via
   Ontwikkelaarshulpmiddelen → Staten).
2. De tekst tussen `<h2>` en `</h2>` — vervang "Milieustraat Naam" door de
   naam die je op de kaart wilt zien staan.

```yaml
type: markdown
content: |
  {#- Bronsensor en attributen ophalen -#}
  {%- set sensor = '<sensor.milieustraat_naam>' -%}
  {%- set vandaag = state_attr(sensor, 'today') -%}
  {%- set upcoming = state_attr(sensor, 'upcoming') or [] -%}
  {#- Alleen dagen met een 'reason' gelden als afwijking -#}
  {%- set afwijkingen = upcoming | selectattr('reason') | list -%}
  {#- Zijn er afwijkingen? Toon die. Zo niet: toon alle komende dagen -#}
  {%- set lijst = afwijkingen if afwijkingen else upcoming -%}
  <h2>Milieustraat Naam</h2>

  **Vandaag:** {% if vandaag is none %}Onbekend{% elif vandaag.closed %}Gesloten{% else %}Geopend tot {{ vandaag.closes }}{% endif %}

  {% if afwijkingen %}<ha-icon icon="mdi:alert-outline"></ha-icon> **Afwijkingen voor de komende dagen:**{% else %}**Openingstijden de komende dagen:**{% endif %}
  {% for dag in lijst %}
  - {{ dag.date }}: {% if dag.closed %}Gesloten{% else %}Open van {{ dag.opens }} tot {{ dag.closes }}{% endif %}{% if dag.reason %} — {{ dag.reason }}{% endif %}
  {%- endfor %}
card_mod:
  style:
    ha-markdown $: |
      /* Kop centreren (style-attribuut werkt niet, sanitizer stript het) */
      ha-markdown-element h2 {
        text-align: center;
      }
      /* Waarschuwingsicoon: donkeroranje + knipperen */
      ha-markdown-element ha-icon {
        color: darkorange;
        --mdc-icon-size: 20px;
        vertical-align: text-bottom;   /* icoon netjes op de tekstregel */
        animation: knipper-alert 1.5s ease-in-out infinite;
      }
      @keyframes knipper-alert {
        50% { opacity: 0.25; }
      }
```

De kop staat gecentreerd via `card_mod`. De tweede kop wisselt automatisch
tussen "Afwijkingen voor de komende dagen" (met een knipperend, donkeroranje
waarschuwingsicoon, `mdi:alert-outline`) en "Openingstijden de komende dagen"
— afhankelijk van of er in de ingestelde vooruitkijkperiode een `reason`
voorkomt. Zijn er afwijkingen, dan toont de lijst daaronder alleen de dagen
mét een afwijking (inclusief de reden); zijn er geen afwijkingen, dan toont de
lijst gewoon alle komende dagen met hun openingstijden.

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

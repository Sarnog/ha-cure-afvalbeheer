🇳🇱 [Nederlands](#routekaart) | 🇬🇧 [English](#roadmap)

---

# Routekaart

Dit bestand is de ideeënbus van deze integratie: toekomstige aanpassingen,
verbeteringen en uitbreidingen die nog **niet** gebouwd zijn, geordend als
*should have* (waarschijnlijk waardevol), *could have* (leuk, situationeel) en
*would have* (later, apart traject). Nog niet alles is besproken of goedgekeurd
— het is een verzamelplek om uit te kiezen, te prioriteren of af te wijzen.

De geschiedenis van wat er al gebouwd en gewijzigd is, staat **niet** hier maar
in de [release notes](https://github.com/Sarnog/ha-cure-afvalbeheer/releases)
van elke versie.

## Should have

- **Opname in de HACS-standaardlijst** — PR
  [hacs/default#9336](https://github.com/hacs/default/pull/9336) staat in de
  reviewwachtrij, zodat de integratie in HACS vindbaar wordt zonder handmatige
  "custom repository"-toevoeging.

## Could have

- **Langetermijnstatistieken** — hoe vaak en hoe lang een milieustraat de
  afgelopen periode gesloten was, via Home Assistants recorder/statistics.
- **Reparatiegeschiedenis** — een overzicht van eerdere parser-storingen in
  plaats van alleen de actuele reparatie-melding.
- **Diagnostics-download automatiseren** — een actie of script om de
  diagnostics-dump op te halen zonder de handmatige UI-stap.
- **Kalender-stijl output, een handmatige refresh-actie en meerdere talen** —
  losse ideeën; nog geen concrete aanpak voor gekozen.

## Would have (later, apart traject)

- **Landelijke uitbreiding** — de integratie op termijn herdopen (en mogelijk
  het logo wijzigen) naar een naam die niet aan Cure gebonden is, om
  milieustraten van álle Nederlandse gemeentes te ondersteunen, niet alleen de
  gemeentes die Cure bedient. Een groot traject: andere afvalbeheerders
  gebruiken andere website-structuren (dus aparte parser-/selector-
  implementaties per bron, met dezelfde laagverdeling als nu), de
  domeinwijziging (`cure_afvalbeheer` → iets generieks) is een breaking change
  die een migratiepad nodig heeft, en er komt een nieuw merk/logo bij. Pas te
  overwegen zodra de huidige Cure-ondersteuning stabiel en volledig is.

---

# Roadmap

This file is the ideas box for this integration: future changes, improvements
and additions that have **not** been built yet, grouped as *should have*
(likely valuable), *could have* (nice, situational) and *would have* (later,
separate effort). Not everything here has been discussed or approved — it's a
place to pick from, prioritize or reject.

The history of what has already been built and changed is **not** here but in
the [release notes](https://github.com/Sarnog/ha-cure-afvalbeheer/releases) of
each version.

## Should have

- **Inclusion in the HACS default store** — PR
  [hacs/default#9336](https://github.com/hacs/default/pull/9336) is in the
  review queue, so the integration becomes discoverable in HACS without a
  manual "custom repository" add.

## Could have

- **Long-term statistics** — how often and how long a recycling centre was
  closed over a given period, via Home Assistant's recorder/statistics.
- **Repairs history** — an overview of earlier parser failures instead of just
  the current repair notification.
- **Automated diagnostics download** — an action or script to fetch the
  diagnostics dump without the manual UI step.
- **Calendar-style output, a manual refresh action and additional languages** —
  loose ideas; no concrete approach chosen yet.

## Would have (later, separate effort)

- **Nationwide expansion** — eventually rename the integration (and possibly
  its logo) to something not tied to Cure, to support recycling centres for
  every Dutch municipality, not just the ones Cure serves. A big undertaking:
  other waste-management providers use different website structures (so
  separate parser/selector implementations per source, with the same layering
  as today), the domain rename (`cure_afvalbeheer` → something generic) is a
  breaking change that needs a migration path, and it brings a new brand/logo.
  Only worth considering once the current Cure support is stable and complete.

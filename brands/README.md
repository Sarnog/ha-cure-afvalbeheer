# Brand-assets voor Home Assistant

Home Assistant haalt het merklogo dat je ziet bij **Instellingen → Apparaten &
Diensten** niet uit deze integratie zelf, maar uit de aparte, centrale repository
[home-assistant/brands](https://github.com/home-assistant/brands). Dat logo
verschijnt pas nadat een pull request daar is geaccepteerd door de HA-maintainers.

## Wat hier klaarstaat

`custom_integrations/cure_afvalbeheer/` bevat de assets in exact de structuur en
naamgeving die die repository verwacht, gegenereerd uit het officiële Cure-logo
(`https://www.cure-afvalbeheer.nl/Assets/Cure%20Logo.svg`):

- `icon.png` (256×256)
- `icon@2x.png` (512×512)
- `logo.png` (256×256)
- `logo@2x.png` (512×512)
- `source.svg` — het originele bronbestand, voor eventuele toekomstige aanpassingen

## Hoe dien je dit in?

1. Fork [home-assistant/brands](https://github.com/home-assistant/brands).
2. Kopieer de map `custom_integrations/cure_afvalbeheer/` (zonder `source.svg` en
   dit `README.md` — die zijn alleen voor intern gebruik in dit project) naar
   dezelfde map in je fork.
3. Open een pull request. Vermeld het domein (`cure_afvalbeheer`) en een link naar
   deze GitHub-repository (`https://github.com/Sarnog/ha-cure-afvalbeheer`) zoals
   opgegeven in `manifest.json`.
4. Wacht op review/goedkeuring door de HA-maintainers. Zodra de PR gemerged is,
   verschijnt het logo automatisch in Home Assistant — er is geen versie-release
   of herstart van deze integratie voor nodig.

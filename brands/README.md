# Merklogo

Sinds **Home Assistant 2026.3** kan een custom integratie zijn eigen merklogo
gewoon meeleveren in de integratie zelf — een externe pull request naar
[home-assistant/brands](https://github.com/home-assistant/brands) is niet
meer nodig. Home Assistant leest de afbeeldingen automatisch uit een
`brand/`-map binnen de integratie (`custom_components/cure_afvalbeheer/brand/`)
en geeft die voorrang boven de centrale brands-CDN. Er is geen aanpassing in
`manifest.json` voor nodig; deze repository voldoet met
`hacs.json`'s `"homeassistant": "2026.7.0"` ruim aan de vereiste minimumversie.

De daadwerkelijke, actieve bestanden staan dus in
`custom_components/cure_afvalbeheer/brand/`:

- `icon.png` (256×256)
- `icon@2x.png` (512×512)
- `logo.png` (256×256)
- `logo@2x.png` (512×512)

`logo-source.svg` in deze map is alleen het originele bronbestand (het
officiële Cure-logo), bewaard voor als de PNG's ooit opnieuw gegenereerd
moeten worden — dit bestand wordt door Home Assistant zelf niet gebruikt.

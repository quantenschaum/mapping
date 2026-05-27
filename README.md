# BSH-DATEN

Die Daten in diesem Ordner wurden von den folgenden Endpunkten abgerufen,
die unter https://gdi.bsh.de/public/public_services.html aufgeführt sind.

- https://gdi.bsh.de/en/mapservice/Aids-to-Navigation-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Hydrographic-Data-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Underwater-Obstructions-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Land-and-Marine-Areas-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Topography-for-Nautical-Products-WMS

Datum des Downloads: 2026-04-27 und 2026-03-02 (`SOUNDG.json` zuletzt verfügbare Spot-Sounding-Daten)

Die Lizenzangabe zum Zeitpunkt des Downloads war und ist http://www.gesetze-im-internet.de/geonutzv/GeoNutzV.pdf

Die Daten wurden in Layer aufgeteilt, ein Layer pro Datei.

Hinweis vom BSH zum Zeitpunkt des Downloads: "Nicht zur Navigation geeignet."
Diese wurd ab ca. April 2026 geänder zu "Die Verwendung der Daten zu Navigationszwecken ist nicht gestattet."

## NfS-Korrekturen

`nfs.json` enthält Positionen und Anweisungen für Korrekturen, die soweit möglich manuell aus den [NfS](https://www.bsh.de/DE/THEMEN/Schifffahrt/Nautische_Informationen/Nachrichten_fuer_Seefahrer/Nachrichten_fuer_Seefahrer_abonnement_node.html) extrahiert wurden. Diese Korrekturen wurden in die Daten eingearbeitet.

|   NfS   | extrahiert | eingearbeitet |
| :-----: | :--------: | :-----------: |
| 13/2026 |     ✓      |       ✓       |
| 14/2026 |     ✓      |       ✓       |
| 15/2026 |     ✓      |       ✓       |
| 17/2026 |     ✓      |               |
| 18/2026 |     ✓      |               |
| 19/2026 |     ✓      |               |
| 20/2026 |     ✓      |               |
| 21/2026 |     ✓      |               |

**zugehörige BfS** (wie in den NfS aufgeführt): NL BaZ 17/P- und T-Liste/26, PL 15/183/26, WSA Elbe-Nordsee 103/26, WSA Elbe-Nordsee 113(P), 121/26, WSA Elbe-Nordsee 131/26, WSA Elbe-Nordsee, Survey LP30325/26, 142/26, WSA Elbe-Nordsee, Survey LP30426, LP30138, LP30422/26, WSA Elbe-Nordsee, Survey LP30426/26, WSA Elbe-Nordsee, Survey LP30598/26, WSA Ems-Nordsee 56/26, WSA Ems-Nordsee 99, 104/26, WSA Ems-Nordsee, Survey LP30280/26, WSA Ostsee 127, 132/26, WSA Ostsee 137/26, WSA Ostsee 82/26, WSA Ostsee 87/26, WSA Ostsee 92/26, WSA Ostsee 98/26, WSA Ostsee, Survey LP30634/26, WSA Weser-Jade-Nordsee 53/26; WSA Elbe-Nordsee 135/26

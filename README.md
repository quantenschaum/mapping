# BSH-DATEN

Die Daten in diesem Ordner wurden von den folgenden Endpunkten, die das BSH öffentlich zur Verfügung stellt und unter https://gdi.bsh.de/public/public_services.html auflistet, abgerufen:

- https://gdi.bsh.de/en/mapservice/Aids-to-Navigation-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Hydrographic-Data-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Underwater-Obstructions-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Land-and-Marine-Areas-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Topography-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Maritime-Boundaries-for-Nautical-Products-WMS

Die Daten wurden in Layer aufgeteilt, ein Layer pro Datei.

Datum des initialen Downloads: 

- 2026-04-27 alle Layer
- 2026-03-02 zusätzlich `SOUNDG.json` (zuletzt verfügbare Tiefenpunkte)

Die Lizenzangabe zum Zeitpunkt des Downloads war und ist die [GeoNutzV](http://www.gesetze-im-internet.de/geonutzv/GeoNutzV.pdf).  

D.h. die Nutzung der Daten für u.a. folgenden Zwecke ist zulässig: 

- alle Nutzungszwecke, kommerziell wie nicht-kommerziell
- Bearbeitung und Umwandlung der Daten sowie die Kombination mit anderen Daten
- Vervielfältigung, Verbreitung und öffentliche Zugänglichmachung

Eine Einschränkung der Nutungszwecke ist im Rahmen der GeoNutzV nicht vorgesehen, dennoch sei auf folgende Angaben des BSH hingewiesen:

- Hinweis vom BSH zum Zeitpunkt des initialen Downloads: "Nicht zur Navigation geeignet."
- Seit April 2026 geändert zu "Die Verwendung der Daten zu Navigationszwecken ist nicht gestattet."

## Updates

Einzelne Layer wurden selektiv aus den oben genannten Endpunken zu späteren Zeitpunkten aktualisiert.

|   Datum    | Layer  | Beschreibung  |
| :--------: | :----: | :------------ |
| 2026-05-27 | DEPARE | Konturflächen |
| 2026-05-27 | DEPCNT | Tiefenlinien  |

## NfS-Korrekturen

`nfs.json` enthält Positionen und Anweisungen für Korrekturen, die soweit möglich manuell aus den [NfS](https://www.bsh.de/DE/THEMEN/Schifffahrt/Nautische_Informationen/Nachrichten_fuer_Seefahrer/Nachrichten_fuer_Seefahrer_abonnement_node.html) extrahiert wurden. Diese Korrekturen wurden manuell soweit möglich und relevant in die Daten eingearbeitet.

|   NfS   | extrahiert | eingearbeitet |
| :-----: | :--------: | :-----------: |
| 13/2026 |     ✓      |       ✓       |
| 14/2026 |     ✓      |       ✓       |
| 15/2026 |     ✓      |       ✓       |
| 17/2026 |     ✓      |       ✓       |
| 18/2026 |     ✓      |       ✓       |
| 19/2026 |     ✓      |       ✓       |
| 20/2026 |     ✓      |       ✓       |
| 21/2026 |     ✓      |       ✓       |
| 22/2026 |     ✓      |       ✓       |

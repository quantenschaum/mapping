# BSH DATA

The data in this folder was retrieved from the following endpoints,
which are listed at https://gdi.bsh.de/public/public_services.html

- https://gdi.bsh.de/en/mapservice/Aids-to-Navigation-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Hydrographic-Data-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Underwater-Obstructions-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Land-and-Marine-Areas-for-Nautical-Products-WMS
- https://gdi.bsh.de/en/mapservice/Topography-for-Nautical-Products-WMS

Date of download: 2026-04-27 and 2026-03-02 (`SOUNDG.json` last available spot sounding data)

The license statement at the time of the download was http://www.gesetze-im-internet.de/geonutzv/GeoNutzV.pdf

The data was split into layers, one layer per file.

Disclaimer by BSH at time of download: "Nicht zur Navigation geeignet." The phrase "Die Verwendung der Daten zu Navigationszwecken ist nicht gestattet." was added later, *after* these downloads.

`_NFS.json` contains locations and instructions for correction, that have been extracted manually from the [NfS](https://www.bsh.de/DE/THEMEN/Schifffahrt/Nautische_Informationen/Nachrichten_fuer_Seefahrer/Nachrichten_fuer_Seefahrer_abonnement_node.html) as far as possible.

|   NfS   | extracted | applied |
| :-----: | :-------: | :-----: |
| 13/2026 |     ✓     |    ✓    |
| 14/2026 |     ✓     |    ✓    |
| 15/2026 |     ✓     |    ✓    |
| 17/2026 |     ✓     |         |
| 18/2026 |     ✓     |         |
| 19/2026 |     ✓     |         |
| 20/2026 |     ✓     |         |
| 21/2026 |     ✓     |         |

corresponding BfS (as listed in NfS): NL BaZ 17/P- und T-Liste/26, PL 15/183/26, WSA Elbe-Nordsee 103/26, WSA Elbe-Nordsee 113(P), 121/26, WSA Elbe-Nordsee 131/26, WSA Elbe-Nordsee, Survey LP30325/26, 142/26, WSA Elbe-Nordsee, Survey LP30426, LP30138, LP30422/26, WSA Elbe-Nordsee, Survey LP30426/26, WSA Elbe-Nordsee, Survey LP30598/26, WSA Ems-Nordsee 56/26, WSA Ems-Nordsee 99, 104/26, WSA Ems-Nordsee, Survey LP30280/26, WSA Ostsee 127, 132/26, WSA Ostsee 137/26, WSA Ostsee 82/26, WSA Ostsee 87/26, WSA Ostsee 92/26, WSA Ostsee 98/26, WSA Ostsee, Survey LP30634/26, WSA Weser-Jade-Nordsee 53/26; WSA Elbe-Nordsee 135/26

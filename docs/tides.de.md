# Gezeitenstromatlas

## Gezeitentafeln und Wasserstand

Das deutsche BSH und der niederländische RWS stellen Gezeitendaten betreit unter

- <https://gezeiten.bsh.de/>
- <https://wasserstand-nordsee.bsh.de/>
- <https://waterinfo.rws.nl/>

Diese sind in die Karte integriert worden. Durch Anklicken der blauen Markierungen erhalten Sie in einem Popup die Gezeitenvorhersagedaten für den aktuellen und den nächsten Tag. Wenn nicht anders angegeben, ist die Bezugshöhe SKN/LAT.

![Gezeiten-Zahlen](img/tide-times.webp)

### Höhe der Gezeit

Die Höhe der Gezeit (HdG) ist die Höhe bezogen auf LAT/SKN, berechnet mit dem [astronomischen Vorhersagemodell](https://gezeiten.bsh.de). Der danach angegebene Wert K ist eine auf die HdG anzuwendende Korrektur, welche die Wettereinflüsse enthält. Sie wird ebenfalls vom BSH berechnet und in der [Wasserstandsvorhersage](https://wasserstand-nordsee.bsh.de) veröffentlicht. 

!!! warning "Achtung"
    Das BSH bezieht seine Wasserstandskorrektur auf das mittlere Hoch- bzw. Niedrigwasser, K ist hingegen relativ zum astronomischen Vorhersagewert und umfasst ausschließlich die Wettereinflüsse.

### Tidenkoeffizient

Analog (aber anders) zum französischen Tidenkoeffizienten wurde der Tidenkoeffizient C eingeführt. Er definiert sich als das Verhältnis des aktuellen Tidenstiegs-/falls zum mittleren Springtidenhub.

```
               | HW - NW |
C = 100 * ---------------------
          mittl. Springtidenhub
```

Wozu ist das nützlich? - Man erkennt unmittelbar, wie der aktuelle Stieg/Fall im Vergleich zur mittleren Springtidenhubhöhe ausfällt. Da die Stromgeschwindigkeit in der Regel direkt proportional zum Stieg/Fall ist, kann man C nutzen, um die im Gezeitenstromatlas angegebene Spring-Stromgeschwindigkeit zu skalieren. Dadurch lässt sich die Strominterpolation deutlich einfacher und schneller durchführen.

Er wird in jeder Zeile aus dem Höhenunterschied zwischen dieser und der vorherigen Zeile berechnet. Liegt der gewünschte Zeitpunkt zwischen zwei Zeilen, liest man C aus der unteren Zeile ab.

!!! example "Beispiel"
    Möchte man die Stromgeschwindigkeit am 28.02. um 1200 kennen, liest man C am nächsten NW als 78 ab. Man multipliziert die im Gezeitenstromatlas abgelesene Spring-Stromgeschwindigkeit einfach mit 0,78 und erhält den interpolierten Wert.

### Gezeitenkurven

![tide curve](img/tidecurve.webp)
Gezeitenkurven im ATT-Stil, berechnet aus den vom BSH bereitgestellten Daten, kann man [hier](index.de.md#gezeitenkurven) herunterladen.

## Gezeitenstrom

Das BSH stellt Gezeitenstromdaten für die Nordsee, den Ärmelkanal und die Deutsche Bucht (höhere Auflösung) bereit.

Die Darstellung dieser Daten im [GeoSeaPortal](https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas) ist leider nicht wirklich brauchbar, man kann weder den Datensatz noch die Gezeitenstunde auswählen. Aber die Rohdaten sind unter [Nordsee](https://gdi.bsh.de/de/feed/Tidal-currents-North-Sea.xml)/[Küste](https://gdi.bsh.de/de/feed/Tidal-currents-German-coastal-waters-and-neighbouring-regions.xml) verfügbar.

I habe mit [QGIS](https://qgis.org/) das Gezeitenstromfeld gerendert und Angaben für Stromgeschwindigkeit- und richtung hinzugefügt. Man kann die Gezeitenstunde auswählen, je nach Zoomstufe erhält man einen Überblick über den Gezeitenstrom und kann bei entsprechender Zoomstufe die Werte direkt an der gewünschten Position ablesen. Bei weiterem Hineinzoomen wird der Küstendatensatz mit höherer Auflösung eingeblendet.

![tides](img/tides.webp)

Die Karte sieht wie oben abgebildet aus. Mit dem Schieberegler wird die Stunde vor/nach Hochwasser Helgoland ausgewählt. Die Pfeile in Größe und Farbe zeigen die durchschnittliche Stromgeschwindigkeit und -richtung an. Die Zahl unter dem Pfeil ist die durchschnittliche Stromrichtung, die Zahlen über dem Pfeil sind die Stromgeschwindigkeit in Zehntelknoten bei Nipptide (vor dem Punkt) und bei Springtide (nach dem Punkt).

![tide figures](img/figures.webp)

Wenn der Schieberegler auf `fig` eingestellt ist, werden die Gezeitenpfeile aller Stunden gleichzeitig angezeigt, um die Gezeitenstromfigur für den jeweiligen Ort darzustellen. Die Zahlen stehen für die Stunde vor/nach HW.

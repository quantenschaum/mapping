---
description: frei verwendbare Seekarten für deutsche und niederländische Gewässer auf Basis offener Daten, Hintergrundinformationen, Datenquellen und vorgefertigte Seekarten zum Download
---
# Download

![freenauticalchart update](https://healthchecks.io/b/3/908ee633-599b-4691-ae79-101e8725752c.svg)

Hier finden Sie vorkompilierte Karten zum Herunterladen in verschiedenen Formaten, die in unterschiedlichen Anwendungen verwendet werden können.
 
## Wichtige Hinweise 
 
!!! danger "Haftungsausschluss"
    Die zur Verfügung gestellten Karten und Dateien dienen ausschließlich Informations-, Referenz- und Schulungszwecken. **Sie sind nicht für die Navigation geeignet.** Für maßgebliche und aktuelle Navigationsinformationen verwenden Sie offizielle Quellen wie z.B. amtliche Seekarten von Regierungsbehörden oder zertifizierten Anbietern.
    
    Es wird keine Garantie, weder ausdrücklich noch stillschweigend, für die Genauigkeit, Zuverlässigkeit, Vollständigkeit oder Aktualität der bereitgestellten Karten und Daten gegeben. Der Anbieter übernimmt keinerlei Verantwortung oder Haftung für etwaige Fehler, Auslassungen, veraltete Informationen oder den Missbrauch dieser Daten. 
    
    **Verwendung auf eigene Gefahr!**

!!! warning "BSH-Daten"
    Auf dem Server des BSH wurden weitere Teile der bislang frei zugänglichen Daten entfernt und der Zugriff erschwert. Weitere Informationen zu [Open Data](opendata.md).  

    Das BSH weist nun darauf hin: "Die Nutzung der Daten für Navigationszwecke ist nicht gestattet."

    Der deutsche Teil der Karte basiert jetzt auf [älteren Daten](https://github.com/quantenschaum/mapping/tree/bsh-data#bsh-daten) mit Stand 2026-04-27 sowie auf Punktlotungen, die zuletzt am 2026-03-02 verfügbar waren. Anschließend wurden die Daten selektiv mit den aktuell verfügbaren Datensätzen aktualisiert, und die NfS wurde soweit wie möglich eingearbeitet.

??? info "Lizenzen"    
    - Die herunterladbaren Dateien auf dieser Seite sind lizenziert unter [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
    - Der Code dieses Projekts, der zur Erstellung der Karten und anderer Daten verwendet wird, ist lizenziert unter [GPL](https://www.gnu.org/licenses/gpl-3.0.de.html).

??? note "Datenquellen"
    Die im Rahmen dieses Projekts erstellten Karten beruhen auf Daten von
    
    - :de: [BSH](https://www.bsh.de/)
        - [GeoSeaPortal](https://www.geoseaportal.de/mapapps/resources/apps/navigation/)/[Öffentliche Dienste](https://gdi.bsh.de/public/public_services.html) ([GeoNutzV](https://www.bsh.de/DE/THEMEN/Geoinformationen/_Anlagen/Downloads/Geonutzv.pdf?__blob=publicationFile&v=2))
        - [Bathymetry](https://gdi.bsh.de/de/feed/Elevation-Bathymetry.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [SKN Seekartenull](https://gdi.bsh.de/de/feed/Chart-datum-for-the-German-Bight-2026.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [Tidal Currents North Sea](https://gdi.bsh.de/de/feed/Tidal-currents-North-Sea.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [Tidal Currents Coastal](https://gdi.bsh.de/de/feed/Tidal-currents-German-coastal-waters-and-neighbouring-regions.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
    - :nl: [RWS](https://www.rijkswaterstaat.nl/)
        - [ENC](https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc) (?)
        - [Vaarwegmarkeringen drijvend](https://data.overheid.nl/dataset/5eb0f65c-e90f-464e-8f46-01c5eeb6adf5) ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.en))
        - [Vaarwegmarkeringen vast](https://data.overheid.nl/dataset/2bf96f3b-128d-4506-85e0-08e8fc19a11c) ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.en))

## [OsmAnd](https://osmand.net/)

### Vektor-Karten

Vektorkarten und Stile für OsmAnd können durch einfaches Öffnen der `obf`- oder `xml`-Datei mit der OsmAnd-App installiert werden. Die Datei wird dann automatisch importiert und als Teil des „Offline-Vektordiagramms“ verwendet. 

- [:de: Tiefendaten DE](depth-de.obf){:download}
- [:nl: Tiefendaten NL](depth-nl.obf){:download}
- [:globe_with_meridians: Feuersektoren, weltweit](lightsectors.obf){:download}
- [:material-xml: Marine Rendering Style](marine.render.xml){:download}

!!! failure "Marine Rendering Style verwenden!"
    Die Vektorkarte wird ohne den Marine Rendering Style und Renderengine 2 (OpenGL) nicht korrekt dargestellt!  
    **Die Darstellung funktioniert ausschließlich mit dem Marine Rendering Style!**  
    Der Marine Rendering Style ist jetzt in OsmAnd bereits enthalten.

### Raster-Karten

Die Rasterkarten werden importiert, indem die `sqlitedb`-Dateien mit der App geöffnet werden. 

- [:de: FNC DE](fnc-de.sqlitedb){:download}
- [:nl: FNC NL](fnc-nl.sqlitedb){:download}
- [:de: Gezeitenstromatlas DE](tides.sqlitedb.zip){:download}

#### Online-Karten

Die Rasterkarten können auch als Online-Kacheln zu OsmAnd hinzugefügt werden, die Kartenkacheln werden bei Bedarf heruntergeladen.

- :de: FNC DE online [`https://freenauticalchart.net/fnc-de/{0}/{1}/{2}.png`](http://osmand.net/add-tile-source?name=FNC-DE&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/fnc-de/%7B0%7D/%7B1%7D/%7B2%7D.png)
- :nl: FNC NL online [`https://freenauticalchart.net/fnc-nl/{0}/{1}/{2}.png`](http://osmand.net/add-tile-source?name=FNC-NL&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/fnc-nl/%7B0%7D/%7B1%7D/%7B2%7D.png)

!!! tip
    Wählen Sie „sqlitedb“ als Speicherformat. Dadurch werden die Kacheln effizienter in einer einzigen Datenbankdatei gespeichert.  
    Wenn Sie eine Verfallszeit festlegen, werden die Kacheln nach Ablauf erneut heruntergeladen, so dass Sie automatische Aktualisierungen erhalten.

## [AvNav](https://www.wellenvogel.net/software/avnav/docs/beschreibung.html?lang=en)

### Raster-Karten

AvNav kann `mbtiles` lesen. Legen Sie die Dateien einfach in dem Ordner `charts` von AvNav ab.

- [:de: FNC DE](fnc-de.mbtiles){:download}
- [:nl: FNC NL](fnc-nl.mbtiles){:download}
- [:de: Gezeitenstromatlas DE](tides.mbtiles.zip){:download}

### Vektor-Karten

Die S57-Dateien können mit dem [Ocharts(NG)](https://www.wellenvogel.net/software/avnav/docs/hints/ochartsng.html) Plugin verwendet werden, sie funktionieren auch mit [OpenCPN](https://opencpn.org/).
    
- [:de: FNC DE](fnc-de.zip){:download}
- [:nl: FNC NL](fnc-nl.zip){:download}

!!! info "FNC NL"
    Die Seezeichen in der FNC-NL-Vektorkarte stammen aus der ursprünglichen ENC und nicht aus dem separaten Datensatz. Die Maßstabseinstellungen der Karte wurden so angepasst, dass die in AvNav korrekt angezeigt wird. Bei der Konvertierung der Karten mit OpenCPN funktioniert dies nicht ohne weiteres.

## [OpenCPN](https://opencpn.org/)

siehe [AvNav](#avnav), die Karten funktionieren auch mit OpenCPN.

## [JOSM](https://josm.openstreetmap.de/)

Die Rasterkarten können in JOSM als [Hintergrund-Layer](https://josm.openstreetmap.de/wiki/Help/Preferences/Imagery) hinzugefügt werden.

- :de: FNC DE `tms:https://freenauticalchart.net/fnc-de/{zoom}/{x}/{y}.png`
- :nl: FNC NL `tms:https://freenauticalchart.net/fnc-nl/{zoom}/{x}/{y}.png`

Sie können auch [dieses zusätzliche `mapcss`](https://josm.openstreetmap.de/wiki/Help/Preferences/MapPaintPreference) (als letzten Eintrag) für eine verbesserte Darstellung von Seezeichen hinzufügen.

- `https://raw.githubusercontent.com/quantenschaum/mapping/refs/heads/icons/extra.mapcss`

## [Gezeitenkurven](tides.md#gezeitenkurven)

im ATT-Stil

- [:de: Gezeitenkurven DE](tidecurves.pdf){:download}

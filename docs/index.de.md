---
description: frei verwendbare Seekarten für deutsche und niederländische Gewässer auf Basis offener Daten, Hintergrundinformationen, Datenquellen und vorgefertigte Seekarten zum Download
---
# Download

Hier finden Sie vorkompilierte Karten zum Herunterladen in verschiedenen Formaten, die in unterschiedlichen Anwendungen verwendet werden können.
 
??? danger "Haftungsausschluss"
    Die zur Verfügung gestellten Karten und Datendateien dienen nur zu Informations- und Referenzzwecken. Sie sind nicht für die Navigation, den offiziellen Schiffsbetrieb oder andere Aktivitäten gedacht, die präzise geografische und hydrografische Daten erfordern. Benutzer sollten offizielle Quellen, wie z. B. Regierungsbehörden oder zertifizierte Navigationsanbieter, für maßgebliche und aktuelle Navigationsinformationen konsultieren.

    Es wird keine Garantie, weder ausdrücklich noch stillschweigend, für die Genauigkeit, Zuverlässigkeit oder Vollständigkeit der bereitgestellten Karten gegeben. Der Anbieter übernimmt keine Verantwortung oder Haftung für etwaige Fehler, Auslassungen oder den Missbrauch dieser Informationen.

    **Verwendung auf eigene Gefahr!**

??? info "Lizenzen"    
    - Die herunterladbaren Dateien auf dieser Seite sind lizenziert unter [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
    - Der Code dieses Projekts, der zur Erstellung der Karten und anderer Daten verwendet wird, ist lizenziert unter [GPL](https://www.gnu.org/licenses/gpl-3.0.de.html).

??? note "Datenquellen"
    Die im Rahmen dieses Projekts erstellten Karten beruhen auf Daten von
    
    - :de: [BSH](https://www.bsh.de/)
        - [GeoSeaPortal](https://www.geoseaportal.de/mapapps/resources/apps/navigation/) ([GeoNutzV](https://www.bsh.de/DE/THEMEN/Geoinformationen/_Anlagen/Downloads/Geonutzv.pdf?__blob=publicationFile&v=2))
        - [Bathymetry](https://gdi.bsh.de/de/feed/Elevation-Bathymetry.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [SKN Seekartenull](https://gdi.bsh.de/de/feed/Chart-datum-for-the-German-Bight-2021.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [Tidal Currents North Sea](https://gdi.bsh.de/de/feed/Tidal-currents-North-Sea.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
        - [Tidal Currents Coastal](https://gdi.bsh.de/de/feed/Tidal-currents-German-coastal-waters-and-neighbouring-regions.xml) ([DL-DE->BY-2.0](https://www.govdata.de/dl-de/by-2-0))
    - :nl: [RWS](https://www.rijkswaterstaat.nl/)
        - [ENC](https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc) (?)
        - [Vaarwegmarkeringen drijvend](https://data.overheid.nl/dataset/5eb0f65c-e90f-464e-8f46-01c5eeb6adf5) ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.en))
        - [Vaarwegmarkeringen vast](https://data.overheid.nl/dataset/2bf96f3b-128d-4506-85e0-08e8fc19a11c) ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.en))

??? note "Rohdaten"
    Rohdaten-Dateien sind hier verfügbar. Sie können in [QGIS](https://qgis.org/) verwendet werden, um eigene Karten zu erstellen oder um die Daten zu untersuchen oder mit ihnen herumzuspielen. Die in diesem Projekt verwendete QGIS-Datei ist auf [GitHub](https://github.com/quantenschaum/mapping/tree/master/qgis) zu finden.
    
    - [Data Paket (alles zum Rendern/Drucken von Karten in einem ZIP)](qmap-data.zip){:download}
    - [QMAP DE tiles](qmap-de.tiles.zip){:download}
    - [QMAP NL tiles](qmap-nl.tiles.zip){:download}
    
    
## [OsmAnd](https://osmand.net/)

### Vektor-Karten

Vektorkarten und Stile für OsmAnd können durch einfaches Öffnen der `obf`- oder `xml`-Datei mit der OsmAnd-App installiert werden. Die Datei wird dann automatisch importiert und als Teil des „Offline-Vektordiagramms“ verwendet. 

- [:de: Tiefendaten DE](depth-de.obf){:download}
- [:nl: Tiefendaten NL](depth-nl.obf){:download}
- [:globe_with_meridians: Feuersektoren, weltweit](lightsectors.obf){:download}
- [:material-xml: Marine Rendering Style](marine.render.xml){:download}
- [:de: QMAP DE (Seezeichen)*](qmap-de.obf){:download}

!!! warning "* QMAP DE"
    Die QMAP DE Vektorkarte enthält Seezeichen, Felsen und andere punktförmige Objekte. Sie ist dafür gedacht, *anstelle* der OSM-Daten verwendet zu werden, nicht in Kombination mit ihnen. Wenn Sie beide aktivieren, erhalten Sie doppelte Objekte, was verwirrend sein kann.

!!! warning "Rendering Style"
    Die Vektorkarte wird ohne den Rendering-Stil „Marine“ und die Render-Engine 2 (OpenGL) nicht korrekt dargestellt!

### Raster-Karten

Die Rasterkarten werden importiert, indem die `sqlitedb`-Dateien mit der App geöffnet werden. 

- [:de: QMAP DE](qmap-de.sqlitedb){:download}
- [:nl: QMAP NL](qmap-nl.sqlitedb){:download}
- [:de: Gezeitenstromatlas DE](tides.sqlitedb.zip){:download}

#### Online-Karten

Die Rasterkarten können auch als Online-Kacheln zu OsmAnd hinzugefügt werden, die Kartenkacheln werden bei Bedarf heruntergeladen.

- :de: QMAP DE online [`https://freenauticalchart.net/qmap-de/{0}/{1}/{2}.webp`](http://osmand.net/add-tile-source?name=QMAP-DE&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/qmap-de/%7B0%7D/%7B1%7D/%7B2%7D.webp)
- :nl: QMAP NL online [`https://freenauticalchart.net/qmap-nl/{0}/{1}/{2}.webp`](http://osmand.net/add-tile-source?name=QMAP-NL&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/qmap-nl/%7B0%7D/%7B1%7D/%7B2%7D.webp)

!!! tip
    Wählen Sie „sqlitedb“ als Speicherformat. Dadurch werden die Kacheln effizienter in einer einzigen Datenbankdatei gespeichert.  
    Wenn Sie eine Verfallszeit festlegen, werden die Kacheln nach Ablauf erneut heruntergeladen, so dass Sie automatische Aktualisierungen erhalten.

## [AvNav](https://www.wellenvogel.net/software/avnav/docs/beschreibung.html?lang=en)

### Raster-Karten

AvNav kann `mbtiles` lesen. Legen Sie die Dateien einfach in dem Ordner `charts` von AvNav ab.

- [:de: QMAP DE](qmap-de.mbtiles){:download}
- [:nl: QMAP NL](qmap-nl.mbtiles){:download}
- [:de: Gezeitenstromatlas DE](tides.mbtiles.zip){:download}

### Vektor-Karten

Die S57-Dateien können mit dem [Ocharts(NG)](https://www.wellenvogel.net/software/avnav/docs/hints/ochartsng.html) Plugin verwendet werden, sie funktionieren auch mit [OpenCPN](https://opencpn.org/).
    
- [:de: QMAP DE](qmap-de.zip){:download}
- [:nl: QMAP NL](qmap-nl.zip){:download}

!!! info "QMAP NL"
    Die Seezeichen in der QMAP-NL-Vektorkarte stammen aus der ursprünglichen ENC und nicht aus dem separaten Datensatz. Die Maßstabseinstellungen der Karte wurden so angepasst, dass die in AvNav korrekt angezeigt wird. Bei der Konvertierung der Karten mit OpenCPN funktioniert dies nicht ohne weiteres.

## [OpenCPN](https://opencpn.org/)

OpenCPN und andere Anwendungen können Rasterkarten aus `mbtiles` anzeigen.

- [:de: QMAP DE](qmap-de.png.mbtiles){:download}
- [:nl: QMAP NL](qmap-nl.png.mbtiles){:download}
- Vektor-Karten: siehe oben

!!! info
    OpenCPN unterstützt WebP nicht, daher gibt es separate `mbtiles`-Dateien, die png-Kacheln enthalten.

## [JOSM](https://josm.openstreetmap.de/)

Die Rasterkarten können in JOSM als [Hintergrund-Layer](https://josm.openstreetmap.de/wiki/Help/Preferences/Imagery) hinzugefügt werden.

- :de: QMAP DE `tms:https://freenauticalchart.net/qmap-de/{zoom}/{x}/{y}.png`
- :nl: QMAP NL `tms:https://freenauticalchart.net/qmap-nl/{zoom}/{x}/{y}.png`

Sie können auch [dieses zusätzliche `mapcss`](https://josm.openstreetmap.de/wiki/Help/Preferences/MapPaintPreference) (als letzten Eintrag) für eine verbesserte Darstellung von Seezeichen hinzufügen.

- `https://raw.githubusercontent.com/quantenschaum/mapping/refs/heads/icons/extra.mapcss`

## Garmin

Es gibt eine **experimentelle** Unterstützung für Garmin-Geräte. Die Datei enthält nur Tiefendaten und Seezeichen, sie kann mit Daten von [bbbike](https://extract.bbbike.org/?format=garmin-oseam.zip) kombiniert werden. Möglicherweise müssen Sie in den Karteneinstellungen Lotungen und Seekartenfarben aktivieren.

- [:de: Tiefendaten DE](gmapsupp.img){:download}

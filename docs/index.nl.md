# Download

Hier vind je voorgecompileerde kaarten om te downloaden in verschillende formaten die bruikbaar zijn in verschillende applicaties.

!!! warning "Nieuwe URL"
    Dit project is verplaatst naar de nieuwe locatie <https://freenauticalchart.net> en maakt nu gebruik van Cloudflare CDN voor verbeterde prestaties.

??? danger "Disclaimer"
    De geleverde kaarten en gegevensbestanden zijn alleen bedoeld voor informatieve en referentiedoeleinden. Ze zijn niet bedoeld voor navigatie, officiële maritieme operaties of andere activiteiten die precieze geografische, hydrografische gegevens vereisen. Gebruikers moeten officiële bronnen raadplegen, zoals overheidsinstanties of gecertificeerde navigatieleveranciers, voor gezaghebbende en actuele navigatie-informatie.

    Er wordt geen garantie, expliciet of impliciet, gegeven met betrekking tot de nauwkeurigheid, betrouwbaarheid of volledigheid van de verstrekte kaarten. De aanbieder aanvaardt geen verantwoordelijkheid of aansprakelijkheid voor eventuele fouten, weglatingen of misbruik van deze informatie.

    **Gebruik op eigen risico!**

??? info "Licentie"    
    - De downloadbare bestanden op deze pagina zijn gelicenseerd onder [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
    - De code van dit project die wordt gebruikt om de kaarten en andere gegevens te genereren is gelicenseerd onder [GPL](https://www.gnu.org/licenses/gpl-3.0.de.html).

??? info "Dieptegegevens"
    De Duitse kaart bevat peilingen uit <https://gdi.bsh.de/de/feed/Elevation-Bathymetry.xml> die van 2018 is en voor het laatst is bijgewerkt op 2023-05! Dit is experimenteel, gegevens kunnen fout zijn of ontbreken. Peilingen en hoogtelijnen komen uit verschillende datasets, dus ze kunnen in bepaalde gebieden niet overeenkomen.

??? note "Gegevensbronnen"    
    De kaarten van dit project zijn gebaseerd op gegevens van
    
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

??? note "Ruwe gegevens"
    De ruwe gegevensbestanden zijn hier beschikbaar. Ze kunnen worden gebruikt in [QGIS](https://qgis.org/) om je eigen kaarten te renderen of om gegevens te onderzoeken of ermee te spelen. Het QGIS-bestand dat in dit project wordt gebruikt, is te vinden op [GitHub](https://github.com/quantenschaum/mapping/tree/master/qgis).
  
    - [Datapakket (alles om kaarten te renderen/printen in één ZIP)](qmap-data.zip){:download}
    - [QMAP DE tiles](qmap-de.tiles.zip){:download}
    - [QMAP NL tiles](qmap-nl.tiles.zip){:download}
    
    
## [OsmAnd](https://osmand.net/)

### Vectorkaarten

Vectorkaarten en stijlen voor OsmAnd kunnen geïnstalleerd worden door simpelweg het `obf` of `xml` bestand te openen met de OsmAnd app. Het bestand wordt dan automatisch geïmporteerd en gebruikt als onderdeel van de “offline vectorkaart”.

- [:de: Dieptegegevens DE](depth-de.obf){:download}
- [:nl: Dieptegegevens NL](depth-nl.obf){:download}
- [:globe_with_meridians: Lichtsectoren wereldwijd](lightsectors.obf){:download}
- [:material-xml: Marine Rendering Style](marine.render.xml){:download}
- [:de: QMAP DE (zeeteken)*](qmap-de.obf){:download}

!!! warning "* QMAP DE"
    De QMAP DE vectorkaart bevat zeeteken, rotsen en andere puntvormige objecten. Deze kaart is bedoeld om te gebruiken *in plaats van* de OSM-gegevens, niet in combinatie ermee. Als je beide activeert, krijg je dubbele objecten, wat verwarrend kan zijn.

!!! warning "Weergavestijl"
    De vectorkaart wordt niet goed weergegeven zonder de maritieme renderstijl en renderengine 2 (OpenGL)!

### Rasterkaarten

De kaarten worden geïmporteerd door de `sqlitedb` bestanden te openen met de app.

- [:de: QMAP DE](qmap-de.sqlitedb){:download}
- [:nl: QMAP NL](qmap-nl.sqlitedb){:download}
- [:de: Getijdenatlas DE](tides.sqlitedb.zip){:download}

#### Online kaarten

De rasterkaarten kunnen ook aan OsmAnd worden toegevoegd als online tegelbron, kaarttegels worden dan op verzoek gedownload.
 
- :de: QMAP DE online [`https://freenauticalchart.net/qmap-de/{0}/{1}/{2}.webp`](http://osmand.net/add-tile-source?name=QMAP-DE&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/qmap-de/%7B0%7D/%7B1%7D/%7B2%7D.webp)
- :nl: QMAP NL online [`https://freenauticalchart.net/qmap-nl/{0}/{1}/{2}.webp`](http://osmand.net/add-tile-source?name=QMAP-NL&min_zoom=8&max_zoom=16&url_template=https://freenauticalchart.net/qmap-nl/%7B0%7D/%7B1%7D/%7B2%7D.webp)

!!! tip
    Selecteer `sqlitedb` als opslagformaat. Dit zal de tiles efficiënter opslaan in een enkel databasebestand.  
    Als u een verlooptijd instelt, worden de tiles opnieuw gedownload nadat ze zijn verlopen, zodat u automatische updates krijgt.

## [AvNav](https://www.wellenvogel.net/software/avnav/docs/beschreibung.html?lang=en)

### Rasterkaarten

AvNav kan `mbtiles` lezen. Zet de bestanden gewoon neer in de map `charts` van AvNav.

- [:de: QMAP DE](qmap-de.mbtiles){:download}
- [:nl: QMAP NL](qmap-nl.mbtiles){:download}
- [:de: Getijdenatlas DE](tides.mbtiles.zip){:download}

### Vectorkaarten

De S57-bestanden kunnen worden gebruikt met de [Ocharts(NG)](https://www.wellenvogel.net/software/avnav/docs/hints/ochartsng.html) plugin, ze werken ook met [OpenCPN](https://opencpn.org/).

- [:de: QMAP DE](qmap-de.zip){:download}
- [:nl: QMAP NL](qmap-nl.zip){:download}

!!! info "QMAP NL"
    De boeien en bakens in de QMAP-NL vectorkaart zijn die van de originele ENC en niet van de aparte dataset. De schaal/gebruiksband van de kaart is aangepast om goed weer te geven in AvNav, het werkt niet out of the box bij het converteren van de kaarten met OpenCPN.

## [OpenCPN](https://opencpn.org/)

OpenCPN en andere applicaties kunnen rasterkaarten van `mbtiles` weergeven.

- [:de: QMAP DE](qmap-de.png.mbtiles){:download}
- [:nl: QMAP NL](qmap-nl.png.mbtiles){:download}
- Vectorkaarten: zie hierboven

!!! info
    OpenCPN ondersteunt WebP niet, dus er zijn aparte `mbtiles` bestanden met png tiles.

## [JOSM](https://josm.openstreetmap.de/)

De rasterkaarten kunnen aan JOSM worden toegevoegd als [achtergrondlaag](https://josm.openstreetmap.de/wiki/Help/Preferences/Imagery).

- :de: QMAP DE `tms:https://freenauticalchart.net/qmap-de/{zoom}/{x}/{y}.png`
- :nl: QMAP NL `tms:https://freenauticalchart.net/qmap-nl/{zoom}/{x}/{y}.png`

Je wilt misschien ook [deze extra `mapcss`](https://josm.openstreetmap.de/wiki/Help/Preferences/MapPaintPreference) toevoegen (als laatste item) voor verbeterde rendering van zeeteken.

- `https://raw.githubusercontent.com/quantenschaum/mapping/refs/heads/icons/extra.mapcss`

## Garmin

Er is **experimentele** ondersteuning voor Garmin-toestellen. Het bestand bevat alleen dieptegegevens en boeien/bakens, het kan worden gecombineerd met gegevens van [bbbike](https://extract.bbbike.org/?format=garmin-oseam.zip). Het kan nodig zijn om peilingen en zeekleuren in te schakelen in de kaartinstellingen.

- [:de: Dieptegegevens DE](gmapsupp.img){:download}

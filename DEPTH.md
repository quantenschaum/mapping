# Depth Data and Rendering

see it in action: https://www.youtube.com/watch?v=TFhysaS7wj8 

## TL;DR - How to get good depth data in OsmAnd

To install the following files, download them to your phone and open them with OsmAnd (just tap and select OsmAnd).

- install and enable the [marine map style](marine.render.xml)
- install [depth rendering style](depthcontourlines.addon.render.xml) (replace!)
- install [OBFs containing depth data](https://github.com/quantenschaum/mapping/releases)

Download the files from the [releases](https://github.com/quantenschaum/mapping/releases).

:exclamation: This only works correctly with [render engine](https://osmand.net/docs/user/personal/global-settings/#map-rendering-engine) 2 and the render styles mentioned above!

### Settings

The custom render styles offer some config option, which can be use to adjust the look to your personal preferences.

- [additional settings](USAGE.md#additional-settings)
- hide
  - spot soundings
  - depth contours
  - depth areas
- nautical depth
  - line width
  - line color scheme
- dashed depth contours
- depth area color scheme
- spot sounding size
- spot sounding distance
- safety depth contour

The safety contour settings allows to choose a contour line (must be in the dataset!) that is drawn in red and depth areas below this depth get an overlay red hatched overlay.

Here an example of paper style areas, dashed contours and a 2m safety line.

![depth rendering](img/depth.png)

## Data Sources

IMHO the depth data supplied by OsmAnd is just a proof of concept showcase, they are very inaccurate and unreliable ([where do they come from?](https://github.com/osmandapp/OsmAnd/discussions/12502)) and not at all usable for actual navigation or trip planning.

### Germany 🇩🇪

The BSH provides access to nautical data in the [GeoSeaPortal](https://www.bsh.de/EN/DATA/GeoSeaPortal/geoseaportal_node.html). There is no documentation, but simply by examining what the webviewer does reveals some [WMS](https://en.wikipedia.org/wiki/Web_Map_Service) endpoints. Depth contours and areas can be found in

- https://gdi.bsh.de/mapservice_gs/NAUTHIS_Hydrography/ows
- https://gdi.bsh.de/mapservice_gs/NAUTHIS_SkinOfTheEarth/ows

 What is particularly nice is, that the data can be downloaded as `application/json;type=geojson`, so we can pull vector data from this server! You can download the entire dataset in one go.

BTW: They also provide a [tidal current atlas](https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas) for free! In the webviewer you cannot select the time before/after HW, but if you use [QGIS](https://www.qgis.org/) as WMS client, you can explore the datasets and switch between different times.

- https://www.geoseaportal.de/wss/service/Gezeitenstrom_Nordsee/guest
- https://www.geoseaportal.de/wss/service/Gezeitenstrom_Kueste/guest

### Netherlands 🇳🇱

RWS provides a full [ENC](https://en.wikipedia.org/wiki/Electronic_navigational_chart) with contours and spot soundings for free for some regions of NL like the Waddenzee and Zeeland.

- https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc

Using [GDAL](https://gdal.org/programs/ogr2ogr.html) the vector data can be extracted from the ENC.

### United States 🇺🇸

[NOAA provides ENCs](https://charts.noaa.gov/ENCs/ENCs.shtml) for free!

## OBF Generation

I managed to create an OBF containing depth contours and spot soundings. The workflow is roughly like this:

- download raw data (GeoJSON, ENC, ...)
- convert to format readable by QGIS (if necessary)
- import into [QGIS](https://www.qgis.org/)
- filter the relevant rows
- fix, dissolve, difference, merge as necessary
- add fields (tags)
  - spot soundings
    - `point=depth`
    - `depth=<DEPTH>`
  - contour lines 
    - `contour=depth`
    - `depth=<DEPTH>`
    - `contourtype=[5m,10m,20m,50m,100m,...]` (see below)
  - contour areas 
    - `contourarea=depth`
    - `areatype=[0,2,5,10,999]` (see below)
- export layer as geopackage only containing the added columns
- import into [JOSM](https://josm.openstreetmap.de/) via [OpenData](https://wiki.openstreetmap.org/wiki/JOSM/Plugins/OpenData) plugin
- save as [OSM XML](https://wiki.openstreetmap.org/wiki/OSM_XML) file
- convert OSM to [OBF](https://osmand.net/docs/technical/osmand-file-formats/osmand-obf/) using [OsmAndMapCreator](https://osmand.net/docs/versions/map-creator/)

Terrible, no command line tools, but it works.

### Lines and Areas

There are 5 contour areas identified by tag `areatype`.

- `0` - drying heights <0m (green)
- `2` - shallow water <2m (dark blue)
- `5` - shallow water <5m (blue)
- `10` - water <10m (light blue)
- `999` - deep water >10m (white)

```
areatype=
if(drval2<=0,0,
if(drval2<=2,2,
if(drval2<=5.4,5,
if(drval2<=10,10,
999))))
```

There are 15 types of contour lines identified by tag `contourtype`.

- dedicated values (line of exactly this value)
  - `0m` 
  - `1m` 
  - `2m` 
  - `3m` 
  - `4m` 
  - `5m` 
  - `10m`
  - `20m`
  - `50m`
- intervals (value of line is multiple of this number)
  - `-1` - drying heights
  - `1` 
  - `5`  
  - `10` 
  - `100m` - suffix `m` for compatibility with old rendering style 
  - `1000m` - suffix `m` for compatibility with old rendering style 

```
contourtype=
if(depth<0,'-1',
if(depth in (0,1,2,3,4,5,10,20,50),to_string(depth)+'m',
if(depth%1000=0,'1000m',
if(depth%100=0,'100m',
if(depth%10=0,'10',
if(depth%5=0,'5',
if(depth=1.8,'2m',
if(depth=5.4,'5m',
if(depth=9.1,'10m',
if(depth=18.2,'20m',
'1'))))))))))
```

Coloring and zoom levels at which the lines and areas appear are assigned in [`depthcontourlines.addon.render.xml`](depthcontourlines.addon.render.xml).

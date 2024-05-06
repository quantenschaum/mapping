[<< Back to Chart](..)

# Chart Files

[This project on GitHub](https://github.com/quantenschaum/mapping)

Here you find precompiled charts for download in various formats usable in different applications.

## [OsmAnd](https://osmand.net/)

### Vector Charts

![vector chart](vector.png)

Vector charts and styles for OsmAnd can be installed by simply opening the `obf` or `xml` file with the OsmAnd app, it will automatically import the file and use it as part of the "offline vector chart".

- [QMAP Germany](qmap-de.obf)
- [Depth Contours Germany](depth-de.obf)
- [Depth Data Netherlands](depth-nl.obf)
- [Light Sectors Worldwide](lightsectors.obf)

To make full use of the data in these files in form of a [nautical chart](https://osmand.net/docs/user/plugins/nautical-charts/), you
**must** use render engine 2, the [boating profile](https://osmand.net/docs/user/personal/profiles/) and also have to
**install and activate ** the following [rendering styles](https://osmand.net/docs/user/map/vector-maps) and enable the display of [nautical depth](https://osmand.net/docs/user/plugins/nautical-charts#depth-contours). When installing the rendering styles, choose "replace" when asked.

- [Marine Rendering Style](marine.render.xml)
- [Depth Data Rendering Style](depthcontourlines.addon.render.xml)

### Raster Charts

![raster chart](raster.png)

OsmAnd also allows the use of [raster charts](https://osmand.net/docs/user/map/raster-maps) via the [online maps plugin](https://osmand.net/docs/user/plugins/online-map/). The charts are imported by opening the `sqlitedb` files with the app. You can use them as base map or as an [overlay](https://osmand.net/docs/user/map/raster-maps#overlay-layer).

- [QMAP Germany](qmap-de.sqlitedb)
- [QMAP Netherlands](qmap-nl.sqlitedb)

## [AvNav](https://www.wellenvogel.net/software/avnav/docs/beschreibung.html)

AvNav uses raster charts in form of [GEMF](https://www.wellenvogel.net/software/avnav/docs/charts.html#chartformats) files. Simply drop the files into AvNav's `charts` folder.

- [QMAP Germany](qmap-de.gemf)
- [QMAP Netherlands](qmap-nl.gemf)

## [OpenCPN](https://opencpn.org/)

OpenCPN and other applications can display raster charts from `mbtiles`.

- [QMAP Germany](qmap-de.mbtiles)
- [QMAP Netherlands](qmap-nl.mbtiles)
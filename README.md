# S57 ENC conversion

How to convert an electronic navigational chart to map tiles and how to use them to update OSM data.

I will describe the procdure I used to update the buoys in the Waddenzee. The necessary commands are stored in the `makefile`, which is in the [ZIP](convert.zip) with all other resources.

1. download ENC from https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
2. extract the ZIP `make unzip`
3. convert the ENC to shape files with [`ogr2ogr`](https://gdal.org/programs/ogr2ogr.html) `make waddenzee` (It uses the mapping CSVs from OpenCPN.)
4. open them in [QGIS](https://www.qgis.org/) using `waddenzee.qgs`
5. export map tiles
  - processing, toolbox, raster tools, generate XYZ tiles (dir)
  - extent: draw on canvas and select the region you want to get rendered
  - max zoom: 16
  - set output dir and output html
  - run - this takes a while :coffee:

Then you can open the HTML file and view the tiles in your browser using [leaflet](https://leafletjs.com/).

I edit OSM data with [JOSM](https://josm.openstreetmap.de/). You can add the generated map tiles to JOSM as imagery layer.

- imagery, imagery preferences
- add TMS with `tms:file:///path/to/qgis/tiles/{zoom}/{x}/{y}.png` 
- the activate the layer from imagery menu

JOSM is pretty easy to use, how it works is explained in the [Wiki](https://josm.openstreetmap.de/wiki/Introduction). For editing seamarks you may want to set a filter filtering on `seamark` and activate hide mode, such that only seamarks are displayed to make it less confusing.

You may want to add the INT1 `icons` path to QGIS in the settings (settings, options, system, SVG path).

The ENC files can be viewed directly in [OpenCPN](https://opencpn.org/).

The tiles can also be used in [OSMAND](https://osmand.net/), an IMHO very good mobile map and navigation app for Adroid devices.

You should also have a look into

- https://appchart.c-map.com/
- https://webapp.navionics.com/


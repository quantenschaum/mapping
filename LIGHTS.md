# Rendering of Sector Lights

Currently, it is [not possible to render light sectors](https://github.com/osmandapp/OsmAnd/issues/16894) directly in OsmAnd.

The workaround to get light sector displayed is to create dedicated lines for the sector limits and sector arcs based on the [attributes of sector lights](https://wiki.openstreetmap.org/wiki/Seamarks/Lights#Sectored_light_attributes) in the OSM database. 

The procedure is as follows:

- download OSM data with JOSM (filter for lights only)
- save as OSM XML file
- run [lightsectors.py](lightsectors.py) on this file
- review the output file in JOSM (optional)
- generate an OBF with the [OsmAndMapCreator](https://osmand.net/docs/versions/map-creator) using these [rendering_types.xml](rendering_types.xml) from the output file

:exclamation: The sectors in this OBF are displayed in OsmAnd with the [marine style](marine.render.xml) only.

Example OBFs can be found in the [releases](https://github.com/quantenschaum/mapping/releases).

In OsmAnd light sectors look like this.

![light sectors](img/lightsectors.png)
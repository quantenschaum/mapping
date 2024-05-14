# Rendering of Sector Lights

Currently, it is [not possible to render light sectors](https://github.com/osmandapp/OsmAnd/issues/16894) directly in OsmAnd.

The workaround to get light sectors displayed is to create dedicated lines for the sector limits and sector arcs based on the [attributes of sector lights](https://wiki.openstreetmap.org/wiki/Seamarks/Lights#Sectored_light_attributes) in the OSM database. 

The procedure is as follows:

- download OSM data with [JOSM](https://josm.openstreetmap.de/) (use [overpass](https://overpass-turbo.eu/) to filter for lights only)
- save as OSM XML file
- run [lightsectors.py](lightsectors.py) on this file
- review the output file in JOSM (optional)
- generate an OBF with the [OsmAndMapCreator](https://osmand.net/docs/versions/map-creator) using these [rendering_types.xml](rendering_types.xml) from the output file

:exclamation: The sectors in this OBF are displayed in OsmAnd with the [marine style](marine.render.xml) only. The sections in `marine.render.xml` and in `rendering_types.xml` responsible for light sector rendering can be found by searing for `lightsector`.

There are custom settings in the hide section of the map config to hide

- *light sectors* - hides the sector limits and arcs 
- *light sector sources* - hides light source icons, the label is still displayed

The icons and labels have a higher render priority and get displayed above other icons/labels, so you might want to hide the *light sector sources* to be able to see the actual beacon/lighthouse icon.

The script creates

- a colored arc for the sector with characteristics label
- lines at sector limits with bearing label
- a colored line for directional lights with bearing and characteristics label
- a marker at the light source with characteristics label

:point_right: An OBF can be found in the [download section](index.md#vector-charts).

In OsmAnd light sectors look like this.

![light sectors](img2/lightsectors.png)

overpass query

```
[out:xml][timeout:90];
(  
  nwr["seamark:type"="light_major"];   
  nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:range"]; 	  
  nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:1:range"];  
);
(._;>;);
out meta;
```

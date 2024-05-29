# Tidal Atlas

The BSH provides tidal current data for the North Sea, the Channel and the Germany Bight (higher resolution).
The presentation of this data in the [GeoSeaPortal](https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas) is not very usable, you can neither select the dataset nor the hour of the tide, so it's pretty useless. But the raw data is available at <https://data.bsh.de/OpenData/Main/>.

I used QGIS to render the average tidal current field and added annotations for set and drift, so you can choose the hour of the tide, depending on the zoom level you get an overview of the tidal current, and you can directly read off set and drift at the desired position (when zoomed in).

![tides overview](img/tides1.png)

![tides detail](img/tides2.png)

The chart looks as shown above. The slider is used to select the hour before/after high water at Helgoland. The arrows in size and color show average set and drift, The number below the arrow is the average set (direction), the numbers above the arrow are the drift (velocity) in 10th of a knot at neaps (before the dot) and at springs (after the dot).

![tide figures](img/tide-figures.png)

When the slider is set to `Figures`, all tide arrows are shown simultaneously revealing the tide figure for the location. The numbers are the hour before/after HW.

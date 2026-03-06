# Printing Charts

There are multiple ways to print a chart. You can print the raster data directly from your browser (quick and easy) or print vector data from QGIS (better quality but more involved).

![exported chart image](img/chartimage.webp)

## Printing from Browser

1. Open the chart in the browser (works best in Chrome based browsers).
2. Click on the print layout button somewhere at the top left and select the desired target paper format and orientation.
3. Adjust zoom and position of the chart to your liking. 
4. Now print the chart (ctrl+p). In the print dialogue 
     - select the right paper size and orientation
     - set margins to none or zero or minimal
     - the chart should be centered on a single page
5. Print!

!!! tip "zoom level and symbol size"
    With an active print layout you may zoom out half a zoom step to fit some more content of the map and make the text and symbols appear smaller without actually switching to another zoom level.
    
!!! hint "print to PDF"
    You may print to PDF instead of printing directly on paper. This way you can save chart for printing it again later. It also allows you to print the chart to an A3 PDF, which can be printed downscaled onto A4. This makes a higher resolution print, but with smaller text and symbols.
    
    Printing PDFs is generally more reliable than printing directly from apps. Often there is better control of the printer and more options available. So, if printing directly from the browser fails, try to print to PDF and then print the PDF from your PDF viewer.

!!! hint "Paper and Ink"
    It is highly recommended to use a laser printer because toner is water-resistant. Ink from inkjet printers is generally not water-resistant and can run when exposed to water, which may render the print unusable. There is also waterproof paper made from treated cotton or synthetic materials that is suitable for laser printers; using this produces a water-resistant print.

### Image export

With the arrow button in the print widget on the top left you can export the currently shown map as an image file. You can resize the browser window to the desired size before the export, or you can select a predefined print layout.

This is useful for creating screenshots of the map like above without the control elements but including the lat/lon borders.
 
## Printing from QGIS

You can use QGIS to create a chart [like this one](img/paperchart.pdf).

You can print your own custom charts with the classical lat/lon zebra border as follows.

1. Install [QGIS](https://qgis.org/) on your computer.
2. Download the [raw data](index.md) containing all necessary file.
3. Unzip the data package.
4. Open `bsh.qgs` with QGIS.
5. Select `Project > Layout Manager`.
6. Doubleclick the `paperchart` layout and the layout editor will open.
7. Adjust the layout to your liking, select the part of the map you want to print (use the move content tool (C)).
8. Export as PDF.
9. Print the PDF (direct printing from QGIS may work, but printing PDF is usually more reliable and you can save it to print it again).


## Large formats

It is possible to print maps in sizes larger than A4. Since most users usually only have an A4 printer, the map can be printed across several A4 sheets and then glued together into a larger map. Proceed as follows.

1. Create the map to be printed as a one-page PDF in the desired size. Pay attention to the resolution and the size of fonts and symbols for the target format. For best quality use QGIS or choose a sufficiently large format (the map may not be fully visible on screen; use Ctrl-Minus to zoom out, Ctrl-0 to reset to 100%) and print to PDF. Set the paper size and margins accordingly.
2. Split this PDF across multiple A4 sheets. Some PDF viewers can do this natively, or you can use [this script](https://github.com/quantenschaum/mapping/blob/master/scripts/poster.py) (requires Linux, Python, pdfposter, LaTeX). With the `-p` option you can specify the number of pages, e.g. `-p 4x2` distributes the map onto 4x2=8 sheets, which is approximately A1 (slightly smaller due to overlapping glue seams).
3. Print the pages, making sure to disable any automatic scaling in the printer settings.
4. Trim the bottom and right margins of each sheet using the crop marks.
5. Glue the sheets together to form the full map.

!!! example "Example map"
    The following example shows the Elbe estuary, once generated from the browser as an A1 PDF and distributed across 4x2 A4 sheets, and once generated from QGIS.

    - Browser (raster image)
        - [Example map A1, single page](img/FreeNauticalChart.pdf)
        - [Example map A1, 4x2 A4](img/FreeNauticalChart.4x2.pdf)
    - QGIS (vector graphic, high quality)
        - [Example map A1, single page](img/paperchart.A1.pdf)
        - [Example map A1, 4x2 A4](img/paperchart.4x2.pdf)

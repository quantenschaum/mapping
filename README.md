# Free Nautical Charts

Conversion of chart data from different sources to create free nautical charts.

:point_right: [Documentation](https://freenauticalchart.net/download/)

![example map](docs/img/chartimage.webp)

> **Not for navigation.** The charts and data are for information, reference and
> training only. See the [disclaimer](https://freenauticalchart.net/download/#important-information)
> and the [legal notice](docs/legal.md).

## What this project does

This repository contains the scripts, styles and build files behind
[freenauticalchart.net](https://freenauticalchart.net/). It takes open data for
German and Dutch waters, converts it and publishes:

- raster charts (`mbtiles`, `sqlitedb`) for AvNav, OpenCPN, OsmAnd and JOSM
- S-57 vector charts (`zip`) for AvNav (Ocharts NG plugin) and OpenCPN
- OsmAnd files (`obf`): depth data, light sectors and the marine rendering style
- the [web chart](https://freenauticalchart.net/) and its [vector version](https://freenauticalchart.net/vector/)
- tide curves, a tidal atlas and printable charts

Ready-made files are on the [download page](https://freenauticalchart.net/download/),
with instructions for each app.

## Data sources

- Germany: [BSH](https://www.bsh.de/) (Bundesamt für Seeschifffahrt und Hydrographie).
  Parts of the BSH data are no longer freely available, so the German chart is now
  based on older data; see the warning on the download page.
- Netherlands: [Rijkswaterstaat](https://www.rijkswaterstaat.nl/) (ENC, buoys and beacons).

The full list of sources and their licences is on the
[download page](https://freenauticalchart.net/download/). Background on using BSH
data (in German): [BSH.md](BSH.md) and [opendata.md](opendata.md).

## Licence

- Code: [GPL-3.0](LICENSE)
- Charts and other downloadable files: [CC0](https://creativecommons.org/publicdomain/zero/1.0/)

## Repository layout

- `docs/` documentation site (MkDocs, English, German and Dutch)
- `scripts/` Python tools for converting S-57, BSH and RWS data, tiles and light sectors
- `qgis/` QGIS projects used to render the raster charts
- `mapproxy/` MapProxy configuration for serving and seeding raster tiles
- `web/` the web chart (Vite, Leaflet, MapLibre)
- `vector/` the vector chart: tiles, styles and sprites (tippecanoe, pmtiles, MapLibre)
- `osmand/` OsmAnd rendering style and map creation settings
- `tides/` tidal atlas and tide curves (see [tides/README.md](tides/README.md))
- `garmin/` Garmin map style
- `icons/` chart symbols
- `www/` output folder for the website

## Building

The full build downloads a lot of data and takes a long time. It is written for Linux.

Tools used by the makefiles:

- `make`, `wget`, `jq`, GNU `parallel`, `zipmerge` (libzip)
- Python 3 with the packages in `scripts/requirements.txt`
- GDAL (`ogr2ogr`) and SpatiaLite
- QGIS Server and MapProxy (or Docker, see below)
- Node.js with `npm` (web chart) and `pnpm` (vector chart)
- Java (OsmAnd map creator)
- MkDocs and its plugins (`cd docs && make install`)
- for `vector/`: `make -C vector tools` builds tippecanoe, pmtiles and spreet
  from source (needs Go, Rust and a C++ compiler)

Main `make` targets:

- `make build` full build: data, charts, tiles, vector charts and the website
- `make docker`, `make docker-seed` run QGIS Server and MapProxy in Docker and seed the tile cache
- `make qgis`, `make mapproxy`, `make seed` the same without Docker
- `make web` build the web chart into `www/`
- `make www` build the documentation into `www/download/`
- `make serve` serve `www/` locally on port 8002
- `cd docs && make serve` preview the documentation while editing

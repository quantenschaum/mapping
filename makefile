# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash

help:
	cat README.md


vwm:
	mkdir -p data/$@
	wget -O data/$@/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O data/$@/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"

BSHWMS=https://gdi.bsh.de/mapservice_gs/NAUTHIS_$$L/ows

bsh:
	rm -rf data/$@
	mkdir -p data/$@
	for L in AidsAndServices SkinOfTheEarth; do wget -O data/$@/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done
	for L in RocksWrecksObstructions; do wget -O data/$@/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done
	for L in Hydrography Topography; do wget -O data/$@/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=1_Overview,2_General,3_Coastel,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done
	rm -f data/$@.sqlite
	for F in $$(find data/$@/ -name "*.json"); do $(OGR_OPTS) ogr2ogr data/$@.sqlite $$F -append -dsco SPATIALITE=YES; done

us-encs:
	rm -rf data/$@
	mkdir -p data/$@
	for I in 01 05 07 08 09 11 13 14 17; do wget -O data/$@/$${I}CGD_ENCs.zip https://charts.noaa.gov/ENCs/$${I}CGD_ENCs.zip; done

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

%.sqlite: s57attributes.csv s57objectclasses.csv
	rm -f $@
	for F in $$(find $(basename $@)/ -name "*.000"); do $(OGR_OPTS) ogr2ogr $@ $$F -append -dsco SPATIALITE=YES; done

waddenzee:
	rm -rf data/$@
	cd data && unzip *Waddenzee*.zip && mv *Waddenzee*/ waddenzee
	$(MAKE) data/$@.sqlite

marrekrite.gpx:
	wget -O data/$@ "https://github.com/marcelrv/OpenCPN-Waypoints/raw/main/Marrekrite-Aanlegplaatsen.gpx"

tides:
	mkdir data/$@ -p
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Nordsee/Gezeitenstrom_Nordsee.zip -O data/$@/Nordsee.zip
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Kueste/Gezeitenstrom_Kueste.zip   -O data/$@/Kueste.zip


bsh.osm: empty.osm
	for L in buoys beacons facil lights; do ./update.py bsh-$$L data/bsh/AidsAndServices.json $< bsh-$$L.osm -a; done
	for L in rocks wrecks obstructions; do ./update.py bsh-$$L data/bsh/RocksWrecksObstructions.json $< bsh-$$L.osm -a; done
	for L in seabed; do ./update.py bsh-$$L data/bsh/Hydrography.json $< bsh-$$L.osm -a; done
	for L in beacons facil lights; do ./lightsectors.py bsh-$$L.osm bsh-$$L-sectors.osm -j; done








.PHONY: nautical.render.xml render.diff marine.render.xml

nautical.render.xml:
	wget -O $@ https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

render.diff:
	diff nautical.render.xml marine.render.xml -u >$@ || true

marine.render.xml:
	cp nautical.render.xml $@
	patch $@ render.diff

replace:
	for F in *.qgs; do echo $$F; sed 's#"INT1/#"./icons/INT1/#g' $$F -i; done

serve:
	xdg-open "http://localhost:8080/index.html#ondemand"
	cd tiles && python -m http.server 8080

qgis: replace
	QGIS_SERVER_ADDRESS=0.0.0.0 qgis_mapserver map.qgs & mapproxy-util serve-develop mapproxy.yaml -b 0.0.0.0:8001 & $(MAKE) serve

wait:
	sleep 60

upload:
	touch tiles/.nobackup
	rsync -hav tiles/ nas:docker/maps/tiles/qgis/ $(O)

sync: replace
	#rsync -hav --del --exclude tiles --exclude cache_data --exclude .git --delete-excluded ./ nas:docker/qgis $(O)
	rsync -hav --del map.qgs mapproxy.yaml marrekrite.gpx Dockerfile shapes bsh vwm icons nas:docker/qgis $(O)


data/josm.jar:
	wget -O $@ https://josm.openstreetmap.de/josm-tested.jar

josm: data/josm.jar
	java -jar $<


data/omc:
	wget -O $@.zip https://download.osmand.net/latest-night-build/OsmAndMapCreator-main.zip
	unzip $@.zip -d $@

omc: data/omc
	$</OsmAndMapCreator.sh
	mv -v data/omc/*obf data/obf/


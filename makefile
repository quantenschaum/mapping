# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR=OGR_S57_OPTIONS="RETURN_PRIMITIVES=ON,RETURN_LINKAGES=ON,LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)" ogr2ogr -skipfailures

help:
	cat README.md

us-encs:
	for I in 01 05 07 08 09 11 13 14 17; do wget https://charts.noaa.gov/ENCs/$${I}CGD_ENCs.zip; done

unzip:
	for Z in *.zip; do unzip -o "$$Z"; done
	touch */ENC_ROOT/.nobackup

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

.PHONY: nautical.render.xml render.diff marine.render.xml vwm bsh

nautical.render.xml:
	wget -O $@ https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

render.diff:
	diff nautical.render.xml marine.render.xml -u >$@ || true

marine.render.xml:
	cp nautical.render.xml $@
	patch $@ render.diff

vwm:
	mkdir -p $@
	wget -O $@/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O $@/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"

OUT=shapes

convert: s57objectclasses.csv s57attributes.csv
	#rm -rf $(OUT)
	mkdir -p $(OUT)
	for F in $(IN)/*.000; do $(OGR) $(OUT) "$$F"; done
	#cd $(OUT) && rm *.prj *.shx *.dbf
	cd $(OUT) && for F in * ; do G=$${F%.*}; mv -n $${F} $${G^^}.$${F#*.}; done
	touch $(OUT)/.nobackup

shapes:
	$(MAKE) convert IN=*U7Inland_*/ENC_ROOT/*/*/*/

DIS=01

us-shapes:
	mkdir us -p
	touch us/.nobackup
	unzip $(DIS)CGD_ENCs.zip -d us/GCD$(DIS)
	$(MAKE) convert OUT=us/GCD$(DIS)/shapes3 IN=us/GCD$(DIS)/ENC_ROOT/US3*
	$(MAKE) convert OUT=us/GCD$(DIS)/shapes4 IN=us/GCD$(DIS)/ENC_ROOT/US4*
	$(MAKE) convert OUT=us/GCD$(DIS)/shapes5 IN=us/GCD$(DIS)/ENC_ROOT/US5*

replace:
	for F in *.qgs; do echo $$F; sed 's#"INT1/#"./icons/INT1/#g' $$F -i; done

bsh0:
	mkdir -p bsh

	for L in AidsAndServices Hydrography SkinOfTheEarth RocksWrecksObstructions Topography; do wget -O bsh/$$L.json "https://www.geoseaportal.de/wss/service/NAUTHIS_$$L/guest?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done

BSHWMS=https://gdi.bsh.de/mapservice_gs/NAUTHIS_$$L/ows

bsh:
	mkdir -p bsh

	for L in AidsAndServices SkinOfTheEarth; do wget -O bsh/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done

	for L in RocksWrecksObstructions; do wget -O bsh/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done

	for L in Hydrography Topography; do wget -O bsh/$$L.json "$(BSHWMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=1_Overview,2_General,3_Coastel,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done

serve:
	xdg-open "http://localhost:8080/index.html#ondemand"
	cd tiles && python -m http.server 8080

qgis: replace
	QGIS_SERVER_ADDRESS=0.0.0.0 qgis_mapserver map.qgs & mapproxy-util serve-develop mapproxy.yaml -b 0.0.0.0:8001 & $(MAKE) serve

docker: replace
	docker-compose up & $(MAKE) serve

clean-tiles:
	rm -rf tiles/*/

clean-enc:
	rm -rf *U7Inland_*/

clean-shapes:
	rm -rf shapes/

clean-bsh:
	rm -rf bsh/

clean-vwm:
	rm -rf vwm/

clean-cache:
	rm -rf cache_data/

clean-all: clean-tiles clean-shapes clean-enc clean-bsh clean-vwm clean-cache

wait:
	sleep 60

upload:
	touch tiles/.nobackup
	rsync -hav tiles/ nas:docker/maps/tiles/qgis/ $(O)

sync: replace
	#rsync -hav --del --exclude tiles --exclude cache_data --exclude .git --delete-excluded ./ nas:docker/qgis $(O)
	rsync -hav --del map.qgs mapproxy.yaml marrekrite.gpx Dockerfile shapes bsh vwm icons nas:docker/qgis $(O)


josm.jar:
	wget -O $@ https://josm.openstreetmap.de/josm-tested.jar

josm: josm.jar
	java -jar josm.jar

marrekrite.gpx:
	wget -O $@ "https://github.com/marcelrv/OpenCPN-Waypoints/raw/main/Marrekrite-Aanlegplaatsen.gpx"

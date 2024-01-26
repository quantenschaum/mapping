# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR_OPTS=OGR_S57_OPTIONS="RETURN_PRIMITIVES=ON,RETURN_LINKAGES=ON,LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)"

.PHONY: nautical.render.xml render.diff marine.render.xml bsh.osm data/vwm data/bsh icons obf

help:
	cat README.md

vwm: data/vwm #data/vwm.sqlite

data/vwm:
	mkdir -p $@
	wget -O $@/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O $@/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"
	#for F in $@/*.json; do jq . $$F>$@/tmp; mv $@/tmp $$F; done
	for F in $$(find $@ -name "*.json"); do ogr2ogr $${F/.json/.gpkg} $$F; done

BSH_WMS=https://gdi.bsh.de/mapservice_gs/NAUTHIS_$$L/ows
BSH_LAYERS_1=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
# need this because there is a typo in the WMS layer name (coastel)
BSH_LAYERS_2=1_Overview,2_General,3_Coastel,4_Approach,5_Harbour,6_Berthing
# no overview layer for obstructions
BSH_LAYERS_3=2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
BSH_BBOX=53,3.3,56,14.4

bsh: data/bsh #data/bsh.sqlite

data/bsh:
	rm -rf $@
	mkdir -p $@
	for L in AidsAndServices SkinOfTheEarth; do wget -O $@/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_1)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in RocksWrecksObstructions; do wget -O $@/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_3)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in Hydrography Topography; do wget -O $@/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_2)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	#for F in $@/*.json; do jq . $$F>$@/tmp; mv $@/tmp $$F; done
	for F in $$(find $@ -name "*.json"); do ogr2ogr $${F/.json/.gpkg} $$F; done

CGDS=01 05 07 08 09 11 13 14 17
CGDS=01

data/us:
	rm -rf $@
	mkdir -p $@
	for I in $(CGDS); do wget -O $@/$${I}CGD_ENCs.zip https://charts.noaa.gov/ENCs/$${I}CGD_ENCs.zip; done
	for F in $@/*.zip; do unzip $$F -d $@; done

us: data/us
	$(MAKE) data/$@.sqlite
	$(MAKE) data/$@.json

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

ENC_LAYERS1=BOYLAT BOYCAR BOYISD BOYSAW BOYSPP BOYINB BCNLAT BCNCAR BCNISD BCNSAW BCNSPP TOPMAR DAYMAR LIGHTS RTPBCN LNDMRK FOGSIG PILPNT UWTROC WRECKS OBSTRN OFSPLF SBDARE HRBFAC SMCFAC
ENC_LAYERS2=DEPARE DEPCNT SOUNDG M_COVR

%.sqlite: s57attributes.csv s57objectclasses.csv
	rm -f $@*
	for F in $$(find $(basename $@) -name "*.000"); do echo $$F; $(OGR_OPTS) ogr2ogr $@ $$F $(ENC_LAYERS1) $(ENC_LAYERS2) -skipfailures -append $(OGR_OPTS2); done

%.json: %.sqlite
	for L in $(ENC_LAYERS1); do rm -f $(basename $@)/$$L.json; echo $$L; ogr2ogr $(basename $@)/$$L.json $< $$L; done
	#for F in $(basename $@)/*.json; do echo $$F; jq . $$F>tmp; mv tmp $$F; done

%/shapes: %/
	rm -f $@/*
	for F in $$(find $< -name "*.000"); do echo $$F; $(OGR_OPTS) ogr2ogr $@ $$F $(ENC_LAYERS1) $(ENC_LAYERS2) -skipfailures -append $(OGR_OPTS2); done
	#for L in $(ENC_LAYERS1); do rm -f $</$$L.json; echo $$L; ogr2ogr $</$$L.json $@/$$L.shp $$L; done

waddenzee:
	rm -rf data/$@
	cd data && unzip *Waddenzee*.zip && mv *Waddenzee*/ waddenzee
	$(MAKE) data/$@.sqlite
	$(MAKE) data/$@.json

marrekrite.gpx:
	wget -O data/$@ "https://github.com/marcelrv/OpenCPN-Waypoints/raw/main/Marrekrite-Aanlegplaatsen.gpx"

tides:
	mkdir data/$@ -p
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Nordsee/Gezeitenstrom_Nordsee.zip -O data/$@/Nordsee.zip
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Kueste/Gezeitenstrom_Kueste.zip   -O data/$@/Kueste.zip









nautical.render.xml:
	wget -O $@ https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

rendering_types0.xml:
	wget -O $@ https://github.com/osmandapp/OsmAnd-resources/raw/master/obf_creation/rendering_types.xml

render.diff:
	diff nautical.render.xml marine.render.xml -u >$@ || true

marine.render.xml:
	cp nautical.render.xml $@
	patch $@ render.diff

bsh1.qgs: bsh.qgs
	sed 's#<value>000000</value>#<value>1</value>#g' $< >$@

serve:
	cd tiles && python -m http.server 8002

qgis: icons bsh1.qgs
	QGIS_SERVER_PARALLEL_RENDERING=1 qgis_mapserver

mapproxy:
	mapproxy-util serve-develop mapproxy.yaml -b 0.0.0.0:8001

seed:
	mapproxy-seed -f mapproxy.yaml -s seed.yaml $(O)

clean-cache:
	rm -rf cache_data

docker:
	docker-compose up -d

upload:
	touch tiles/.nobackup
	rsync -hav tiles/ nas:docker/maps/tiles/qgis/ $(O)

data/josm.jar:
	wget -O $@ https://josm.openstreetmap.de/josm-tested.jar

josm: data/josm.jar
	java -jar $<


data/omc:
	mkdir -p data
	wget -O $@.zip https://download.osmand.net/latest-night-build/OsmAndMapCreator-main.zip
	unzip $@.zip -d $@

omc: data/omc
	$</OsmAndMapCreator.sh
	mv -v data/omc/*obf data/obf/

mobac:
	#java -Xms64m -Xmx1200M -jar data/mobac/Mobile_Atlas_Creator.jar
	java -jar data/mobac/Mobile_Atlas_Creator.jar

obf: data/omc
	mkdir -p $@
	java -cp "$$(ls $</*.jar)" net.osmand.util.IndexBatchCreator batch.xml
	for F in $@/*_2.obf; do G=$${F/_2./.}; G=$${G,,}; mv -v $$F $$G; done
	rm -f $@/*.log
	#cp -v $@/*.obf data/obf

icons: icons/gen

icons/gen:
	cd icons && ./genicons.py
	sed 's#icons/gen#https://raw.githubusercontent.com/quantenschaum/mapping/icons#g' extra.mapcss >icons/gen/extra.mapcss

lights:
	wget -O $@.osm 'https://overpass-api.de/api/interpreter?data=[out:xml][timeout:90];(  nwr[~"seamark:type"~"light"];  nwr["seamark:light:range"][~"seamark:type"~"landmark"];  nwr["seamark:light:range"][~"seamark:type"~"beacon"];  nwr["seamark:light:1:range"][~"seamark:type"~"landmark"];  nwr["seamark:light:1:range"][~"seamark:type"~"beacon"];);(._;>;);out meta;'
	./lightsectors.py $@.osm lightsectors.osm
	rm -rf osm
	mkdir -p osm
	cp lightsectors.osm osm
	$(MAKE) obf
	cp obf/lightsectors.obf data/obf/

bsh.osm:
	mkdir -p bsh
	for L in buoys beacons facilities lights stations; do ./update.py bsh-$$L data/bsh/AidsAndServices.json none bsh/$$L.osm -a; done
	for L in rocks wrecks obstructions; do ./update.py bsh-$$L data/bsh/RocksWrecksObstructions.json none bsh/$$L.osm -a; done
	for L in seabed; do ./update.py bsh-$$L data/bsh/Hydrography.json none bsh/$$L.osm -a; done
	for L in beacons facilities lights; do ./lightsectors.py bsh/$$L.osm bsh/$$L-sectors.osm; done

bsh.obf: bsh.osm
	rm -rf obf osm
	mkdir -p osm
	cp bsh/*.osm osm/
	$(MAKE) obf
	data/omc/inspector.sh -c obf/bsh.obf obf/*.obf
	cp obf/bsh.obf data/obf/
	rm -rf osm


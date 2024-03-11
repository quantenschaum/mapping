# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR_OPTS=OGR_S57_OPTIONS="RETURN_PRIMITIVES=ON,RETURN_LINKAGES=ON,LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)"

.PHONY: nautical.render.xml render.diff marine.render.xml bsh.osm icons obf vwm bsh

help:
	cat README.md

vwm:
	rm -rf data/vwm
	mkdir -p data/vwm
	wget -O data/vwm/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O data/vwm/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"
	#for F in data/vwm/*.json; do jq . $$F>data/vwm/tmp; mv data/vwm/tmp $$F; done
	for F in $$(find data/vwm -name "*.json"); do ogr2ogr $${F/.json/.gpkg} $$F; done

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

ENC_LAYERS=BOYLAT BOYCAR BOYISD BOYSAW BOYSPP BOYINB BCNLAT BCNCAR BCNISD BCNSAW BCNSPP TOPMAR DAYMAR LIGHTS RTPBCN LNDMRK FOGSIG PILPNT UWTROC WRECKS OBSTRN OFSPLF SBDARE HRBFAC SMCFAC DEPARE DEPCNT SOUNDG M_COVR
ENC_LAYERS=NAVLNE RECTRC OFSPLF FERYRT FAIRWAY PIPSOL PIPARE CBLSUB CBLARE SLCONS

waddenzee: s57attributes.csv s57objectclasses.csv
	rm -rf data/waddenzee data/waddenzee.gpkg
	cd data && unzip *Waddenzee*.zip && mv *Waddenzee*/ waddenzee
	for F in $$(find data/waddenzee -name "*.000"); do echo $$F; $(OGR_OPTS) ogr2ogr data/waddenzee.gpkg $$F $(ENC_LAYERS) -skipfailures -append; done

BSH_WMS=https://gdi.bsh.de/mapservice_gs/NAUTHIS_$$L/ows
BSH_LAYERS_1=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
# need this because there is a typo in the WMS layer name (coastel)
BSH_LAYERS_2=1_Overview,2_General,3_Coastel,4_Approach,5_Harbour,6_Berthing
# no overview layer for obstructions
BSH_LAYERS_3=2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
BSH_BBOX=53.0,3.3,56.0,14.4

bsh:
	rm -rf data/bsh data/bsh.gpkg
	mkdir -p data/bsh
	for L in AidsAndServices SkinOfTheEarth; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_1)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in RocksWrecksObstructions; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_3)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in Hydrography Topography; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_2)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	#for F in data/bsh/*.json; do jq . $$F>data/bsh/tmp; mv data/bsh/tmp $$F; done
	for F in $$(find data/bsh -name "*.json"); do ogr2ogr $${F/.json/.gpkg} $$F; done
	for F in $$(find data/bsh -name "*.json"); do ogr2ogr data/bsh.gpkg $$F -append; done

waypoints:
	mkdir -p data
	wget https://faq.nvdev.de/api/assets/9attdq0jedc0w08w -O data/waypoints.gpx

icons:
	cd icons && ./genicons.py
	sed 's#icons/gen#https://raw.githubusercontent.com/quantenschaum/mapping/icons#g' extra.mapcss >icons/gen/extra.mapcss

bsh1.qgs: bsh.qgs
	sed 's#<value>000000</value>#<value>1</value>#g' $< >$@

bsh2.qgs: bsh.qgs
	sed 's#<value>000000</value>#<value>2</value>#g' $< >$@

serve:
	cd tiles && python -m http.server 8002

qgis: icons bsh1.qgs bsh2.qgs
	QGIS_SERVER_PARALLEL_RENDERING=1 qgis_mapserver

mapproxy:
	mapproxy-util serve-develop mapproxy.yaml -b 0.0.0.0:8001

seed:
	mapproxy-seed -f mapproxy.yaml -s seed.yaml $(O)

convert: cache_data/bsh.mbtiles
	./tileconvert.py -yf $< qmap-de.mbtiles -t "QMAP DE `date +%F`" -Mminzoom=7 -Mmaxzoom=18 -Mbounds=3.3,53.0,14.4,56.0 -Mversion=`date +%F` -Mattribution=https://github.com/quantenschaum/mapping -Mdescription="navigational chart of german waters, north sea and baltic sea"
	./tileconvert.py -yf $< qmap-de.sqlitedb -t "QMAP DE `date +%F`"
	./tileconvert.py -ya $< tiles/enc/

convert-aton: cache_data/aton.mbtiles
	./tileconvert.py -yf $< aton-de.mbtiles -t "ATON DE `date +%F`" -Mminzoom=7 -Mmaxzoom=18 -Mbounds=3.3,53.0,14.4,56.0 -Mversion=`date +%F` -Mattribution=https://github.com/quantenschaum/mapping -Mdescription="aids to navigation in german waters, north sea and baltic sea"
	./tileconvert.py -yf $< aton-de.sqlitedb -t "ATON DE `date +%F`"
	./tileconvert.py -ya $< tiles/aton/

convert-depth: cache_data/depth.mbtiles
	./tileconvert.py -yf $< depth-de.mbtiles -t "DEPTH DE `date +%F`" -Mminzoom=7 -Mmaxzoom=18 -Mbounds=3.3,53.0,14.4,56.0 -Mversion=`date +%F` -Mattribution=https://github.com/quantenschaum/mapping -Mdescription="depth contours and obstructions in german waters, north sea and baltic sea"
	./tileconvert.py -yf $< depth-de.sqlitedb -t "DEPTH DE `date +%F`"
	./tileconvert.py -ya $< tiles/depth/

clean-cache:
	rm -rf cache_data

docker:
	docker-compose up -d

upload:
	touch tiles/.nobackup
	cp -v marine.render.xml tiles/download/
	cp -v qmap-de* aton-de* depth-de* tiles/download/ || true
	rsync -hav tiles/ nas:mapping/tiles/ --stats $(O)

vwm-update:
	#wget -O wad.osm '[out:xml][timeout:90][bbox:{{bbox}}];(  nwr[~"seamark:type"~"buoy"];  nwr[~"seamark:type"~"beacon"];  nwr["waterway"="fairway"];); (._;>;);out meta;'
	./update.py rws_buoys data/vwm/drijvend.json wad.osm















########################################################################################################################


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

bsh.osm:
	rm -rf osm
	mkdir -p osm
	for L in buoys beacons facilities lights stations; do ./update.py bsh-$$L data/bsh/AidsAndServices.json none osm/$$L.osm -a; done
	for L in rocks wrecks obstructions; do ./update.py bsh-$$L data/bsh/RocksWrecksObstructions.json none osm/$$L.osm -a; done
	for L in seabed; do ./update.py bsh-$$L data/bsh/Hydrography.json none osm/$$L.osm -a; done
	for L in beacons facilities lights; do ./lightsectors.py osm/$$L.osm osm/$$L-sectors.osm; done

bsh.obf: bsh.osm
	rm -rf obf
	$(MAKE) obf
	data/omc/inspector.sh -c obf/bsh.obf obf/*.obf

lightsectors.osm:
	rm -rf osm
	mkdir -p osm
	wget -O osm/lights.osm 'https://overpass-api.de/api/interpreter?data=[out:xml][timeout:90];(  nwr[~"seamark:type"~"light"];  nwr["seamark:light:range"][~"seamark:type"~"landmark"];  nwr["seamark:light:range"][~"seamark:type"~"beacon"];  nwr["seamark:light:1:range"][~"seamark:type"~"landmark"];  nwr["seamark:light:1:range"][~"seamark:type"~"beacon"];);(._;>;);out meta;'
	./lightsectors.py osm/lights.osm osm/$@

lightsectors.obf: lightsectors.osm
	$(MAKE) obf



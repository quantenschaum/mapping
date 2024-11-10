# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR_OPTS=OGR_S57_OPTIONS="LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)"

.PHONY: bsh.osm icons obf vwm bsh charts

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

%.zip:
	wget -O data/$@ "`./rwsget.py $(basename $@)`"

%.enc:
	rm -rf data/$@ data/$(basename $@).gpkg data/$(basename $@)-covr.gpkg
	unzip -j -n data/$(basename $@).zip -d data/$@
	for F in $$(find data/$@ -name "*.000"); do $(OGR_OPTS) ogr2ogr data/$(basename $@).gpkg      $$F        -skipfailures -append; done
	for F in $$(find data/$@ -name "*.000"); do $(OGR_OPTS) ogr2ogr data/$(basename $@)-covr.gpkg $$F M_COVR -skipfailures -append; done
	rm -rf data/$@

DIR=

dybde-no.gpkg:
	echo "download data from https://kartkatalog.geonorge.no/metadata/sjoekart-dybdedata/2751aacf-5472-4850-a208-3532a51c529a"
	rm -rf data/$(DIR)$@
	for F in data/$(DIR)Basis*GML.zip; do B=$${F%.zip}; unzip -o -d data/$(DIR) $$F && ogr2ogr data/$(DIR)$@ $$B.gml -append && rm $$B.g*; done

depth-no:
	rm -rf osm obf
	mkdir osm
	cp -v data/no-$(R)/*.osm osm
	$(MAKE) obf BLEVEL=no
	data/omc/inspector.sh -c charts/depth-no-$(R).obf obf/*.obf

depth-no.all:
	$(MAKE) depth-no R=east
	$(MAKE) depth-no R=west
	$(MAKE) depth-no R=mid
	$(MAKE) depth-no R=north

BSH_WMS=https://gdi.bsh.de/mapservice_gs/NAUTHIS_$$L/ows
BSH_LAYERS_1=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
# need this because there is a typo in the WMS layer name (coastel)
BSH_LAYERS_2=1_Overview,2_General,3_Coastel,4_Approach,5_Harbour,6_Berthing
# no overview layer for obstructions
BSH_LAYERS_3=2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing
BSH_BBOX=53.0,3.3,56.0,14.4

bsh:
	rm -rf data/bsh #data/bsh.gpkg
	mkdir -p data/bsh
	for L in AidsAndServices SkinOfTheEarth; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_1)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in RocksWrecksObstructions; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_3)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	for L in Hydrography Topography; do wget -O data/bsh/$$L.json "$(BSH_WMS)?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=$(BSH_LAYERS_2)&FORMAT=application/json;type=geojson&WIDTH=99999999&HEIGHT=99999999&CRS=EPSG:4326&BBOX=$(BSH_BBOX)"; done
	#for F in data/bsh/*.json; do jq . $$F>data/bsh/tmp; mv data/bsh/tmp $$F; done
	for F in $$(find data/bsh -name "*.json"); do ogr2ogr $${F/.json/.gpkg} $$F; done
	#for F in $$(find data/bsh -name "*.json"); do ogr2ogr data/bsh.gpkg $$F -append; done


data/Elevation-Bathymetry.zip:
	# https://gdi.bsh.de/de/feed/Hoehe-Bathymetrie.xml
	wget -O data/Elevation-Bathymetry.zip https://gdi.bsh.de/de/data/Elevation-Bathymetry.zip

bsh-bathy: data/Elevation-Bathymetry.zip
	unzip $< -d data/Elevation-Bathymetry

schutzzonen:
	rm -rf data/$@ data/$@.gpkg
	mkdir -p data/$@
	cd data/$@ && ../../$@.py
	cd data/ && for F in $@/*.zip; do unzip -n $$F -d $${F%.*}; ogr2ogr schutzzonen.gpkg $${F%.*} -append; rm -r $${F%.*}; done
	cd data/ && for F in $@/*.json; do ogr2ogr schutzzonen.gpkg $$F -append; done

waypoints:
	mkdir -p data
	rm -rf data/Wegepunkte2024.gpx
	wget -O data/waypoints.zip https://nvcharts.com/downloads/wegepunkte/2024/Wegepunkte2024_txt.zip
	cd data && unzip -n waypoints.zip && rm waypoints.zip

icons: icons/gen

icons/gen:
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
	mkdir -p cache_data && touch cache_data/.nobackup
	mapproxy-util serve-develop mapproxy.yaml -b 0.0.0.0:8001

seed:
	mkdir -p cache_data && touch cache_data/.nobackup
	mapproxy-seed -f mapproxy.yaml -s seed.yaml $(O)

stop-all:
	pkill qgis_mapserve || true
	pkill mapproxy-util || true
	pkill mapproxy-seed || true

clean-cache:
	rm -rf cache_data

docker:
	docker compose up -d

docker-seed: docker
	docker compose exec -T qgis make seed
	docker compose down

charts/%.mbtiles: cache_data/%.mbtiles
	mkdir -p charts
	./convert.py -yfX $< $@ -t "$(basename $(notdir $@)) `date +%F`" -Fwebp

charts/%.png.mbtiles: cache_data/%.mbtiles
	mkdir -p charts
	./convert.py -yfX $< $@ -t "$(basename $(notdir $@)) `date +%F`" -Fpng

charts/%.sqlitedb: charts/%.mbtiles
	mkdir -p charts
	./convert.py -f $< $@ -t "$(basename $(notdir $@)) `date +%F`"

www/%/: charts/%.mbtiles charts/%.png.mbtiles
	./convert.py -f $< $@
	./convert.py -a $(word 2,$^) $@
	chmod +rX -R $@

data/chartconvert:
	mkdir -p data
	wget -O data/avnav.zip https://github.com/wellenvogel/avnav/archive/refs/heads/master.zip
	cd data && unzip -n avnav.zip && mv avnav-master/chartconvert .
	cd data && rm -r avnav.zip avnav-master

charts/%.gemf: charts/%.mbtiles data/chartconvert
	data/chartconvert/convert_mbtiles.py tms $@ $<

tiles: $(patsubst cache_data/%.mbtiles,www/%/,$(wildcard cache_data/*.mbtiles))

charts: $(patsubst cache_data/%.mbtiles,charts/%.mbtiles,$(wildcard cache_data/*.mbtiles)) \
        $(patsubst cache_data/%.mbtiles,charts/%.png.mbtiles,$(wildcard cache_data/*.mbtiles)) \
        $(patsubst cache_data/%.mbtiles,charts/%.sqlitedb,$(wildcard cache_data/*.mbtiles)) \
        $(patsubst cache_data/%.mbtiles,charts/%.gemf,$(wildcard cache_data/*.mbtiles))

upload:
	rm -rf tmp && mkdir tmp
	cp -rpv mkdocs.yml docs tmp
	cp -rpv marine.render.xml depthcontourlines.addon.render.xml charts/* tmp/docs
	cd tmp/docs && ./times.py index.md
	cd tmp && mkdocs build
	rm -rf www/download
	mv tmp/site www/download
	rm -rf tmp
	chmod +rX -R www

vwm-update:
	#wget -O wad.osm '[out:xml][timeout:90][bbox:{{bbox}}];(  nwr[~"seamark:type"~"buoy"];  nwr[~"seamark:type"~"beacon"];  nwr["waterway"="fairway"];); (._;>;);out meta;'
	./update.py rws_buoys data/vwm/drijvend.json wad.osm

build:
	git pull
	$(MAKE) bsh
	$(MAKE) qmap-de.obf
	$(MAKE) lightsectors.obf
	$(MAKE) vwm waddenzee.zip waddenzee.enc
	$(MAKE) clean-cache
	$(MAKE) docker-seed
	$(MAKE) charts tiles upload






########################################################################################################################


CGDS=01 05 07 08 09 11 13 14 17
CGDS=01

data/us:
	rm -rf $@
	mkdir -p $@
	for I in $(CGDS); do wget -O $@/$${I}CGD_ENCs.zip https://charts.noaa.gov/ENCs/$${I}CGD_ENCs.zip; done
	for F in $@/*.zip; do unzip $$F -d $@; done

us: data/us
	for F in $$(find $< -name "*.000"); do echo $$F; $(OGR_OPTS) ogr2ogr data/us.gpkg $$F -skipfailures -append; done



marrekrite.gpx:
	wget -O data/$@ "https://github.com/marcelrv/OpenCPN-Waypoints/raw/main/Marrekrite-Aanlegplaatsen.gpx"

tides:
	mkdir data/$@ -p
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Nordsee/Gezeitenstrom_Nordsee.zip -O data/$@/Nordsee.zip
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Kueste/Gezeitenstrom_Kueste.zip   -O data/$@/Kueste.zip







xmls: nautical.render.xml depthcontourlines.addon.render.xml rendering_types.xml

%.render.xml:
	wget -O $(subst .xml,.0.xml,$@) https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

rendering_types.xml:
	wget -O $(subst .xml,.0.xml,$@) https://github.com/osmandapp/OsmAnd-resources/raw/master/obf_creation/rendering_types.xml

data/josm.jar:
	wget -O $@ https://josm.openstreetmap.de/josm-tested.jar

josm: data/josm.jar
	java $(JAVA_OPTS) --add-exports=java.base/sun.security.action=ALL-UNNAMED --add-exports=java.desktop/com.sun.imageio.plugins.jpeg=ALL-UNNAMED --add-exports=java.desktop/com.sun.imageio.spi=ALL-UNNAMED -jar $<


data/omc:
	mkdir -p data
	wget -O $@.zip https://download.osmand.net/latest-night-build/OsmAndMapCreator-main.zip
	unzip $@.zip -d $@

omc: data/omc
	$</OsmAndMapCreator.sh
	mv -v data/omc/*obf data/obf/

mobac:
	#java -Xms64m -Xmx1200M -jar data/mobac/Mobile_Atlas_Creator.jar
	java $(JAVA_OPTS) -jar data/mobac/Mobile_Atlas_Creator.jar

batch-0.xml: batch-all.xml
	sed 's/mapZooms.*/mapZooms="6-9;10-11"/' $< >$@

batch-1.xml: batch-all.xml
	sed 's/mapZooms.*/mapZooms="12-13"/' $< >$@

batch-2.xml: batch-all.xml
	sed 's/mapZooms.*/mapZooms="14-15"/' $< >$@

batch-3.xml: batch-all.xml
	sed 's/mapZooms.*/mapZooms="16-"/' $< >$@

batch-no.xml: batch-all.xml
	sed 's/mapZooms.*/mapZooms="10-11;12-13;14-15;16-"/' $< >$@
	sed 's/renderingTypesFile.*/renderingTypesFile="rendering_types-no.xml"/' $< >$@

BLEVEL=all

obf: data/omc batch-$(BLEVEL).xml
	mkdir -p $@
	java $(JAVA_OPTS) -cp "$$(ls $</*.jar)" net.osmand.util.IndexBatchCreator batch-$(BLEVEL).xml
	for F in $@/*_2.obf; do G=$${F/_2./.}; G=$${G,,}; mv -v $$F $$G; done
	rm -f $@/*.log

qmap-de.obf: bsh.osm
	rm -rf osm && mkdir -p osm
	for L in buoys beacons facilities lights stations; do ./update.py bsh-$$L data/bsh/AidsAndServices.json none osm/$$L.osm -a; done
	for L in rocks wrecks obstructions; do ./update.py bsh-$$L data/bsh/RocksWrecksObstructions.json none osm/$$L.osm -a; done
	for L in seabed; do ./update.py bsh-$$L data/bsh/Hydrography.json none osm/$$L.osm -a; done
	for L in beacons facilities lights; do ./lightsectors.py osm/$$L.osm osm/$$L-sectors.osm; done

	rm -rf obf
	$(MAKE) obf
	mkdir -p charts
	data/omc/inspector.sh -c charts/qmap-de.obf obf/*.obf

lightsectors.obf:
	wget -O data/lights.osm 'https://overpass-api.de/api/interpreter?data=[out:xml][timeout:90];( 	  nwr["seamark:type"="light_major"];   nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:range"]; 	  nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:1:range"];   	);(._;>;);out meta;'

	rm -rf obf

	#rm -rf osm && mkdir -p osm
	#./lightsectors.py data/lights.osm osm/$@
	#$(MAKE) obf

	rm -rf osm && mkdir -p osm
	./lightsectors.py data/lights.osm osm/lightsectors-0.osm -a 0.30 -f 1.6 -r 16
	$(MAKE) obf BLEVEL=0

	rm -rf osm && mkdir -p osm
	./lightsectors.py data/lights.osm osm/lightsectors-1.osm -a 0.20 -f 0.8 -r 8
	$(MAKE) obf BLEVEL=1

	rm -rf osm && mkdir -p osm
	./lightsectors.py data/lights.osm osm/lightsectors-2.osm -a 0.15 -f 0.4 -r 4
	$(MAKE) obf BLEVEL=2

	rm -rf osm && mkdir -p osm
	./lightsectors.py data/lights.osm osm/lightsectors-3.osm -a 0.10 -f 0.2 -r 2
	$(MAKE) obf BLEVEL=3

	mkdir -p charts
	data/omc/inspector.sh -c charts/lightsectors.obf obf/*.obf


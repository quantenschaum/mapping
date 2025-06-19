# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
export PATH:=$(PWD)/scripts:$(PWD)/spreet/target/release:$(PWD)/tippecanoe:$(PATH)
export OGR_S57_OPTIONS=LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON
# export S57_CSV="$(PWD)/scripts"

.PHONY: icons obf vwm charts qgis mapproxy www web

help:
	cat README.md

build:
# 	$(MAKE) lightsectors.obf
	$(MAKE) vwm rws
	$(MAKE) qmap-de.obf qmap-de.zip qmap-nl.zip
	$(MAKE) clean-cache
	$(MAKE) docker-seed
	$(MAKE) charts tiles zips www

vwm:
	rm -rf data/vwm && mkdir -p data/vwm
	wget -O data/vwm/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O data/vwm/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"

	vconvert.py data/vwm/drijvend.json data/vwm/drijvend.s57.json
	vconvert.py data/vwm/vast.json data/vwm/vast.s57.json
	filter.py data/vwm/drijvend.s57.json -L data/vwm/layers
	filter.py data/vwm/vast.s57.json -L data/vwm/layers

	rm -f data/vwm.gpkg
	for F in $$(find data/vwm -name "*.json"); do ogr2ogr data/vwm.gpkg $$F -append; done

csv:  scripts/s57objectclasses.csv scripts/s57attributes.csv

%.csv:
	curl https://raw.githubusercontent.com/OpenCPN/OpenCPN/refs/heads/master/data/s57data/$(notdir $@) >$@

%.zip:
	wget -O data/$@ "`rwsget.py $(basename $@)`"

%.enc: %.zip
	rm -rf data/$@ data/$(basename $@).gpkg data/$(basename $@)-covr.gpkg
	unzip -j -n data/$(basename $@).zip -d data/$@
	for F in $$(find data/$@ -name "*.000"); do S57_CSV="$(PWD)/scripts" ogr2ogr -q $${F//.000/.gpkg} $$F; done
	for F in $$(find data/$@ -name "*.gpkg"); do C=$${F##*/}; C=$${C%.gpkg}; for L in `ogrinfo -q $$F |grep : |cut -d ' ' -f 2`; do echo "$$C $$L"; ogrinfo $$F -q -sql "ALTER TABLE $$L ADD COLUMN chart TEXT"; ogrinfo $$F -q -sql "UPDATE $$L SET chart = '$$C'"; done; done
	for F in $$(find data/$@ -name "*.gpkg"); do ogr2ogr data/$(basename $@).gpkg $$F -append; done
	rm -rf data/$@

rws: waddenzee.enc zeeland.enc
	cp data/waddenzee.gpkg data/$@.gpkg
	ogr2ogr data/$@.gpkg data/zeeland.gpkg -append
	ogr2ogr data/$@-covr.gpkg data/$@.gpkg M_COVR

%.layers: data/%.gpkg
	rm -rf data/$@ && mkdir data/$@
	for L in `ogrinfo -q $< |grep : |cut -d ' ' -f 2`; do echo $$L; ogr2ogr -q -f GeoJSON data/$@/$$L.json $< $$L; done

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

icons: icons/gen

icons/gen:
	cd icons && rm -rf gen/* && genicons.py
	cd icons/gen && ln -sr TOPSHP/12 TOPSHP/9
	cd icons/gen && ln -sr TOPSHP/19 TOPSHP/20
	cd icons/gen && ln -sr TOPSHP/19 TOPSHP/21
	cd icons/gen && mkdir -p TOPSHP/15/0 && ln -sr TOPSHP/15.svg TOPSHP/15/0/0.svg
	cd icons/gen && mkdir -p TOPSHP/16/0 && ln -sr TOPSHP/16.svg TOPSHP/16/0/0.svg
	sed 's#gen/#https://raw.githubusercontent.com/quantenschaum/mapping/refs/heads/icons/#g' icons/extra.mapcss >icons/gen/extra.mapcss

icons.zip: icons/gen
	rm -f charts/$@
	zip charts/$@ -r icons/gen

spreet:
	git clone https://github.com/flother/spreet
	cd spreet && cargo build --release

sprites: icons
	spreet icons/gen  www/icons --recursive --unique --ratio 2
	sed 's/"pixelRatio": [[:digit:]]\+/"pixelRatio": 1/g' www/icons.json -i
	spreet icons/gen  www/icons@2x --recursive --unique --ratio 4
	sed 's/"pixelRatio": [[:digit:]]\+/"pixelRatio": 2/g' www/icons@2x.json -i

vector:
	rm -rf www/pbf
	tippecanoe -Z6 -z16 -B6 -r1 data/bsh/filtered/*.json -j '{"*":["any", ["all",["==","uband",1],["<=","$$zoom",8]], ["all",["==","uband",2],["in","$$zoom",9]], ["all",["==","uband",3],["in","$$zoom",10,11]], ["all",["==","uband",4],["in","$$zoom",12,13]], ["all",["==","uband",5],["in","$$zoom",14,15]], ["all",["==","uband",6],[">=","$$zoom",16]],        ["all",["has","MARSYS"], ["any", ["all",["==","uband",2],["<=","$$zoom",8]], ["all",["==","uband",3],["in","$$zoom",9]], ["all",["==","uband",4],["in","$$zoom",10,11]], ["all",["==","uband",5],["in","$$zoom",12,13]], ["all",["==","uband",6],["in","$$zoom",14,15]]] ] ]}' --no-tile-compression -x lnam --output-to-directory=www/pbf       # -o www/bsh.mbtiles
	du -sch www/pbf/*
# 	cat www/pbf/metadata.json |jq .json -r |jq >www/tile.json

data/Elevation-Bathymetry.zip:
	# https://gdi.bsh.de/de/feed/Hoehe-Bathymetrie.xml
	wget -O data/Elevation-Bathymetry.zip https://gdi.bsh.de/de/data/Elevation-Bathymetry.zip
	wget -O data/SKN_Nordsee_2021.zip https://data.bsh.de/OpenData/Main/SKN_Nordsee_2021/SKN_Nordsee_2021.zip

bsh-bathy: data/Elevation-Bathymetry.zip
	unzip $< -d data/Elevation-Bathymetry

schutzzonen:
	rm -rf data/$@
	mkdir -p data/$@
	cd data/$@ && schutzzonen.py
	cd data/ && for F in $@/*.zip; do unzip -n $$F -d $${F%.*}; ogr2ogr schutzzonen.gpkg $${F%.*} -append; rm -r $${F%.*}; done

	rm -rf data/$@.gpkg
	cd data/$@ && for F in *.json; do ogr2ogr $$F.gpx $$F -t_srs "EPSG:4326"; done
	cd data/$@ && for F in *.json; do ogr2ogr ../$@.gpkg $$F -append -t_srs "EPSG:4326"; done

waypoints:
	mkdir -p data
	rm -rf data/Wegepunkte2024.gpx
	wget -O data/waypoints.zip https://nvcharts.com/downloads/wegepunkte/2024/Wegepunkte2024_txt.zip
	cd data && unzip -n waypoints.zip && rm waypoints.zip

qgis/bsh1.qgs: qgis/bsh.qgs
	sed 's#<value>000000</value>#<value>1</value>#g' $< >$@

qgis/bsh2.qgs: qgis/bsh.qgs
	sed 's#<value>000000</value>#<value>2</value>#g' $< >$@

serve:
	cd www && python -m http.server 8002

qgis: icons qgis/bsh1.qgs qgis/bsh2.qgs
	cd qgis && QGIS_SERVER_PARALLEL_RENDERING=1 qgis_mapserver

mapproxy:
	mkdir -p cache_data && touch cache_data/.nobackup
	mapproxy-util serve-develop mapproxy/mapproxy.yaml -b 0.0.0.0:8001

seed:
	sleep 3
	mkdir -p cache_data && touch cache_data/.nobackup
	mapproxy-seed -f mapproxy/mapproxy.yaml -s mapproxy/seed.yaml $(O)

stop-all:
	pkill qgis_mapserve || true
	pkill mapproxy-util || true
	pkill mapproxy-seed || true
	docker compose down

clean-cache:
	rm -rf cache_data

docker:
	docker compose up -d

docker-seed: docker
	docker compose exec -T qgis make seed
	docker compose down

TRANSPARENT=-cf9ecc0

charts/%.mbtiles: cache_data/%.mbtiles
	mkdir -p charts
	convert.py -yfX $< $@ -t "$(basename $(notdir $@)) `date +%F`" -Fwebp #$(TRANSPARENT)

charts/%.png.mbtiles: cache_data/%.mbtiles
	mkdir -p charts
	convert.py -yfX $< $@ -t "$(basename $(notdir $@)) `date +%F`" -Fpng #$(TRANSPARENT)

charts/%.sqlitedb: charts/%.mbtiles
	mkdir -p charts
	convert.py -f $< $@ -t "$(basename $(notdir $@)) `date +%F`"

www/%/: charts/%.mbtiles charts/%.png.mbtiles
	convert.py -f $< $@
	convert.py -a $(word 2,$^) $@
	cp www/map.html $@/index.html
	chmod +rX -R $@

data/chartconvert:
	mkdir -p data
	wget -O data/avnav.zip https://github.com/wellenvogel/avnav/archive/refs/heads/master.zip
	cd data && unzip -n avnav.zip && mv avnav-master/chartconvert .
	cd data && rm -r avnav.zip avnav-master

charts/%.gemf: charts/%.mbtiles data/chartconvert
	data/chartconvert/convert_mbtiles.py tms $@ $<

tiles: $(patsubst cache_data/%.mbtiles,www/%/,$(wildcard cache_data/*.mbtiles))
	touch www/updated

charts: $(patsubst cache_data/%.mbtiles,charts/%.mbtiles,$(wildcard cache_data/*.mbtiles)) \
        $(patsubst cache_data/%.mbtiles,charts/%.png.mbtiles,$(wildcard cache_data/*.mbtiles)) \
        $(patsubst cache_data/%.mbtiles,charts/%.sqlitedb,$(wildcard cache_data/*.mbtiles))
#         $(patsubst cache_data/%.mbtiles,charts/%.gemf,$(wildcard cache_data/*.mbtiles))

zips: icons.zip qmap-data.zip qmap-de.tiles.zip qmap-nl.tiles.zip

web:
	cd $@ && npm install && npm run build
	cd www && rm *bundle*.js workbox*.js
	cp -rv $@/dist/* www

www: web
	rm -rf tmp && mkdir tmp
	cp -rpv .git tmp
	cp -rpv mkdocs.yml docs tmp
	cp -rpv osmand/marine.render.xml charts/* data/*.gpkg qgis/*.qgs tmp/docs
	cd tmp/docs && ./times.py index.md print.md index.de.md print.de.md index.nl.md print.nl.md
	cd tmp && mkdocs build
	rm -rf www/download
	mv tmp/site www/download
	rm -rf tmp
	chmod +rX -R www

%.tiles.zip:
	cd www && zip - -q -r $(patsubst %.tiles.zip,%/,$@) -x '*.png' >../charts/$@

qmap-data.zip:
	rm -f charts/$@
	zip charts/$@ -r icons/gen data/bsh.gpkg data/soundg-de.gpkg data/rws.gpkg data/vwm.gpkg qgis/bsh.qgs qgis/rws.qgs qgis/paperchart.qpt

vwm-update:
	#wget -O wad.osm '[out:xml][timeout:90][bbox:{{bbox}}];(  nwr[~"seamark:type"~"buoy"];  nwr[~"seamark:type"~"beacon"];  nwr["waterway"="fairway"];); (._;>;);out meta;'
	update.py rws_buoys data/vwm/drijvend.json wad.osm





########################################################################################################################


CGDS=01 05 07 08 09 11 13 14 17
CGDS=01

data/us:
	rm -rf $@
	mkdir -p $@
	for I in $(CGDS); do wget -O $@/$${I}CGD_ENCs.zip https://charts.noaa.gov/ENCs/$${I}CGD_ENCs.zip; done
	for F in $@/*.zip; do unzip $$F -d $@; done

us: data/us
	for F in $$(find $< -name "*.000"); do echo $$F; ogr2ogr data/us.gpkg $$F -skipfailures -append; done



marrekrite.gpx:
	wget -O data/$@ "https://github.com/marcelrv/OpenCPN-Waypoints/raw/main/Marrekrite-Aanlegplaatsen.gpx"

tides:
	mkdir data/$@ -p
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Nordsee/Gezeitenstrom_Nordsee.zip -O data/$@/Nordsee.zip
	wget https://data.bsh.de/OpenData/Main/Gezeitenstrom_Kueste/Gezeitenstrom_Kueste.zip   -O data/$@/Kueste.zip







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

osmand/batch-0.xml: osmand/batch-all.xml
	sed 's/mapZooms.*/mapZooms="6-9;10-11"/' $< >$@

osmand/batch-1.xml: osmand/batch-all.xml
	sed 's/mapZooms.*/mapZooms="12-13"/' $< >$@

osmand/batch-2.xml: osmand/batch-all.xml
	sed 's/mapZooms.*/mapZooms="14-15"/' $< >$@

osmand/batch-3.xml: osmand/batch-all.xml
	sed 's/mapZooms.*/mapZooms="16-"/' $< >$@

osmand/batch-no.xml: osmand/batch-all.xml
	sed 's/mapZooms.*/mapZooms="10-11;12-13;14-15;16-"/' $< >$@
	sed 's/renderingTypesFile.*/renderingTypesFile="rendering_types-no.xml"/' $< >$@

BLEVEL=all

obf: data/omc osmand/batch-$(BLEVEL).xml
	mkdir -p $@
	java $(JAVA_OPTS) -cp "$$(ls $</*.jar)" net.osmand.util.IndexBatchCreator osmand/batch-$(BLEVEL).xml
	for F in $@/*_2.obf; do G=$${F/_2./.}; G=$${G,,}; mv -v $$F $$G; done
	rm -f $@/*.log

qmap-de.obf:
	rm -rf osm && mkdir -p osm
	for L in buoys beacons facilities lights stations; do update.py bsh-$$L data/bsh/A*.json none osm/$$L.osm -a; done
	for L in rocks wrecks obstructions; do update.py bsh-$$L data/bsh/R*.json none osm/$$L.osm -a; done
	for L in seabed; do update.py bsh-$$L data/bsh/H*.json none osm/$$L.osm -a; done
	for L in beacons facilities lights; do lightsectors.py osm/$$L.osm osm/$$L-sectors.osm; done

	rm -rf obf
	$(MAKE) obf
	mkdir -p charts
	data/omc/inspector.sh -c charts/qmap-de.obf obf/*.obf

qmap-de.zip:
	rm -rf qmap-de/
	sconvert.py -o qmap-de data/bsh/layers/*.json -t "QMAP-DE `date +%F`"
	rm -f charts/$@
	zip charts/$@ -r qmap-de

qmap-nl.zip: rws.layers
	rm -rf $(basename $@)/
# 	cp -v data/vwm/layers/*.json data/rws.layers
	sconvert.py -o $(basename $@) data/rws.layers/*.json -t "QMAP-NL `date +%F`" -u4 -j0
	rm -f charts/$@
	zip charts/$@ -r $(basename $@)

lightsectors.obf:
	wget -O data/lights.osm 'https://overpass-api.de/api/interpreter?data=[out:xml][timeout:90];( 	  nwr["seamark:type"="light_major"];   nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:range"]; 	  nwr[~"seamark:type"~"landmark|light|beacon"]["seamark:light:1:range"];   	);(._;>;);out meta;'

	rm -rf obf

	#rm -rf osm && mkdir -p osm
	#lightsectors.py data/lights.osm osm/$@
	#$(MAKE) obf

	rm -rf osm && mkdir -p osm
	lightsectors.py data/lights.osm osm/lightsectors-0.osm -a 0.30 -f 1.6 -r 16
	$(MAKE) obf BLEVEL=0

	rm -rf osm && mkdir -p osm
	lightsectors.py data/lights.osm osm/lightsectors-1.osm -a 0.20 -f 0.8 -r 8
	$(MAKE) obf BLEVEL=1

	rm -rf osm && mkdir -p osm
	lightsectors.py data/lights.osm osm/lightsectors-2.osm -a 0.15 -f 0.4 -r 4
	$(MAKE) obf BLEVEL=2

	rm -rf osm && mkdir -p osm
	lightsectors.py data/lights.osm osm/lightsectors-3.osm -a 0.10 -f 0.2 -r 2
	$(MAKE) obf BLEVEL=3

	mkdir -p charts
	data/omc/inspector.sh -c charts/lightsectors.obf obf/*.obf

depth-de.obf:
	rm -rf obf
# 	rm -rf osm && mkdir -p osm
# 	cp data/depth-de-6.osm osm
# 	$(MAKE) obf
# 	cp obf/depth-de-6.obf charts/$@

	rm -rf osm && mkdir -p osm
	cp data/depth-de-2.osm osm
	$(MAKE) obf BLEVEL=0

	rm -rf osm && mkdir -p osm
	cp data/depth-de-3.osm osm
	$(MAKE) obf BLEVEL=1

	rm -rf osm && mkdir -p osm
	cp data/depth-de-4.osm osm
	$(MAKE) obf BLEVEL=2

	rm -rf osm && mkdir -p osm
	cp data/depth-de-6.osm osm
	$(MAKE) obf BLEVEL=3

	mkdir -p charts
	data/omc/inspector.sh -c charts/$@ obf/*.obf

SHELL=/bin/bash
export PATH:=$(PWD)/tools/bin:$(PWD)/node_modules/.bin:$(PATH)
TODAY=$(shell date +%F)
MERGE=jq -sc '{type:"FeatureCollection", features: map(.features // []) | add}'

# usesful tools
# https://stevage.github.io/vector-inspector/
# https://pmtiles.io/
# https://docs.teledynecaris.com/s-57/frames/S57catalog.htm
# https://mapshaper.org/

tools:
	pnpm install
	touch node_modules/.nobackup
	make -C $@

dev:
	make -B styles
	npx vite

open:
	npx vite --open

build:
	make -B styles BASE=https://freenauticalchart.net/vector
	pnpm install
	npx vite build

preview:
	npx vite preview

deploy: build
	rsync -hrtlv dist/ nas:mapping/www/vector/

tunnel:
	cloudflared tunnel --url http://localhost:5173/

OSM=visible

data/styles/%.json: styles/s57.json
	mkdir -p data/styles
	N=$(patsubst data/styles/%.json,%,$@); \
	jq '.name="'$$N'" | .sources.s57.url="mbtiles://{'$$N'}" | .sprite="icons" | .glyphs="{fontstack}/{range}.pbf" | .layers[0].layout.visibility="$(OSM)"' $< > $@
	gl-style-validate $@

BASE=http://localhost:5173

public/%.json: styles/s57.json
	mkdir -p public
	N=$(patsubst public/%.json,%,$@); \
	jq '.name="'$$N'" | .sources.s57.url="pmtiles://$(BASE)/'$$N'.pmtiles" | .sprite="$(BASE)/icons" | .glyphs="$(BASE)/fonts/{fontstack}/{range}.pbf"' $< > $@

sprites:
	cd .. && make -B icons/gen && rm icons/gen/compass-*
	mkdir -p public
	spreet ../icons/gen  public/icons --recursive --unique --ratio 2
	sed 's/"pixelRatio": [[:digit:]]\+/"pixelRatio": 1/g' public/icons.json -i
	spreet ../icons/gen  public/icons@2x --recursive --unique --ratio 4
	sed 's/"pixelRatio": [[:digit:]]\+/"pixelRatio": 2/g' public/icons@2x.json -i
	cp public/icons* data/sprites

FURL=https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans
FONTS=NotoSans-Regular NotoSans-SemiBold NotoSans-Bold NotoSans-Italic NotoSans-BoldItalic NotoSans-SemiBoldItalic

fonts:
	mkdir -p data/fonts
	for F in $(FONTS); do [[ -f $@/$$F.ttf ]] || wget $(FURL)/$$F.ttf -O $@/$$F.ttf; done
	for F in $@/*.ttf; do \
		D="$${F#*/}"; \
		D="$${D%.*}"; \
		D="$${D//Noto/Noto }"; \
		D="$${D//-/ }"; \
		D="$${D//SemiBold/Semi Bold}"; \
		D="$${D//BoldItalic/Bold Italic}"; \
		mkdir -p "$@/$$D"; \
		build-glyphs $$F "$@/$$D"; done


SOURCE=../data/bsh

split/%.json: $(SOURCE)/%.json
	mapshaper $< -filter 'uband>0' -o $@

split: $(SOURCE)
	rm -rf $@ && mkdir -p $@
	touch $@/.nobackup
	nice make $(patsubst $</%.json,$@/%.json,$(wildcard $</??????.json)) -j
	$(MERGE) $@/BOY*.json > $@/buoys.json
	$(MERGE) $@/BCN*.json > $@/beacons.json
	rm $@/BOY*.json $@/BCN*.json
	[[ -f $@/M_COVR.json ]] && \
		mapshaper $@/M_COVR.json -filter 'CATCOV==1' -o force $@/M_COVR.json || \
		mapshaper $@/M_NSYS.json -filter 'ORIENT==null' -o $@/M_COVR.json
	mapshaper $@/M_COVR.json -each 'chartname=chart' -o force $@/M_COVR.json
	mapshaper $@/DEPARE.json -each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' -dissolve allow-overlaps uband,areatype calc='DRVAL1=min(DRVAL1), DRVAL2=max(DRVAL2)' -explode -each 'area=this.area/1e6' -o force $@/DEPARE.json

merged/_M%.json: split
	mapshaper $</M_COVR.json -filter "uband==$(patsubst merged/_M%.json,%,$@)" -dissolve -o $@

merged/%.json: split/%.json
	L=$(patsubst merged/%.json,%,$@); \
	for U in $$(seq 6); do echo -e "\e[33m$$L $$U\e[0m"; \
		rm -f merged/__*$$L.json; \
		[[ -f $@ ]] && mapshaper $@ -erase merged/_M$$U.json -o merged/__A$$U-$$L.json; \
  	mapshaper $< -filter "uband==$$U" -o merged/__B$$U-$$L.json && \
   	$(MERGE) merged/__?$$U-$$L.json > $@ && \
		mapshaper $@ -each uband=$$U -o force $@ && \
		cp $@ merged/UB$$U/ && \
		rm merged/__*$$L.json || break; done

merged: split
	rm -rf $@ && mkdir -p $@/UB1 $@/UB2 $@/UB3 $@/UB4 $@/UB5 $@/UB6
	touch $@/.nobackup
	for U in $$(seq 6); do make $@/_M$$U.json; done
	nice make $(patsubst $</%.json,$@/%.json,$(wildcard $</*.json)) -j
	rm -f $@/*.json
	for F in $@/*/*1.json; do $(MERGE) $${F//1./?.} > $${F//1./.} && rm $${F//1./?.}; done
	# for F in $$(cd $@/UB6 && echo *.json); do $(MERGE) $@/UB?/$$F >$@/$$F; done
	# for U in $$(seq 6); do cp $</M_COVR.json $@/UB$$U; done
	# mapshaper $</M_COVR.json -lines each='uband=A.uband||B.uband,chartname=A.chartname||B.chartname' -o $@/M_COVR.json

# include only fields used in the style
Y=$(shell jq '.. | arrays | select(.[0]=="get" or .[0]=="has") | .[1]' styles/s57.json | sort | uniq | sed 's/^/-y /')

bsh.tiles: merged
	tippecanoe $</M_COVR.json -f -y uband $(Y) -Z6 -z13 -j '{"*":["any",["all",["<=","$$zoom",6],[">","uband",1]],["all",["<=","$$zoom",8],[">","uband",2]],["all",["<=","$$zoom",10],[">","uband",3]],["all",["<=","$$zoom",12],[">","uband",4]],["all",["<=","$$zoom",13],[">","uband",5]]]}' -o UB0.mbtiles # charts outlines
	tippecanoe $</UB1/*.json -f -r1 -ao -ac $(Y) -Z6  -z6  -o UB1.mbtiles # 1 Overview
	tippecanoe $</UB2/*.json -f -r1 -ao -ac $(Y) -Z7  -z8  -o UB2.mbtiles # 2 General
	tippecanoe $</UB3/*.json -f -r1 -ao -ac $(Y) -Z9  -z10 -o UB3.mbtiles # 3 Coastal
	tippecanoe $</UB4/*.json -f -r1 -ao -ac $(Y) -Z11 -z12 -o UB4.mbtiles # 4 Approach
	tippecanoe $</UB5/*.json -f -r1 -ao -ac $(Y) -Z13 -z13 -o UB5.mbtiles # 5 Harbour
	tippecanoe $</UB6/*.json -f -r1 -ao -ac $(Y) -Z14 -z14 -o UB6.mbtiles # 6 Berthing
	tile-join -n QMAP-DE -N "$(TODAY)" -A QMAP/BSH -f -o qmap-de.mbtiles UB?.mbtiles
	pmtiles convert qmap-de.mbtiles qmap-de.pmtiles
	ls -lh *tiles
	mv qmap-de.mbtiles data
	mv qmap-de.pmtiles public
	rm UB*.mbtiles

styles: data/styles/qmap-de.json public/qmap-de.json

rws: ../data/rws.layers
	rm -rf $@ && cp -r $< $@
	touch $@/.nobackup
	for F in $@/*; do B=$${F#*/}; B=$${B%.*}; mv $$F $@/$${B^^}.json; done
	$(MERGE) $@/BOY*.json > $@/buoys.json
	$(MERGE) $@/BCN*.json > $@/beacons.json
	rm $@/BOY*.json $@/BCN*.json
	mapshaper ../data/vwm/drijvend.s57.json -filter 'layer.startsWith("BOY")' -o $@/buoys.json
	# cp ../data/vwm/vast.s57.json     $@/beacons.json
	mapshaper $@/DEPARE.json -each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' -dissolve areatype calc='DRVAL1=min(DRVAL1), DRVAL2=max(DRVAL2)' -o force $@/DEPARE.json
	mapshaper $@/DEPCNT.json -filter 'VALDCO<=0 || [1,2,3,5,10,20,50].includes(VALDCO)' -o force $@/DEPCNT.json
	mapshaper $@/SOUNDG.json -each 'VALSOU=DEPTH' -o force $@/SOUNDG.json
	mapshaper $@/M_COVR.json -filter 'CATCOV==1' -each 'chartname=chart' -o force $@/M_COVR.json

rws.tiles: rws
	tippecanoe $</M_COVR.json $</LNDARE.json $</DEPARE.json $</COALNE.json $</BUAARE.json $</LNDRGN.json $</SEAARE.json -f -ao -ac -Z8 -z9 $(Y) -o $<0.mbtiles
	tippecanoe $</*.json -f -r1 -ao -ac -Z10 -z14 -y SCAMIN $(Y) -o $<1.mbtiles -j '{ "SOUNDG": ["any", ["all", ["==", "$$zoom", 11], [">=", "SCAMIN", 160000] ], ["all", ["==", "$$zoom", 12], [">=", "SCAMIN", 80000] ], ["all", ["==", "$$zoom", 13], [">=", "SCAMIN", 40000] ], ["all", [">=", "$$zoom", 14]] ], "buoys":[">=","$$zoom",11], "beacons":[">=","$$zoom",11], "LIGHTS":[">=","$$zoom",11], "DAYMAR":[">=","$$zoom",11], "DEPCNT":[">=","$$zoom",11] }'
	tile-join -n "RWS" -N "$(TODAY)" -A "QMAP/RWS" -f -o qmap-nl.mbtiles $<?.mbtiles
	pmtiles convert qmap-nl.mbtiles qmap-nl.pmtiles
	ls -lh *tiles
	mv qmap-nl.mbtiles data
	mv qmap-nl.pmtiles public
	rm rws*.mbtiles
styles: data/styles/qmap-nl.json public/qmap-nl.json

tiles: bsh.tiles rws.tiles

clean:
	rm -rf dist split merged rws *.gpkg *.mbtiles *.pmtiles

depth:
	rm -rf $@ && mkdir -p $@
	mapshaper merged/UB6/DEPARE.json \
		-each 'contourarea="depth"' \
		-each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' \
		-dissolve contourarea,areatype \
		-o $@/DEPARE.json
	mapshaper merged/UB6/DEPCNT.json \
		-each 'contour="depth"' \
		-each 'depth=VALDCO.toFixed(0)' \
		-each 'contourtype=10' \
		-dissolve contour,depth,contourtype \
		-o $@/DEPCNT.json
	mapshaper merged/UB6/SOUNDG.json \
		-each 'point="depth"' \
		-each 'depth=VALSOU>10||VALSOU%10==0?VALSOU.toFixed(0):VALSOU.toFixed(1)' \
		-filter-fields point,depth,uband \
		-o $@/SOUNDG.json
	ogr2ogr $@/depth.gpkg $@/DEPARE.json
	ogr2ogr $@/depth.gpkg $@/DEPCNT.json -append
	ogr2ogr $@/depth.gpkg $@/SOUNDG.json -append

serve:
	make -B styles
	mkdir -p cache_data && touch cache_data/.nobackup
	docker compose up

seed:
	make -B styles OSM=none
	mkdir -p cache_data && touch cache_data/.nobackup
	docker compose up -d
	sleep 3
	docker compose exec -u mapproxy -T mapproxy mapproxy-seed -f /data/mapproxy.yaml -s /data/seed.yaml
	docker compose down

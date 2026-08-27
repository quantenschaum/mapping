SHELL=/bin/bash
export PATH:=$(PWD)/tools/bin:$(PWD)/node_modules/.bin:$(PATH)
export NODE_OPTIONS="--max-old-space-size=8192"
TODAY=$(shell date +%F)

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
	pnpx vite

open:
	pnpx vite --open

build:
	make -B styles BASE=https://freenauticalchart.net/vector
	pnpm install
	pnpx vite build

preview:
	pnpx vite preview

deploy: build
	rsync -hrtlv dist/ nas:mapping/www/vector/

tunnel:
	cloudflared tunnel --url http://localhost:5173/

OSM=visible

.PRECIOUS: data/styles/%.json

data/styles/%.json: styles/s57.json
	mkdir -p data/styles
	N=$(patsubst data/styles/%.json,%,$@); \
	C=$$(pmtiles show public/$$N.pmtiles |grep center:); \
	[[ $$C =~ long:[[:space:]]*([-0-9.]+),[[:space:]]*lat:[[:space:]]*([-0-9.]+) ]] && \
	lon="$${BASH_REMATCH[1]}" && lat="$${BASH_REMATCH[2]}"; \
	[[ ! -v lat ]] || LL="| .center=[$$lon,$$lat]"; \
	jq ".name=\"$$N\" | .sources.s57.url=\"mbtiles://{$$N}\" | .sprite=\"icons\" | .glyphs=\"{fontstack}/{range}.pbf\" | .layers[0].layout.visibility=\"$(OSM)\" $$LL" $< > $@
	gl-style-validate $@

BASE=http://localhost:5173

public/%.json: data/styles/%.json
	mkdir -p public
	N=$(patsubst public/%.json,%,$@); \
	jq ".name=\"$$N\" | .sources.s57.url=\"pmtiles://$(BASE)/$$N.pmtiles\" | .sources.s57.attribution=\"$$N $(TODAY)\" | .sprite=\"$(BASE)/icons\" | .glyphs=\"$(BASE)/fonts/{fontstack}/{range}.pbf\"" $< > $@

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

MERGE=jq -sc '{type:"FeatureCollection", features: map(.features // []) | add}'

SRC=../data/bsh
DST=fnc-de
ATT=FNC/BSH

split/%.json: $(SRC)/%.json
	# split by type and remove unused fields
	mapshaper $< -filter 'uband>0' -drop fields=RCID,PRIM,GRUP,OBJL,RVER,AGEN,FIDN,FIDS,LNAM,LNAM_REFS,FFPT_RIND -o $@

split: $(SRC)
	rm -rf $@ && mkdir -p $@
	touch $@/.nobackup
	nice parallel -j50% --bar make ::: $(patsubst $</%.json,$@/%.json,$(wildcard $</??????.json))
	$(MERGE) $@/BOY*.json > $@/buoys.json
	$(MERGE) $@/BCN*.json > $@/beacons.json
	rm $@/BOY*.json $@/BCN*.json
	[[ -f $@/M_COVR.json ]] && \
		mapshaper $@/M_COVR.json -filter 'CATCOV==1' -o force $@/M_COVR.json || \
		mapshaper $@/M_NSYS.json -filter 'ORIENT==null' -o $@/M_COVR.json
	mapshaper $@/M_COVR.json -each 'cell=chart' -o force $@/M_COVR.json
	# mapshaper $@/DEPARE.json -each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' -filter-fields uband,areatype,DRVAL1,DRVAL2 -each 'area=this.area/1e6' -o force $@/DEPARE.json
	mapshaper $@/DEPARE.json -each 'areatype=DRVAL1>=9.1?10:DRVAL1>=5?5:DRVAL1>=1.8?2:DRVAL1>=0?0:-1' -dissolve allow-overlaps uband,areatype calc='DRVAL1=min(DRVAL1), DRVAL2=max(DRVAL2)' -explode -each 'area=this.area/1e6' -o force $@/DEPARE.json
	# mapshaper $@/SOUNDG.json -each 'VALSOU=DEPTH' -o force $@/SOUNDG.json || true
	# mapshaper $@/SOUNDG.json -each 'VALSOU=DEPTH' -filter-fields uband,VALSOU -o force $@/SOUNDG.json || true
	mapshaper $@/SOUNDG.json -each 'VALSOU=DEPTH' -dissolve group-points uband,VALSOU -o force $@/SOUNDG.json || true

merged/M/%.json: split
	mkdir -p merged/M
	mapshaper $</M_COVR.json -filter "uband==$(patsubst merged/M/%.json,%,$@)" -dissolve -each 'mask=1' -o $@

xmerged/%.json: split/%.json
	# separate usage bands
	for U in {1..6}; do mapshaper $< -filter "uband==$$U" -o merged/UB$$U/$(notdir $@).json; done

xmerged/%.json: split/%.json
	# higher usage bands merged with all lower bands
	B=$(basename $@); \
	for U in {1..6}; do mapshaper $< -filter "uband==$$U" -o $$B-$$U.json; done; \
	$(MERGE) $$B-1.json > $@ && cp $@ merged/UB1; \
	mapshaper $@ -erase merged/M/2.json -o $$B-1.json; \
	$(MERGE) $$B-{1,2}.json > $@ && cp $@ merged/UB2; \
	mapshaper $@ -erase merged/M/3.json -o $$B-1.json; \
	$(MERGE) $$B-{1,3}.json > $@ && cp $@ merged/UB3; \
	mapshaper $@ -erase merged/M/4.json -o $$B-1.json; \
	$(MERGE) $$B-{1,4}.json > $@ && cp $@ merged/UB4; \
	mapshaper $@ -erase merged/M/5.json -o $$B-1.json; \
	$(MERGE) $$B-{1,5}.json > $@ && cp $@ merged/UB5; \
	mapshaper $@ -erase merged/M/6.json -o $$B-1.json; \
	$(MERGE) $$B-{1,6}.json > $@ && cp $@ merged/UB6; \
	rm $$B*.json

merged/%.json: split/%.json
	# higher usage bands merged with 2 previous bands
	B=$(basename $@); \
	for U in {1..6}; do mapshaper $< -filter "uband==$$U" -o $$B-$$U.json; done; \
	$(MERGE) $$B-{1..1}.json > $@ && mv $@ merged/UB1; \
	mapshaper $$B-1.json -erase merged/M/2.json -o force $$B-1.json; \
	$(MERGE) $$B-{1..2}.json > $@ && mv $@ merged/UB2; \
	mapshaper $$B-1.json -erase merged/M/3.json -o force $$B-1.json; \
	mapshaper $$B-2.json -erase merged/M/3.json -o force $$B-2.json; \
	$(MERGE) $$B-{1..3}.json > $@ && mv $@ merged/UB3; \
	mapshaper $$B-2.json -erase merged/M/4.json -o force $$B-2.json; \
	mapshaper $$B-3.json -erase merged/M/4.json -o force $$B-3.json; \
	$(MERGE) $$B-{2..4}.json > $@ && mv $@ merged/UB4; \
	mapshaper $$B-3.json -erase merged/M/5.json -o force $$B-3.json; \
	mapshaper $$B-4.json -erase merged/M/5.json -o force $$B-4.json; \
	$(MERGE) $$B-{3..5}.json > $@ && mv $@ merged/UB5; \
	mapshaper $$B-4.json -erase merged/M/6.json -o force $$B-4.json; \
	mapshaper $$B-5.json -erase merged/M/6.json -o force $$B-5.json; \
	$(MERGE) $$B-{4..6}.json > $@ && mv $@ merged/UB6; \
	rm $$B*.json

merged: split
	rm -rf $@ && mkdir -p $@/UB{1..6}
	touch $@/.nobackup
	parallel --bar make $@/M/{}.json ::: {1..6}
	nice parallel -j50% --bar make ::: $(patsubst $</%.json,$@/%.json,$(wildcard $</*.json))
	# rm -f $@/*.json
	for F in $@/*/*1.json; do $(MERGE) $${F//1./?.} > $${F//1./.} && rm $${F//1./?.}; done
	# for F in $$(cd $@/UB6 && echo *.json); do $(MERGE) $@/UB?/$$F >$@/$$F; done
	mapshaper $</M_COVR.json -lines each='uband=A.uband||B.uband,cell=A.cell||B.cell' -o $@/M_COVR.json

# include only fields used in the style
Y=$(shell jq '.. | arrays | select(.[0]=="get" or .[0]=="has") | .[1]' styles/s57.json | sort | uniq | sed 's/^/-y /')

enc.tiles: merged
	tippecanoe $</M_COVR.json -f -y uband $(Y) -Z1 -z13 -j '{"*":["any",["all",["<","$$zoom",6]],["all",["<=","$$zoom",8],[">","uband",1]],["all",["<=","$$zoom",9],[">","uband",2]],["all",["<=","$$zoom",10],[">","uband",3]],["all",["<=","$$zoom",12],[">","uband",4]],["all",["<=","$$zoom",13],[">","uband",5]]]}' -o UB0.mbtiles # charts outlines
	nice tippecanoe $</UB1/*.json -f -r1 -ao -ac $(Y) -Z6  -z8  -o UB1.mbtiles ||true # 1 Overview
	nice tippecanoe $</UB2/*.json -f -r1 -ao -ac $(Y) -Z9  -z9  -o UB2.mbtiles ||true # 2 General
	nice tippecanoe $</UB3/*.json -f -r1 -ao -ac $(Y) -Z10 -z10 -o UB3.mbtiles ||true # 3 Coastal
	nice tippecanoe $</UB4/*.json -f -r1 -ao -ac $(Y) -Z11 -z12 -o UB4.mbtiles ||true # 4 Approach
	nice tippecanoe $</UB5/*.json -f -r1 -ao -ac $(Y) -Z13 -z13 -o UB5.mbtiles ||true # 5 Harbour
	nice tippecanoe $</UB6/*.json -f -r1 -ao -ac $(Y) -Z14 -z14 -o UB6.mbtiles ||true # 6 Berthing
	nice tile-join -n $(DST) -N "$(TODAY)" -A "$(ATT)" -f -o $(DST).mbtiles UB?.mbtiles
	pmtiles convert $(DST).mbtiles $(DST).pmtiles
	ls -lh *tiles
	mv $(DST).mbtiles data
	mv $(DST).pmtiles public
	rm UB*.mbtiles

fnc:
	rm -rf split merged
	make enc.tiles

styles: public/fnc-de.json

noaa:
	rm -rf split merged
	make enc.tiles SRC=../data/$@.layers DST=$@ ATT=NOAA

styles: public/noaa.json

rws: ../data/rws.layers
	rm -rf $@ && cp -r $< $@
	touch $@/.nobackup
	# for F in $@/*; do B=$${F#*/}; B=$${B%.*}; mv $$F $@/$${B^^}.json; done
	$(MERGE) $@/BOY*.json > $@/buoys.json
	$(MERGE) $@/BCN*.json > $@/beacons.json
	rm $@/BOY*.json $@/BCN*.json

	# mapshaper ../data/vwm/drijvend.s57.json -filter 'layer.startsWith("BOY")' -o $@/buoys.json
	# mapshaper ../data/vwm/drijvend.s57.json -filter 'layer=="LIGHTS"' -o $@/lights1.json
	# mapshaper ../data/vwm/drijvend.s57.json -filter 'layer=="TOPMAR"' -o $@/topmar1.json
	# # mapshaper ../data/vwm/vast.s57.json -filter 'layer.startsWith("BCN")' -o $@/beacons.json
	# mapshaper ../data/vwm/vast.s57.json -filter 'layer=="LIGHTS"' -o $@/lights2.json
	# mapshaper ../data/vwm/vast.s57.json -filter 'layer=="TOPMAR"' -o $@/topmar2.json
	# $(MERGE) $@/lights?.json > $@/LIGHTS.json && rm $@/lights?.json
	# $(MERGE) $@/topmar?.json > $@/TOPMAR.json && rm $@/topmar?.json

	mapshaper $@/DEPARE.json -each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' -dissolve areatype calc='DRVAL1=min(DRVAL1), DRVAL2=max(DRVAL2)' -o force $@/DEPARE.json
	mapshaper $@/DEPCNT.json -filter 'VALDCO<=0 || [1,2,3,5,10,20,50].includes(VALDCO)' -o force $@/DEPCNT.json
	mapshaper $@/SOUNDG.json -each 'VALSOU=DEPTH' -o force $@/SOUNDG.json
	mapshaper $@/M_COVR.json -filter 'CATCOV==1' -each 'cell=chart' -o force $@/M_COVR.json

rws.tiles: rws
	nice tippecanoe $</M_COVR.json $</LNDARE.json $</DEPARE.json $</COALNE.json $</BUAARE.json $</LNDRGN.json $</SEAARE.json -f -ao -ac -Z8 -z9 $(Y) -o $<0.mbtiles
	nice tippecanoe $</*.json -f -r1 -ao -ac -Z10 -z14 -y SCAMIN $(Y) -o $<1.mbtiles -j '{ "SOUNDG": ["any", ["all", ["==", "$$zoom", 11], [">=", "SCAMIN", 160000] ], ["all", ["==", "$$zoom", 12], [">=", "SCAMIN", 80000] ], ["all", ["==", "$$zoom", 13], [">=", "SCAMIN", 40000] ], ["all", [">=", "$$zoom", 14]] ], "buoys":[">=","$$zoom",11], "beacons":[">=","$$zoom",11], "LIGHTS":[">=","$$zoom",11], "TOPMAR":[">=","$$zoom",11], "DAYMAR":[">=","$$zoom",11], "DEPCNT":[">=","$$zoom",11] }'
	nice tile-join -n "fnc-nl" -N "$(TODAY)" -A "FNC/RWS" -f -o fnc-nl.mbtiles $<?.mbtiles
	pmtiles convert fnc-nl.mbtiles fnc-nl.pmtiles
	ls -lh *tiles
	mv fnc-nl.mbtiles data
	mv fnc-nl.pmtiles public
	rm $<*.mbtiles

styles: public/fnc-nl.json

tiles: enc.tiles rws.tiles

clean: clean-cache
	rm -rf dist split merged rws *.gpkg *.mbtiles *.pmtiles *@2x.yaml depth-de*

clean-cache:
	rm -rf cache_data

depth-de: merged/UB6
	rm -rf $@ && mkdir -p $@
	mapshaper $</DEPARE.json \
		-each 'contourarea="depth"' \
		-each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' \
		-dissolve allow-overlaps fields=contourarea,areatype \
		-o $@/DEPARE.json
	mapshaper $@/DEPARE.json -filter 'areatype==10' -erase $</LNDARE.json -o $@/DEPARE1.json
	mapshaper $@/DEPARE.json -filter 'areatype==5'  -erase $</LNDARE.json -o $@/DEPARE2.json
	mapshaper $@/DEPARE.json -filter 'areatype==2'  -erase $</LNDARE.json -o $@/DEPARE3.json
	mapshaper $@/DEPARE.json -filter 'areatype==0'  -erase $</LNDARE.json -o $@/DEPARE4.json
	mapshaper $@/DEPARE.json -filter 'areatype==-1' -erase $</LNDARE.json -o $@/DEPARE5.json
	$(MERGE) $@/DEPARE?.json >$@/DEPARE.json
	mapshaper $</DEPCNT.json \
		-filter 'VALDCO<0 || [0,1,2,3,4,5,10,20,50].includes(VALDCO)' \
		-each 'contour="depth"' \
		-each 'depth=VALDCO.toFixed(0)' \
		-each 'contourtype=VALDCO<0?"-1":[0,1,2,3,4,5,10,20,50].includes(VALDCO)?VALDCO.toFixed(0)+"m":VALDCO%1000==0?"1000":VALDCO%100==0?"100":VALDCO%10==0?"10":VALDCO%5==0?"5":"1"' \
		-dissolve contour,depth,contourtype \
		-o $@/DEPCNT.json
	mapshaper $</SOUNDG.json \
		-each 'point="depth"' \
		-each 'depth=VALSOU>10||VALSOU%10==0?VALSOU.toFixed(0):VALSOU.toFixed(1)' \
		-filter-fields point,depth \
		-o $@/SOUNDG.json
	ogr2ogr $@/$@.gpkg $@/DEPARE.json
	ogr2ogr $@/$@.gpkg $@/DEPCNT.json -append
	ogr2ogr $@/$@.gpkg $@/SOUNDG.json -append

depth-nl: rws
	rm -rf $@ && mkdir -p $@
	mapshaper $</DEPARE.json \
		-each 'contourarea="depth"' \
		-each 'areatype=DRVAL1>=10?10:DRVAL1>=5?5:DRVAL1>=2?2:DRVAL1>=0?0:-1' \
		-dissolve allow-overlaps fields=contourarea,areatype \
		-o $@/DEPARE.json
	mapshaper $</DEPCNT.json \
		-filter 'VALDCO<0 || [0,1,2,3,4,5,10,20,50].includes(VALDCO)' \
		-each 'contour="depth"' \
		-each 'depth=VALDCO.toFixed(0)' \
		-each 'contourtype=VALDCO<0?"-1":[0,1,2,3,4,5,10,20,50].includes(VALDCO)?VALDCO.toFixed(0)+"m":VALDCO%1000==0?"1000":VALDCO%100==0?"100":VALDCO%10==0?"10":VALDCO%5==0?"5":"1"' \
		-dissolve contour,depth,contourtype \
		-o $@/DEPCNT.json
	mapshaper $</SOUNDG.json \
		-each 'point="depth"' \
		-each 'depth=VALSOU>10||VALSOU%10==0?VALSOU.toFixed(0):VALSOU.toFixed(1)' \
		-filter-fields point,depth,SCAMIN \
		-o $@/SOUNDG3.json
	mapshaper $@/SOUNDG3.json -filter 'SCAMIN>=40000'  -o $@/SOUNDG2.json
	mapshaper $@/SOUNDG2.json -filter 'SCAMIN>=80000'  -o $@/SOUNDG1.json
	mapshaper $@/SOUNDG1.json -filter 'SCAMIN>=160000' -o $@/SOUNDG0.json
	for F in $@/*.json; do ogr2ogr $${F//.json/.gpkg} $$F; done

serve:
	make -B styles
	mkdir -p cache_data && touch cache_data/.nobackup
	docker compose up

mapproxy:
	mkdir -p cache_data && touch cache_data/.nobackup
	docker compose up $@

mapproxy@2x.yaml: mapproxy.yaml
	cp $< $@
	sed -i 's/s\.png/s@2x.png/g' $@
	sed -i 's/GLOBAL_WEBMERCATOR/GLOBAL_WEBMERCATOR\n    tile_size: [512, 512]/g' $@
	sed -i 's/#\s*tile_size/tile_size/g' $@
	sed -i -E 's/(fnc-[a-z]+)(:|])/\1@2x\2/g' $@

seed@2x.yaml: seed.yaml
	sed -E 's/(fnc-[a-z]+)/\1@2x/g' $< >$@

seed: seed$(R).yaml mapproxy$(R).yaml
	make -B styles OSM=none
	mkdir -p cache_data && touch cache_data/.nobackup
	docker compose up -d
	sleep 3
	docker compose exec -u mapproxy -T mapproxy mapproxy-seed -f /data/$(word 2,$^) -s /data/$<
	docker compose down
	ls -lh cache_data

seed2x:
	make seed R=@2x

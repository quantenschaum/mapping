# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR=OGR_S57_OPTIONS="RETURN_PRIMITIVES=ON,RETURN_LINKAGES=ON,LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)" ogr2ogr -skipfailures

help:
	cat README.md

unzip:
	for Z in *.zip; do unzip -o "$$Z"; done

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

nautical.render.xml:
	wget -O $@ https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

xmarine.render.xml: nautical.render.xml
	diff $< marine.render.xml -u >$@.diff || true
	cp $< $@
	patch $@ $@.diff

vwm:
	mkdir -p $@
	wget -O $@/drijvend.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_drijvend&outputFormat=json"
	wget -O $@/vast.json "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vaarweg_markering_vast&outputFormat=json"

OUT=shapes

convert: s57objectclasses.csv s57attributes.csv
	#rm -rf $(OUT)
	for F in $(IN)/*.000; do $(OGR) $(OUT) "$$F"; done
	#cd $(OUT) && rm *.prj *.shx *.dbf
	cd $(OUT) && for F in * ; do G=$${F%.*}; mv -n $${F} $${G^^}.$${F#*.}; done
	touch $(OUT)/.nobackup

shapes:
	$(MAKE) convert IN=*U7Inland_*/ENC_ROOT/*/*/*/

replace:
	for F in *.qgs; do echo $$F; sed 's#"INT1/#"./icons/INT1/#g' $$F -i; done

BSH=FORMAT=application/json;type=geojson&WIDTH=10000000&HEIGHT=10000000&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333

bsh:
	mkdir -p bsh
	for L in AidsAndServices Hydrography SkinOfTheEarth RocksWrecksObstructions Topography; do wget -O bsh/$$L.json "https://www.geoseaportal.de/wss/service/NAUTHIS_$$L/guest?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=1_Overview,2_General,3_Coastal,4_Approach,5_Harbour,6_Berthing&FORMAT=application/json;type=geojson&WIDTH=10000000&HEIGHT=10000000&CRS=EPSG:4326&BBOX=53,5.5,55.5,14.3333"; done

clean-tiles:
	rm -rf tiles/*/

clean-shapes:
	rm -rf shapes/

clean-bsh:
	rm -rf bsh/

clean-vwm:
	rm -rf vwm/

serve: replace
	QGIS_SERVER_ADDRESS=0.0.0.0 qgis_mapserver map.qgs

docker: replace
	docker-compose up -d
	@echo QGIS: http://localhost:8000

sync: replace
	rsync -hav --del --exclude tiles --exclude cache_data --exclude .git --delete-excluded ./ nas:docker/qgis $(O)
	touch tiles/.nobackup
	rsync -hav tiles/ nas:docker/maps/tiles/qgis/ $(O)


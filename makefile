# https://www.perrygeo.com/processing-s57-soundings.html
# https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc
# https://www.teledynecaris.com/s-57/frames/S57catalog.htm

SHELL=/bin/bash
OGR=OGR_S57_OPTIONS="RETURN_PRIMITIVES=ON,RETURN_LINKAGES=ON,LNAM_REFS=ON,SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,LIST_AS_STRING=ON,UPDATES=APPLY" S57_CSV="$(PWD)" ogr2ogr -skipfailures

help:
	cat README.md

unzip:
	unzip -o *Inland_Waddenzee_week*.zip

%.csv:
	wget https://github.com/OpenCPN/OpenCPN/raw/master/data/s57data/$@

convert: s57objectclasses.csv s57attributes.csv
	rm -rf $(OUT)
	for F in $(IN)/*.000; do $(OGR) $(OUT) "$$F"; done
	#cd $(OUT) && rm *.prj *.shx *.dbf
	cd $(OUT) && for F in * ; do G=$${F%.*}; mv -n $${F} $${G^^}.$${F#*.}; done
	touch $(OUT)/.nobackup

.PHONY: waddenzee zeeland nederland rotterdam us

waddenzee:
	$(MAKE) convert OUT=$@ IN=*Inland_Waddenzee_week*/ENC_ROOT/*/*/*/

zeeland:
	$(MAKE) convert OUT=$@ IN=*Inland_Zeeland_week*/ENC_ROOT/*/*/*/

nederland:
	$(MAKE) convert OUT=$@ IN=Nederland*/ENC_ROOT/*/
	
rotterdam:
	$(MAKE) convert OUT=$@ IN=Port*/
	
us:
	$(MAKE) convert OUT=$@ IN=02Region_ENCs/ENC_ROOT/*/

copy:
	for F in zeeland nederland rotterdam us; do sed "s/waddenzee/$$F/g" waddenzee.qgs >$$F.qgs; done
	
replace:
	for F in *.qgs; do sed 's#"INT1/#"./icons/INT1/#g' $$F -i; done

sync:
	touch tiles/.nobackup
	rsync -hav --del tiles/ nas:docker/maps/tiles/qgis/
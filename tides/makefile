SHELL=/bin/bash

all:
	$(MAKE) seed HOUR=-6
	$(MAKE) seed HOUR=-5
	$(MAKE) seed HOUR=-4
	$(MAKE) seed HOUR=-3
	$(MAKE) seed HOUR=-2
	$(MAKE) seed HOUR=-1
	$(MAKE) seed HOUR=+0
	$(MAKE) seed HOUR=+1
	$(MAKE) seed HOUR=+2
	$(MAKE) seed HOUR=+3
	$(MAKE) seed HOUR=+4
	$(MAKE) seed HOUR=+5
	$(MAKE) seed HOUR=+6
	$(MAKE) seed SEEDS=figures

qgis:
	QGIS_SERVER_PARALLEL_RENDERING=1 qgis_mapserver &>/dev/null

mapproxy: mapproxy-x.yaml
	mapproxy-util serve-develop $< -b 0.0.0.0:8001

seed: mapproxy-x.yaml
	echo SEEDS=$(SEEDS) HOUR=$(HOUR)
	mapproxy-seed -f $< -s seed.yaml --seed=$(SEEDS)

HOUR=+0
SEEDS=northsea,coast
.PHONY: mapproxy-x.yaml
mapproxy-x.yaml:
	cp mapproxy.yaml $@
	sed 's/hw+0/hw$(HOUR)/' mapproxy-x.yaml -i
	sed 's/"hwhour" = 0/"hwhour" = $(HOUR)/' mapproxy-x.yaml -i

clean-cache:
	rm -rf cache_data

convert: $(subst cache_data/,,$(wildcard cache_data/*.mbtiles)) \
         $(subst .mbtiles,.sqlitedb,$(subst cache_data/,,$(wildcard cache_data/*.mbtiles))) \
         $(subst .mbtiles,.gemf,$(subst cache_data/,,$(wildcard cache_data/*.mbtiles)))

unpack:  $(subst .mbtiles,/,$(subst cache_data/,,$(wildcard cache_data/*.mbtiles)))

%.mbtiles: cache_data/%.mbtiles
	../convert.py -yf $< $@ -t "$(basename $@) `date +%F`"

%.sqlitedb: cache_data/%.mbtiles
	../convert.py -yf $< $@ -t "$(basename $@) `date +%F`"

%/: cache_data/%.mbtiles
	../convert.py -yf $< $@

%.gemf: %.mbtiles
	../data/chartconvert/convert_mbtiles.py tms $@ $<

zip:
	zip tides.mbtiles.zip *.mbtiles
	zip tides.sqlitedb.zip *.sqlitedb
	zip tides.gemf.zip *.gemf

clean:
	rm -frv *.mbtiles *.sqlitedb *.gemf mapproxy-x.yaml hw*/ fig/

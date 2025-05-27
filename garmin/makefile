SHELL=/bin/bash

MKGMAP=java -jar mkgmap/mkgmap.jar
SPLIT =java -jar splitter/splitter.jar
#--keep-going

help:
	$(MKGMAP) --help=options >$@

typ: marine.typ

%.typ: %.txt
	$(MKGMAP) $<

FAMILY=4200
PRODUCT=1
MAPID=42000001

OSM=../osm/depth-de.osm ../osm/soundg-de.osm ../osm/buoys.osm ../osm/beacons.osm ../osm/lights.osm

split:
	$(SPLIT) --mapid=$(MAPID) $(OSM)
	ls -lh *.pbf

map:
	$(MKGMAP) --mapname=$(MAPID) --family-id=$(FAMILY) --product-id=$(PRODUCT) --custom --gmapsupp --latin1 --style-file=marine --family-name=QMAP --description=depth-de $(OSM)
	ls -lh gmapsupp.img

merge:
	$(MKGMAP) --gmapsupp $(MAPID).img other/*.img
	ls -lh gmapsupp.img

upload:
	cp -v gmapsupp.img /media/*/*/garmin/

clean:
	rm -f *.typ *.img *.tdb *.pbf

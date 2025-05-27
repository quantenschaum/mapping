SHELL=/bin/bash

MKGMAP=java -jar mkgmap/mkgmap.jar
#--keep-going

help:
	$(MKGMAP) --help=options >$@

typ: marine.typ

%.typ: %.txt
	$(MKGMAP) $<

FAMILY=4200
PRODUCT=1

map:
	$(MKGMAP) --max-jobs --family-id=$(FAMILY) --product-id=$(PRODUCT) --custom --gmapsupp --latin1 --style-file=marine --family-name=QMAP --description=depth-de ../osm/depth-de.osm ../osm/soundg-de.osm
	ls -lh gmapsupp.img

upload:
	cp -v gmapsupp.img /media/*/*/garmin/

merge:
	$(MKGMAP) --gmapsupp 6*.img other/*.img

clean:
	rm -f *.typ *.img *.tdb

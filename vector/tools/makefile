all: pmtiles spreet tippecanoe
	mkdir -p bin
	touch .nobackup
	ln -sr pmtiles/go-pmtiles bin/pmtiles
	ln -sr spreet/target/release/spreet bin/
	ln -sr tippecanoe/tippecanoe* tippecanoe/tile-join bin/

pmtiles:
	git clone --depth=1 https://github.com/protomaps/go-pmtiles.git $@
	cd $@ && go build

spreet:
	git clone --depth=1 https://github.com/flother/spreet $@
	cd $@ && cargo build --release

tippecanoe:
	git clone --depth=1 https://github.com/felt/tippecanoe.git $@
	make -C $@ -j

clean:
	rm -rf bin pmtiles spreet tippecanoe

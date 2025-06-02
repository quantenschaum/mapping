
xmls: nautical.render.xml depthcontourlines.addon.render.xml rendering_types.xml

%.render.xml:
	wget -O $(subst .xml,.0.xml,$@) https://github.com/osmandapp/OsmAnd-resources/raw/master/rendering_styles/$@

rendering_types.xml:
	wget -O $(subst .xml,.0.xml,$@) https://github.com/osmandapp/OsmAnd-resources/raw/master/obf_creation/rendering_types.xml

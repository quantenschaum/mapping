document.addEventListener("DOMContentLoaded", () => {
  function d2dm(a,n){
      deg = (new URL(document.location)).searchParams.get("deg");
      if(deg) {
          n=parseInt(deg);
          f=Math.pow(10,n);
          return Math.round(a*f)/f;
      }
      a=Math.abs(a);
      d=Math.floor(a);
      f=Math.pow(10,n);
      m=Math.round(((60*a)%60)*f)/f;
      while(m>=60) { m-=60; d+=1; }
      M=m==0?"":m.toFixed(n).replace(/\.?0+$/,"")+"'";
      return d+'°'+M;
  }

  var grid=L.latlngGraticule({
  showLabel: true,
  color: '#222',
  zoomInterval: [
          {start: 2, end: 4, interval: 30},
          {start: 5, end: 5, interval: 20},
          {start: 6, end: 6, interval: 10},
          {start: 7, end: 7, interval: 5},
          {start: 8, end: 8, interval: 2},
          {start: 9, end: 9, interval: 1},
          {start: 10, end: 10, interval: 30/60},
          {start: 11, end: 11, interval: 15/60},
          {start: 12, end: 12, interval: 10/60},
          {start: 13, end: 13, interval: 5/60},
          {start: 14, end: 14, interval: 2/60},
          {start: 15, end: 15, interval: 1/60},
          {start: 16, end: 16, interval: 1/60/2},
          {start: 17, end: 17, interval: 1/60/5},
          {start: 18, end: 18, interval: 1/60/10},
      ],
      latFormatTickLabel: function(l){
          s=l<0?'S':l>0?'N':'';
          return s+d2dm(l,2);
      },
      lngFormatTickLabel: function(l){
          l%=360;
          l-=Math.abs(l)>180?Math.sign(l)*360:0;
          s=l<0?'W':l>0?'E':'';
          return s+d2dm(l,2);
      },
  });

  var basemaps = {
    'OpenStreetMap ORG':L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
    }),
    'OpenStreetMap DE':L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
      attribution: '<a href="https://openstreetmap.de/">OpenStreetMap</a>'
    }),
    'OsmAnd Nautical':L.tileLayer('https://maptile.osmand.net/tile/nautical/{z}/{x}/{y}.png', {
      attribution: '<a href="https://osmand.net/map">OsmAnd</a>'
    }),
    'ENC (RWS)':L.tileLayer.wms('https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/WMSServer', {
      layers:'0,2,3,4,5,6,7',
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      attribution: '<a href="https://rijkswaterstaat.nl/">RWS</a> <a href="https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/">Chart Server</a>'
     }),
    'Worldy Imagery':L.tileLayer('https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '<a href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">ArcGIS ESRI World Imagery</a>'
    }),
    'Luchtfoto 2023 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2023_quick_orthoLR',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2023 8cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2023_quick_orthoHR',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2022 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2022_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2021 8cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2021_orthoHR',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2020 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2020_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2019 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2019_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2018 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2018_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2017 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2017_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2016 25cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2016_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
  };

  var overlays = {
    'Grid': grid,
    'ENC':L.tileLayer('enc/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS ENC</a>, <a href="https://www.bsh.de/DE/THEMEN/Geoinformationen/geoinformationen_node.html">BSH GeoSeaPortal</a>'
    }),
    'Depth Contours':L.tileLayer('contours/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS ENC</a>, <a href="https://www.bsh.de/DE/THEMEN/Geoinformationen/geoinformationen_node.html">BSH GeoSeaPortal</a>'
    }),
    'Buoys and Beacons':L.tileLayer('seamarks/{z}/{x}/{y}.png', {
      attribution: '<a href="https://data.overheid.nl/dataset/2c5f6817-d902-4123-9b1d-103a0a484979">RWS Buoys</a>, <a href="https://data.overheid.nl/dataset/c3d9facc-5b74-4cae-8841-135890f44049">RWS Beacons</a>, <a href="https://www.bsh.de/DE/THEMEN/Geoinformationen/geoinformationen_node.html">BSH GeoSeaPortal</a>'
    }),
    'Vaarweg Markeringen':L.tileLayer.wms('https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows', {
      layers:'vaarweg_markering_drijvend,vaarweg_markering_drijvend_detail,vaarweg_markering_vast,vaarweg_markering_vast_detail',
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      attribution: '<a href="https://data.overheid.nl/dataset/2c5f6817-d902-4123-9b1d-103a0a484979">RWS Buoys</a> <a href="https://data.overheid.nl/dataset/c3d9facc-5b74-4cae-8841-135890f44049">RWS Beacons</a>'
     }),
    'OpenSeaMap':L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
      attribution: '<a href="https://openseamap.org/">OpenSeaMap</a>'
    }),
  };

  for (let i = -6; i <= 6; i++) {
    let s=(i>=0?'+':'')+i;
    overlays['Tide HW Helgoland '+s+'h']=L.tileLayer('tides/'+s+'/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.bsh.de/DE/THEMEN/Geoinformationen/geoinformationen_node.html">BSH GeoSeaPortal</a>'
    });
  }
  overlays['Tide Figures']=L.tileLayer('tides/fig/{z}/{x}/{y}.png', {
    attribution: '<a href="https://www.bsh.de/DE/THEMEN/Geoinformationen/geoinformationen_node.html">BSH GeoSeaPortal</a>'
  });

  var layers = [basemaps['OpenStreetMap ORG'], overlays['Grid'], overlays['ENC']];

  if(document.URL.startsWith('file') || document.URL.includes('localhost')) {
    overlays['QGIS ENC'] = L.tileLayer('http://localhost:8001/tiles/enc/EPSG3857/{z}/{x}/{y}.png');
    overlays['QGIS Buoys and Beacons'] = L.tileLayer('http://localhost:8001/tiles/bnb/EPSG3857/{z}/{x}/{y}.png');
  }

  var map = L.map('map', {
    center: [52.8907,5.4128],
    zoom: 10,
    layers: layers,
    minZoom: 8,
    maxZoom: 16,
  });

  var layers=L.control.layers(basemaps, overlays, {collapsed: true}).addTo(map);

  function restoreActiveLayers(){
    var active=sessionStorage.getItem("activeLayers");
//    console.log(active);
    if(!active){ return; }
    active=JSON.parse(active);
//    console.log(active);
    for(let i=0;i<layers._layers.length;i++){
      let l=layers._layers[i];
      if(active.includes(i)){
        map.addLayer(l.layer);
      }else{
        map.removeLayer(l.layer);
      }
    }
  }

  restoreActiveLayers();

  function storeActiveLayers(){
    var active=[];
    for(let i=0;i<layers._layers.length;i++){
      let l=layers._layers[i];
//      console.log(i,map.hasLayer(l.layer));
      if(map.hasLayer(l.layer)) {
        active.push(i);
      }
    }
//    console.log("active",active);
    sessionStorage.setItem("activeLayers",JSON.stringify(active));
  }

  storeActiveLayers();

  map.on('layeradd layerremove overlayadd overlayremove',storeActiveLayers);


  new L.Hash(map); // try https://github.com/KoGor/leaflet-fullHash

  L.control.polylineMeasure({
      unit: 'nauticalmiles',
      clearMeasurementsOnStop: false,
      showBearings: true,
      showClearControl: true,
      showUnitControl: true,
  }).addTo(map);

  map.on('contextmenu',(e) => {
    var b=map.getBounds();
    L.popup()
    .setLatLng(e.latlng)
    .setContent('<button id="b1" type="button">Edit in JOSM</button>')
    .addTo(map)
    .openOn(map);
    $('#b1').click(function() {
      $.get('http://localhost:8111/'+(map.getZoom()>13?'load_and_zoom':'zoom'),{
        left:b.getWest(),
        right:b.getEast(),
        bottom:b.getSouth(),
        top:b.getNorth()
      });
      $.get('http://localhost:8111/imagery',{
        name:'Waddenzee',
        type:'tms',
        url:'http://waddenzee.duckdns.org/{zoom}/{x}/{y}.png'
      });
      $.get('http://localhost:8111/imagery',{
        name:'OpenStreetMap',
        type:'tms',
        url:'https://tile.openstreetmap.org/{zoom}/{x}/{y}.png'
      });
    });
  });

  L.chartTools({urlPrefix:''}).addTo(map);
});

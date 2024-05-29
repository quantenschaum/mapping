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
    'OpenStreetMap':L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    //'OpenStreetMap':L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.openstreetmap.org/">OpenStreetMap</a>',
      class:'grayscale',
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
      layers:'2023_ortho25',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
    'Luchtfoto 2023 8cm':L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
      layers:'2023_orthoHR',
      version:'1.3.0',
      transparent:'true',
      format:'image/jpg',
      attribution: '<a href="https://www.pdok.nl/">PDOK</a>'
    }),
  };

  var overlays = {
    'Grid': grid,
    'EMODnet Bathymetry':L.tileLayer.wms('https://ows.emodnet-bathymetry.eu/wms', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: 'emodnet:mean_multicolour',
      attribution: '<a href="https://emodnet.ec.europa.eu/">EMODnet</a>',
      class:"invert"
    }),
    'QMAP DE':L.tileLayer.fallback('qmap-de/{z}/{x}/{y}.png', {
      attribution: '<a href="/download/">QMAP</a> <a href="https://creativecommons.org/publicdomain/zero/1.0/">(CC0)</a>'
    }),
    'QMAP NL':L.tileLayer.fallback('qmap-nl/{z}/{x}/{y}.png', {
      attribution: '<a href="/download/">QMAP</a> <a href="https://creativecommons.org/publicdomain/zero/1.0/">(CC0)</a>'
    }),
    'BSH SkinOfEarth':L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_SkinOfTheEarth/ows', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: 'Coastal_Depth_area,Approach_Depth_area,Harbour_Depth_area',
      attribution: '<a href="https://www.bsh.de/DE/DATEN/GeoSeaPortal/geoseaportal_node.html">BSH GeoSeaPortal</a>'
    }),
    'BSH Hydro':L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_Hydrography/ows', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: '4_Approach',
      attribution: '<a href="https://www.bsh.de/DE/DATEN/GeoSeaPortal/geoseaportal_node.html">BSH GeoSeaPortal</a>'
    }),
    'BSH NavAids':L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_AidsAndServices/ows', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: 'Coastal_Lights,Coastal_Lateral_Buoys,Coastal_Cardinal_Buoys,Coastal_All_Other_Buoys,Coastal_Lateral_Beacons,Coastal_Cardinal_Beacons,Coastal_All_Other_Beacons,Approach_Lights,Approach_Lateral_Buoys,Approach_Cardinal_Buoys,Approach_All_Other_Buoys,Approach_Lateral_Beacons,Approach_Cardinal_Beacons,Approach_All_Other_Beacons,Harbour_Lights,Harbour_Lateral_Buoys,Harbour_Cardinal_Buoys,Harbour_All_Other_Buoys,Harbour_Lateral_Beacons,Harbour_Cardinal_Beacons,Harbour_All_Other_Beacons,Berthing_Lights,Berthing_Lateral_Buoys,Berthing_Cardinal_Buoys,Berthing_All_Other_Buoys,Berthing_Lateral_Beacons,Berthing_Cardinal_Beacons,Berthing_All_Other_Beacons',
      attribution: '<a href="https://www.bsh.de/DE/DATEN/GeoSeaPortal/geoseaportal_node.html">BSH GeoSeaPortal</a>'
    }),
    'BSH Topo':L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_Topography/ows', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: '4_Approach,5_Harbour',
      attribution: '<a href="https://www.bsh.de/DE/DATEN/GeoSeaPortal/geoseaportal_node.html">BSH GeoSeaPortal</a>'
    }),
    'BSH Obstr':L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_RocksWrecksObstructions/ows', {
      version:'1.3.0',
      transparent:'true',
      format:'image/png',
      layers: '4_Approach,5_Harbour',
      attribution: '<a href="https://www.bsh.de/DE/DATEN/GeoSeaPortal/geoseaportal_node.html">BSH GeoSeaPortal</a>'
    }),
    'Vaarweg Markeringen':L.tileLayer.wms('https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows', {
      layers:'vaarweg_markering_drijvend,vaarweg_markering_vast',
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
    overlays['Tide HW Helgoland '+s+'h']=L.tileLayer.fallback('tides/hw'+s+'/{z}/{x}/{y}.png', {
      attribution: '<a href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH Tidal Atlas</a>'
    });
  }
  overlays['Tide Figures']=L.tileLayer.fallback('tides/fig/{z}/{x}/{y}.png', {
    attribution: '<a href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH Tidal Atlas</a>'
  });

  var layers = [basemaps['OpenStreetMap'], overlays['Grid'], overlays['QMAP DE'], overlays['QMAP NL']];

  var isLocal=document.URL.startsWith('file') || document.URL.includes('localhost');

  if(isLocal) {
    overlays['QGIS'] = L.tileLayer('http://localhost:8001/tiles/qmap-de/EPSG3857/{z}/{x}/{y}.png');
  }


  var map = L.map('map', {
    center: [54.264,9.196],
    zoom: 8,
    layers: layers,
    minZoom: 6,
    maxZoom: 18,
  });

  var layers=L.control.layers(basemaps, overlays, {collapsed: true}).addTo(map);

  basemaps['OpenStreetMap'].getContainer().classList.add('grayscale');
  map.on('baselayerchange', function(evt) {
    //console.log(evt);
    if(evt.layer.options.class) {
      evt.layer.getContainer().classList.add(evt.layer.options.class);
    }
  });
  map.on('layeradd', function(evt) {
//    console.log(evt);
    if(evt.layer.options.class) {
      evt.layer.getContainer().classList.add(evt.layer.options.class);
    }
  });

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

  L.control.opacity(overlays, {collapsed: true}).addTo(map);

  map.on('contextmenu',(e) => {
    var b=map.getBounds();
    L.popup()
    .setLatLng(e.latlng)
    .setContent('<button id="b1" type="button">Edit in JOSM</button><p>You need to have JOSM running and remote control enabled.</p>')
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
        url:'http://waddenzee.duckdns.org/qmap-de/{zoom}/{x}/{y}.png'
      });
      $.get('http://localhost:8111/imagery',{
        name:'OpenStreetMap',
        type:'tms',
        url:'https://tile.openstreetmap.org/{zoom}/{x}/{y}.png'
      });
    });
  });

  L.chartTools({urlPrefix:''}).addTo(map);

  var tides=false;

  L.control.timelineSlider({
        timelineItems: ["off","-6h","-5h","-4h","-3h","-2h","-1h","HW Helgoland","+1h","+2h","+3h","+4h","+5h","+6h","Figures"],
        labelWidth:"40px",
        betweenLabelAndRangeSpace:"10px",
        changeMap: function(p){
          var x=p.label.replace("HW Helgoland","+0h");
          var t=x!="off";
//          console.log(x);
          Object.entries(overlays).forEach(l=>{
//            console.log(l);
            var name=l[0],layer=l[1];
              if(name.includes(x)) {
//                console.log("+",name);
                map.addLayer(layer);
              } else if(name.includes("Tide") || !tides && t) {
//                console.log("-",name);
                map.removeLayer(layer);
              }
          });
          tides=t;
        }
     }).addTo(map);
});

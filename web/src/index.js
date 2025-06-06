import './manifest.json';
import './icon.png';
import './style.css';

import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-hash';
import 'leaflet-graticule';
import 'leaflet.tilelayer.fallback';
import 'leaflet.polylinemeasure';
import 'leaflet.polylinemeasure/Leaflet.PolylineMeasure.css';
import 'leaflet.control.opacity';
import 'leaflet.nauticscale/dist/leaflet.nauticscale';
import './leaflet-timeline-slider';

const params = new URLSearchParams(window.location.search);
console.log(params.get('l'));

if ('serviceWorker' in navigator && params.get('app')=='1') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('service-worker.js')
      .then(reg => console.log('SW registered', reg))
      .catch(err => console.error('SW registration failed', err));
  });
}

const debug = process.env.NODE_ENV === 'development';

function d2dm(a, n) {
  const dec = params.get('dec');
  if (dec) {
    var n = parseInt(dec);
    var f = Math.pow(10, n);
    return Math.round(a * f) / f;
  }
  var a = Math.abs(a);
  var d = Math.floor(a);
  var f = Math.pow(10, n);
  var m = Math.round(((60 * a) % 60) * f) / f;
  while (m >= 60) {
    m -= 60;
    d += 1;
  }
  var M = m == 0 ? "" : m.toFixed(n).replace(/\.?0+$/, "") + "'";
  return d + '°' + M;
}

const grid = L.latlngGraticule({
  showLabel: true,
  color: '#222',
  zoomInterval: [
    {start: 2, end: 4, interval: 30},
    {start: 5, end: 5, interval: 20},
    {start: 6, end: 6, interval: 10},
    {start: 7, end: 7, interval: 5},
    {start: 8, end: 8, interval: 2},
    {start: 9, end: 9, interval: 1},
    {start: 10, end: 10, interval: 30 / 60},
    {start: 11, end: 11, interval: 15 / 60},
    {start: 12, end: 12, interval: 10 / 60},
    {start: 13, end: 13, interval: 5 / 60},
    {start: 14, end: 14, interval: 2 / 60},
    {start: 15, end: 15, interval: 1 / 60},
    {start: 16, end: 16, interval: 1 / 60 / 2},
    {start: 17, end: 17, interval: 1 / 60 / 5},
    {start: 18, end: 18, interval: 1 / 60 / 10},
  ],
  latFormatTickLabel: function (l) {
    let s = l < 0 ? 'S' : l > 0 ? 'N' : '';
    return s + d2dm(l, 2);
  },
  lngFormatTickLabel: function (l) {
    l %= 360;
    l -= Math.abs(l) > 180 ? Math.sign(l) * 360 : 0;
    let s = l < 0 ? 'W' : l > 0 ? 'E' : '';
    return s + d2dm(l, 2);
  },
});

const boundsDE = L.latLngBounds([53.0, 3.3], [56.0, 14.4]);
const boundsNL = L.latLngBounds([51.2, 3.0], [53.8, 7.3]);

const baseurl = 'https://freenauticalchart.net';

const basemaps = {
  'OpenStreetMap': L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    class: 'grayscale',
  }),
  'OsmAnd Nautical': L.tileLayer('https://maptile.osmand.net/tile/nautical/{z}/{x}/{y}.png', {
    attribution: '<a target="_blank" href="https://osmand.net/map">OsmAnd</a>'
  }),
  'ENC (RWS)': L.tileLayer.wms('https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/WMSServer', {
    layers: '0,2,3,4,5,6,7',
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    attribution: '<a target="_blank" href="https://rijkswaterstaat.nl/">RWS</a> <a target="_blank" href="https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/">Chart Server</a>',
    bounds: boundsNL,
  }),
  'Worldy Imagery': L.tileLayer('https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '<a target="_blank" href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">World Imagery</a>'
  }),
  'Luchtfoto 25cm': L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
    layers: 'Actueel_ortho25',
    version: '1.3.0',
    transparent: 'true',
    format: 'image/jpg',
    tiled: true,
    attribution: '<a target="_blank" href="https://www.pdok.nl/">PDOK</a>',
    bounds: boundsNL,
  }),
  'Luchtfoto 8cm': L.tileLayer.wms('https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0', {
    layers: 'Actueel_orthoHR',
    version: '1.3.0',
    transparent: 'true',
    format: 'image/jpg',
    tiled: true,
    attribution: '<a target="_blank" href="https://www.pdok.nl/">PDOK</a>',
    bounds: boundsNL,
  }),
};

const overlays = {
  'Grid': grid,
  'QMAP DE': L.tileLayer.fallback(baseurl + '/qmap-de/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP DE</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH</a>)',
    bounds: boundsDE,
  }),
  'QMAP Contours DE': L.tileLayer.fallback(baseurl + '/contours-de/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP Contours DE</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH</a>)',
    bounds: boundsDE,
  }),
  'QMAP Soundings DE': L.tileLayer.fallback(baseurl + '/soundg-de/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP Soundings DE</a> (<a target="_blank" href="https://gdi.bsh.de/de/feed/Hoehe-Bathymetrie.xml">BSH</a>)',
    bounds: boundsDE,
  }),
  'QMAP NL': L.tileLayer.fallback(baseurl + '/qmap-nl/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP NL</a> (<a target="_blank" href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS</a>)',
    bounds: boundsNL,
  }),
  'EMODnet Bathymetry': L.tileLayer.wms('https://ows.emodnet-bathymetry.eu/wms', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: 'emodnet:mean_multicolour',
    attribution: '<a target="_blank" href="https://emodnet.ec.europa.eu/">EMODnet</a>',
    class: "invert"
  }),
  'BSH Bathymetry': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/ELC_INSPIRE/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    layers: 'EL.GridCoverage',
    attribution: '<a target="_blank" href="https://inspire-geoportal.ec.europa.eu/srv/api/records/5afbd3f9-8bd8-4bfc-a77c-ac3de4ace07f">BSH Bathymetry</a>',
    bounds: boundsDE,
  }),
  'BSH SkinOfEarth': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_SkinOfTheEarth/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: 'Coastal_Depth_area,Approach_Depth_area,Harbour_Depth_area',
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
    bounds: boundsDE,
  }),
  'BSH Hydro': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_Hydrography/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: 'Approach_Depths,Approach_Fishing_Facility_Marine_Farm_Areas,Approach_Offshore_Installations,Approach_Areas_Limits',
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
    bounds: boundsDE,
  }),
  'BSH NavAids': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_AidsAndServices/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: 'Coastal_Lights,Coastal_Lateral_Beacons,Coastal_Cardinal_Beacons,Coastal_All_Other_Beacons,Coastal_Lateral_Buoys,Coastal_Cardinal_Buoys,Coastal_All_Other_Buoys,Coastal_Fog_Signals_Daymarks,Approach_Lights,Approach_Lateral_Beacons,Approach_Cardinal_Beacons,Approach_All_Other_Beacons,Approach_Lateral_Buoys,Approach_Cardinal_Buoys,Approach_All_Other_Buoys,Approach_Fog_Signals_Daymarks,Harbour_Lights,Harbour_Lateral_Beacons,Harbour_Cardinal_Beacons,Harbour_All_Other_Beacons,Harbour_Lateral_Buoys,Harbour_Cardinal_Buoys,Harbour_All_Other_Buoys,Harbour_Fog_Signals_Daymarks',
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
    bounds: boundsDE,
  }),
  'BSH Topo': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_Topography/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: '4_Approach,5_Harbour',
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
    bounds: boundsDE,
  }),
  'BSH Obstr': L.tileLayer.wms('https://gdi.bsh.de/mapservice_gs/NAUTHIS_RocksWrecksObstructions/ows', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: '4_Approach,5_Harbour',
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>'
  }),
  'BSH Contours': L.tileLayer.wms('https://gdi.bsh.de/en/mapservice/Elevation-depth-contours-WMS', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    layers: 'EL.ContourLine',
    attribution: '<a target="_blank" href="https://inspire-geoportal.ec.europa.eu/srv/api/records/cee22cf8-60c0-401b-8a98-e01959b66f9b">BSH Contours</a>',
    bounds: boundsDE,
  }),
  'Vaarweg Markeringen': L.tileLayer.wms('https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows', {
    layers: 'vaarweg_markering_drijvend,vaarweg_markering_vast',
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    attribution: '<a target="_blank" href="https://data.overheid.nl/dataset/5eb0f65c-e90f-464e-8f46-01c5eeb6adf5">RWS Buoys</a> <a target="_blank" href="https://data.overheid.nl/dataset/2bf96f3b-128d-4506-85e0-08e8fc19a11c">RWS Beacons</a>'
  }),
  'OpenSeaMap': L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
    attribution: '<a target="_blank" href="https://openseamap.org/">OpenSeaMap</a>',
    bounds: boundsNL,
  }),
};

for (let i = -6; i <= 6; i++) {
  let s = (i >= 0 ? '+' : '') + i;
  overlays['Tide HW Helgoland ' + s + 'h'] = L.tileLayer.fallback(baseurl + '/tides/hw' + s + '/{z}/{x}/{y}.webp', {
    attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH Tidal Atlas</a>',
    tide: true
  });
}
overlays['Tide Figures'] = L.tileLayer.fallback(baseurl + '/tides/fig/{z}/{x}/{y}.webp', {
  attribution: '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH Tidal Atlas</a>'
});

const map = L.map('map', {
  center: [54.264, 9.196],
  zoom: 8,
  layers: [basemaps['OpenStreetMap'], overlays['Grid'], overlays['QMAP DE'], overlays['QMAP Soundings DE'], overlays['QMAP NL']],
  // layers: [basemaps['OpenStreetMap'], overlays['Grid']],
  minZoom: 7,
  maxZoom: 18,
});

map.attributionControl.setPrefix('<a class="highlight" href="/download/">QMAP (download and more)</a>, <a href="https://leafletjs.com/">Leaflet</a>');

fetch('/updated').then(response => {
  let dateHeader = response.headers.get('Last-Modified');
  let date = new Date(dateHeader).toISOString().slice(0, 10);
  map.attributionControl.setPrefix('<a class="highlight" href="/download/">QMAP (download and more, last updated ' + date + ')</a>, <a href="https://leafletjs.com/">Leaflet</a>');
});

new L.Hash(map);

map.addControl(new L.Control.ScaleNautic({
  metric: true, imperial: false, nautic: true
}));

const layers = L.control.layers(basemaps, overlays, {collapsed: true}).addTo(map);

basemaps['OpenStreetMap'].getContainer().classList.add('grayscale');
map.on('baselayerchange', function (evt) {
  //console.log(evt);
  if (evt.layer.options.class) {
    evt.layer.getContainer().classList.add(evt.layer.options.class);
  }
});
map.on('layeradd', function (evt) {
//    console.log(evt);
  if (evt.layer.options.class) {
    evt.layer.getContainer().classList.add(evt.layer.options.class);
  }
});

L.control.polylineMeasure({
  unit: 'nauticalmiles',
  clearMeasurementsOnStop: false,
  showBearings: true,
  showClearControl: true,
  showUnitControl: true,
}).addTo(map);


var opacity = L.control.opacity();

map.on('overlayadd overlayremove', function (e) {
  map.removeControl(opacity);
  var activeOverlays = Object.fromEntries(Object.entries(overlays).filter(([k, v]) => !k.includes("Grid") && !v.options.tide && map.hasLayer(v)));
  console.log('active overlays', activeOverlays);
  if (Object.keys(activeOverlays).length) {
    opacity = L.control.opacity(activeOverlays, {collapsed: true});
    map.addControl(opacity);
  }
});

L.control.timelineSlider({
  timelineItems: ["off", "-6h", "-5h", "-4h", "-3h", "-2h", "-1h", "HW Helgoland", "+1h", "+2h", "+3h", "+4h", "+5h", "+6h"],
  labelWidth: "40px",
  betweenLabelAndRangeSpace: "10px",
  changeMap: function (p) {
    var x = p.label.replace("HW Helgoland", "+0h");
//          console.log(p,x);
    Object.entries(overlays).forEach(l => {
      var name = l[0], layer = l[1];
      if (!layer.options.tide) {
        return;
      }
//            console.log(l);
      if (name.includes(x)) {
        map.addLayer(layer);
      } else if (layer.options.tide) {
        map.removeLayer(layer);
      }
    });
  }
}).addTo(map);


const nightswitch = L.Control.extend({
  onAdd: (m) => {
    console.log('nightswitch');
    var div = L.DomUtil.create('div','nightswitch');
    var button = L.DomUtil.create('button', 'nightswitch');
    button.innerHTML = '&#x1F319;'; // 🌙
    button.title = 'toggle night mode';
    div.appendChild(button);
    button.addEventListener('click', () => {
      const map = document.querySelector('#map');
      if (map.classList.contains('night')) {
        map.classList.remove('night');
      } else {
        map.classList.add('night');
      }
    });
    return div;
  },

});


new nightswitch({position: 'topleft'}).addTo(map);


function restoreActiveLayers(l) {
  var active = sessionStorage.getItem("activeLayers");
  active = JSON.parse(active);
  if (l) active = l.split(',');
  console.log(active);
  if (!active) return;
  console.log("restore", active);
  for (let i = 0; i < layers._layers.length; i++) {
    let l = layers._layers[i];
    if (active.includes(l.name)) {
      map.addLayer(l.layer);
    } else {
      map.removeLayer(l.layer);
    }
  }
}

restoreActiveLayers(params.get('l'));

function storeActiveLayers() {
  var active = [];
  for (let i = 0; i < layers._layers.length; i++) {
    let l = layers._layers[i];
//      console.log(i,l,map.hasLayer(l.layer));
    if (map.hasLayer(l.layer)) {
      active.push(l.name);
    }
  }
  console.log("store", active);
  sessionStorage.setItem("activeLayers", JSON.stringify(active));
}

storeActiveLayers();

map.on('layeradd layerremove overlayadd overlayremove', storeActiveLayers);

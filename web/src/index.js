import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-graticule';
import 'leaflet.tilelayer.fallback';
import '@kvforksorg/leaflet.polylinemeasure';
import '@kvforksorg/leaflet.polylinemeasure/Leaflet.PolylineMeasure.css';
import 'leaflet.control.opacity';
import 'leaflet.nauticscale/dist/leaflet.nauticscale';
import {LocateControl} from 'leaflet.locatecontrol';
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
import 'leaflet-mouse-position';
import 'leaflet-mouse-position/src/L.Control.MousePosition.css';
import {OpenLocationCode} from 'open-location-code';

// npx png-to-ico src/favicon.png >src/favicon.ico
import './favicon.ico';
import './manifest.json';
import './icon.png';
import './icon.svg';
import './style.css';
import {log, debounce, logger} from './utils';
import {legend} from './legend';
import {grid, degmin} from './grid';
import {NightSwitch} from './nightmode';
import {restoreLayers} from './restore';
import {addVectorLayer} from './vector';
import {addTidealAtlas, addTideGauges} from "./tides";
import {addWattSegler} from './wattsegler';

const isDevMode = process.env.NODE_ENV === 'development';
const isStandalone = !!(window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone);

log('PWA', 'red', 'standalone', isStandalone, 'development', isDevMode);

const params = new URLSearchParams(window.location.search);

if ('serviceWorker' in navigator && (isStandalone || params.get('sw') == '1')) {
  window.addEventListener('load', () => {
    log('PWA', 'red', 'registering service worker');
    navigator.serviceWorker.register('service-worker.js')
      .then(reg => console.log('SW registered', reg))
      .catch(err => console.error('SW registration failed', err));
  });
}

const baseurl = '';
// const baseurl = 'https://freenauticalchart.net';
const boundsDE = L.latLngBounds([53.0, 3.3], [56.0, 14.4]);
const boundsNL = L.latLngBounds([51.2, 3.0], [53.8, 7.3]);
const cors = window.location.hostname != 'freenauticalchart.net';

function addClass(cls) {
  return function (e) {
    e.target.getContainer().classList.add(cls);
  };
}

const basemaps = {
  'OpenStreetMap': L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).on('add', addClass('grayscale')),
  'Worldy Imagery': L.tileLayer('https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: '<a target="_blank" href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">World Imagery</a>'
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
  'Grid': grid(params.get('dec')),
  'EMODnet Bathymetry': L.tileLayer.wms('https://ows.emodnet-bathymetry.eu/wms', {
    version: '1.3.0',
    transparent: 'true',
    format: 'image/png',
    tiled: true,
    layers: 'emodnet:mean_multicolour',
    attribution: '<a target="_blank" href="https://emodnet.ec.europa.eu/">EMODnet</a>',
  }).on('add', addClass('invert')),
  'QMAP DE': L.tileLayer.fallback(baseurl + '/qmap-de/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP DE</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH</a>)',
    bounds: boundsDE,
    crossOrigin: cors,
  }),
  'QMAP NL': L.tileLayer.fallback(baseurl + '/qmap-nl/{z}/{x}/{y}.webp', {
    attribution: '<a href="/download/">QMAP NL</a> (<a target="_blank" href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS</a>)',
    bounds: boundsNL,
    crossOrigin: cors,
  }),
  'OpenSeaMap': L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
    attribution: '<a target="_blank" href="https://openseamap.org/">OpenSeaMap</a>',
    opacityControl: false,
  }),
};

if (isDevMode) {
  overlays['QMAP DE*'] = L.tileLayer('http://nas:8001/tiles/qmap-de/EPSG3857/{z}/{x}/{y}.png');
  overlays['QMAP NL*'] = L.tileLayer('http://nas:8001/tiles/qmap-nl/EPSG3857/{z}/{x}/{y}.png');
}

if (params.get('bsh') == '1') {
  const bsh = {
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
  };
  Object.assign(overlays, bsh);
}

const map = L.map('map', {
  center: [54.264, 9.196],
  zoom: 8, minZoom: 7, maxZoom: 18,
  layers: [basemaps['OpenStreetMap'], overlays['Grid'], overlays['QMAP DE'], overlays['QMAP NL']],
});

function updateAttribution(online = true) {
  const attrib = '<a class="highlight" href="/download/">free nautical chart (?)</a> | <a target="_blank" href="https://leafletjs.com/">Leaflet</a>';

  if (!online) {
    map.attributionControl.setPrefix(attrib.replace('(?)', '(offline)'));
    return;
  }

  map.attributionControl.setPrefix(attrib);

  fetch(baseurl + '/updated').then(response => {
    console.log('updated', response);
    if (!response.ok) return;
    const date = new Date(response.headers.get('Last-Modified')).toISOString().slice(0, 10);
    map.attributionControl.setPrefix(attrib.replace('(?)', `(${date})`));
  }).catch(console.log);
}

updateAttribution();
window.addEventListener('online', () => updateAttribution(true));
window.addEventListener('offline', () => updateAttribution(false));


L.control.mousePosition({
  separator: ' ',
  latFormatter: v => degmin(v, 3, true),
  lngFormatter: v => degmin(v, 3, false),
}).addTo(map);

map.addControl(new L.Control.ScaleNautic({metric: true, imperial: false, nautic: true}));

const layers = L.control.layers(basemaps, overlays, {collapsed: true}).addTo(map);

L.control.polylineMeasure({
  unit: 'nauticalmiles',
  clearMeasurementsOnStop: false,
  showBearings: true,
  showClearControl: true,
  showUnitControl: true,
  unitControlUnits: ["kilometres", "nauticalmiles"],
}).addTo(map);


map.on('contextmenu', (e) => {
  const lat = e.latlng.lat.toFixed(6);
  const lng = e.latlng.lng.toFixed(6);
  const coords = `${lat}, ${lng}`;
  if (isDevMode) navigator.clipboard.writeText(coords);
  const olc = new OpenLocationCode();
  L.popup()
    .setLatLng(e.latlng)
    .setContent(`${degmin(e.latlng.lat, 3, true)} ${degmin(e.latlng.lng, 3, false)}<br/>${coords}<br/>${olc.encode(e.latlng.lat, e.latlng.lng)}`)
    .openOn(map);
});


var opacity = L.control.opacity();

function updateOpacityControl() {
  map.removeControl(opacity);
  var activeOverlays = Object.fromEntries(Object.entries(overlays)
    .filter(([k, v]) => v.options.opacityControl !== false && map.hasLayer(v)));
  log('opacity', 'cyan', activeOverlays);
  if (Object.keys(activeOverlays).length) {
    opacity = L.control.opacity(activeOverlays, {collapsed: true});
    map.addControl(opacity);
  }
}

updateOpacityControl();

map.on('overlayadd overlayremove', debounce(updateOpacityControl));

if (isDevMode || isStandalone) {
  new LocateControl({flyTo: true}).addTo(map);
  new NightSwitch({position: 'topleft'}).addTo(map);
}

if (params.get('gpx') == '1') {
  import('./gpx').then(({GPXbutton}) => new GPXbutton({position: 'topleft', layers: layers}).addTo(map));
}

addTidealAtlas(map);
if (isDevMode || params.get('tides') == '1') {
  addTideGauges(map);
  addWattSegler(map);
}

legend(layers);

if (params.get('vector') == '1') {
  import('@maplibre/maplibre-gl-leaflet').then(maplibre => {
    console.log('maplibre', maplibre);
    layers.addBaseLayer(L.maplibreGL({
      style: baseurl + '/style.json',
    }), 'Vector (experimental)');
  });
}

if (params.get('zones') == '1') {
  import('./besondere.json');
  import('./allgemeine.json');
  import('./kite.json');
  import('./routen.json');
  import('./wege.json');
  import('./ausstiegeA.json');
  import('./ausstiegeK.json');
  import('./rot.json');
  import('./gruen.json');

  (async () => {
    const attr = '<a target="_blank" href="https://www.nationalpark-wattenmeer.de/wissensbeitrag/befahrensverordnung-karte/">NordSBefV</a>';
    await addVectorLayer(layers, 'allg. Schutzgebiete', 'allgemeine.json', {
      active: false,
      color: 'green',
      legend: 'Befahren erlaubt, Betreten verboten. Diese Bereiche entsprechen den Kernzonen der Nationalparke, also der „Schutzzone I“ (Schleswig-Holstein), der „Ruhezone (Zone I)“ (Niedersachsen) bzw. der „Zone I“ (Hamburg).',
      attribution: attr,
    });
    await addVectorLayer(layers, 'bes. Schutzgebiete', 'besondere.json', {
      active: true,
      color: 'red',
      legend: 'Bereiche, die während der jeweiligen Schutzzeit – vom 15. April bis 1. Oktober eines Jahres oder ganzjährig – außerhalb der Fahrwasser grundsätzlich nicht befahren werden dürfen. Innerhalb der Fahrwasser darf ein maschinengetriebenes Wasserfahrzeug maximal mit 12kn (Fahrt über Grund) fahren. Außerhalb der Fahrwasser – soweit außerhalb der jeweiligen Schutzzeit – gilt eine zulässige Höchstgeschwindigkeit von 8kn (Fahrt über Grund). Das Trockenfallen ist in diesen Bereichen untersagt.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Kitesurf-Gebiete', 'kite.json', {
      active: false,
      color: 'orange',
      legend: 'Erlaubniszone, in der Kitesurfen und ähnliche Sportarten wie Wingsurfen erlaubt sind. Außerhalb der Kitesurfgebiete sind diese Sportarten bis auf Windsurfen nicht zulässig.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Schutzgebietsrouten', 'routen.json', {
      active: true,
      color: 'purple',
      legend: 'Routen zum Befahren der Besonderen Schutzgebiete für Wasserfahrzeuge mit einer Breite von 250m, die auch zum Aufenthalt genutzt werden können. Diese Wasserwanderwege sind im Gebiet nicht gekennzeichnet.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Wasserwanderwege', 'wege.json', {
      active: true,
      color: 'brown',
      legend: 'Zusätzliche Routen zum Befahren der Besonderen Schutzgebiete nur für muskelkraftbetriebene Wasserfahrzeuge (Kajaks) mit einer Breite von 250m, die auch zum Aufenthalt genutzt werden können. Diese Wasserwanderwege sind im Gebiet nicht gekennzeichnet.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Ausstiegsstellen, allg.', 'ausstiegeA.json', {
      active: true,
      color: 'blue',
      legend: 'Das Trockenfallen und der sonstige Aufenthalt sind in diesen Bereichen in einem Radius von 200m um einen durch Koordinaten bestimmten Punkt erlaubt. Einige Ausstiegs- und Aufenthaltsstellen sind nur für Kanuten und ähnliche muskelkraftbetriebene Kleinfahrzeuge bestimmt. Die Ausstiegs- und Aufenthaltsstellen sind im Gebiet nicht gekennzeichnet.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Ausstiegsstellen, Kayak', 'ausstiegeK.json', {
      active: true,
      color: '#09a9ff',
      legend: 'Das Trockenfallen und der sonstige Aufenthalt sind in diesen Bereichen in einem Radius von 200m um einen durch Koordinaten bestimmten Punkt erlaubt. Einige Ausstiegs- und Aufenthaltsstellen sind nur für Kanuten und ähnliche muskelkraftbetriebene Kleinfahrzeuge bestimmt. Die Ausstiegs- und Aufenthaltsstellen sind im Gebiet nicht gekennzeichnet.',
      attribution: attr,
    });
    await addVectorLayer(layers, 'Rotzone', 'rot.json', {
      active: true,
      color: 'red',
      legend: 'Gesperrt für alle - In der Rotzone liegen besonders sensible Lebensräume. Dort ist jegliches Befahren für Wasserfahrzeuge untersagt.',
      attribution: '<a target="_blank" href="https://www.nationalpark-vorpommersche-boddenlandschaft.de/karte#&e=3000,3200&c=0,3201,3202">NPVB</a>',
    });
    await addVectorLayer(layers, 'Grünzone', 'gruen.json', {
      active: true,
      color: 'green',
      legend: 'Gesperrt für Motoren - In der Grünzone ist ein Befahren mit motorgetriebenen Wasserfahrzeugen verboten. Dort darf sich mit Muskel- oder Windkraft fortbewegt werden.',
      attribution: '<a target="_blank" href="https://www.nationalpark-vorpommersche-boddenlandschaft.de/karte#&e=3000,3200&c=0,3201,3202">NPVB</a>',
    });
    restoreLayers(layers, params.get('l'));
  })();
} else {
  restoreLayers(layers, params.get('l'));
}


import 'leaflet-hash';
import {log, debounce} from './utils';

const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

function logStore(...args) {
  log('Store', 'blue', ...args);
}

function logRestore(...args) {
  log('Restore', 'blue', ...args);
}

export function restoreLayers(control, list) {

  const map = control._map;
  const storage = isStandalone ? localStorage : sessionStorage;

  const LAYERS = 'layers';

  function storeActiveLayers() {
    let active = [];
    for (let i = 0; i < control._layers.length; i++) {
      let l = control._layers[i];
      if (map.hasLayer(l.layer)) {
        active.push(l.name);
      }
    }
    logStore("layers", active);
    storage.setItem(LAYERS, JSON.stringify(active));
  }

  function restoreActiveLayers() {
    let active = storage.getItem(LAYERS);
    active = JSON.parse(active);
    if (list) active = list.split(',');
    if (!active) return;
    logRestore("layers", active);
    for (let i = 0; i < control._layers.length; i++) {
      let l = control._layers[i];
      if (active.includes(l.name)) {
        map.addLayer(l.layer);
      } else {
        map.removeLayer(l.layer);
      }
    }
  }


  restoreActiveLayers();
  map.on('layeradd layerremove overlayadd overlayremove', debounce(storeActiveLayers));


  const VIEW = 'view';

  function storeView() {
    logStore("view", map.getZoom(), map.getCenter());
    storage.setItem(VIEW, JSON.stringify({center: map.getCenter(), zoom: map.getZoom()}));
  }

  function restoreView() {
    const view = JSON.parse(storage.getItem(VIEW));
    if (!view) return;
    logRestore("view", view);
    map.setView(view.center, view.zoom);
  }

  if (isStandalone) {
    restoreView();
    map.on('moveend zoomend', debounce(storeView));
  } else {
    logRestore('use hash');
    new L.Hash(map);
  }
}

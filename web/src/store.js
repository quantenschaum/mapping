import {log} from './utils';

const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;

function xlog(...args) {
  log('Restore', 'blue', ...args);
}

export function restoreLayers(control, list) {

  const map = control._map;
  const storage = isStandalone ? localStorage : sessionStorage;

  function restoreActiveLayers() {
    var active = storage.getItem("activeLayers");
    active = JSON.parse(active);
    if (list) active = list.split(',');
    if (!active) return;
    xlog("restore", active);
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

  function storeActiveLayers() {
    var active = [];
    for (let i = 0; i < control._layers.length; i++) {
      let l = control._layers[i];
//      console.log(i,l,map.hasLayer(l.layer));
      if (map.hasLayer(l.layer)) {
        active.push(l.name);
      }
    }
    // xlog("store", active);
    storage.setItem("activeLayers", JSON.stringify(active));
  }

  storeActiveLayers();

  map.on('layeradd layerremove overlayadd overlayremove', storeActiveLayers);
}

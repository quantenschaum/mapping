import L from "leaflet";
import 'leaflet.tilelayer.fallback';
import {log, debounce} from './utils';
import './leaflet-timeline-slider';

const baseurl = 'https://freenauticalchart.net';
const attrTides = '<a href="/download/tides/">Tidal Atlas</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH</a>)';

export function addTides(map, params) {

  const layers = [];

  for (let i = -6; i <= 6; i++) {
    let s = (i >= 0 ? '+' : '') + i;
    layers.push(L.tileLayer.fallback(baseurl + '/tides/hw' + s + '/{z}/{x}/{y}.webp', {
      attribution: attrTides,
    }));
  }
  layers.push(L.tileLayer.fallback(baseurl + '/tides/fig/{z}/{x}/{y}.webp', {
    attribution: attrTides,
  }));

  L.control.timelineSlider({
    timelineItems: ["off", "-6h", "-5h", "-4h", "-3h", "-2h", "-1h", "HW Helgoland", "+1h", "+2h", "+3h", "+4h", "+5h", "+6h", "fig"],
    labelWidth: "40px",
    betweenLabelAndRangeSpace: "10px",
    changeMap: p => {
      let x = p.label.replace("HW Helgoland", "+0h").replace("h", "");
      layers.forEach(l => {
        if (l._url.includes(x)) {
          map.addLayer(l);
          l.bringToFront();
        } else {
          map.removeLayer(l);
        }
      });
    }
  }).addTo(map);
}

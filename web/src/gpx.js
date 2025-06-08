import L from 'leaflet';
import {log} from './utils';
import {addVectorLayer} from './vector';

function xlog(...args) {
  log('GPX', 'purple', ...args);
}

export async function addGPX(control, name, url, opts = {color: 'blue'}) {
  xlog('add', name, url);

  const layer = L.geoJSON(null, {
    ...opts,
    onEachFeature: (f, l) => {
      if (f.properties && f.properties.name) {
        l.bindPopup(f.properties.name);
      }
    },
    style: f => {
      if (f.geometry.type == 'Point') return {};
      return {weight: 4, opacity: 0.8, color: opts.color, fillOpacity: 0.1};
    },
    pointToLayer: (f, latlng) =>
      L.circleMarker(latlng, {
        radius: 6,
        fillColor: opts.color,
        weight: 0,
        fillOpacity: 1,
      }),
  });

  const {gpx} = await import('@mapbox/leaflet-omnivore');

  gpx(url, null, layer).on('ready', () => {
    name = name.slice(0, 20);
    try {
      var length = 0;
      layer.eachLayer(f => {
        xlog('layer:', f);
        if (f instanceof L.Polyline) {
          var latlngs = f.getLatLngs();
          xlog('latlngs:', latlngs);
          for (var i = 1; i < latlngs.length; i++) {
            length += latlngs[i - 1].distanceTo(latlngs[i]);
          }
        }
      });

      if (length > 0) {
        length = `(${(length / 1000.0).toFixed(1)}km/${(length / 1852.0).toFixed(2)}sm)`;
        xlog('length:', length);
        name += ' ' + length;
      }
    } catch (e) {
      xlog('error:', e);
    }

    control.addOverlay(layer, name);
    layer.addTo(control._map);
  });
}

const colors = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
];

function randomColor() {
  return colors[Math.floor(Math.random() * colors.length)];
}

export const GPXbutton = L.Control.extend({
  onAdd: function (map) {
    xlog('add button');

    const div = L.DomUtil.create('div', 'addgpx leaflet-bar');
    L.DomEvent.disableClickPropagation(div);

    const button = L.DomUtil.create('a');
    button.innerHTML = '&#x1F4C2;'; // 📂
    button.title = 'add GPX file';
    div.appendChild(button);

    const input = L.DomUtil.create('input');
    input.type = 'file';
    input.accept = '.gpx'; // file extensions
    input.style.display = 'none'; // hidden from view
    div.appendChild(input);

    button.addEventListener('click', e => input.click());

    input.addEventListener('change', e => {
      [...e.target.files].forEach(file => {
        xlog('file:', file.name, file.type, file.size);
        const reader = new FileReader();
        reader.onload = e => {
          var blob = new Blob([e.target.result], {type: 'application/gpx+xml'});
          var url = URL.createObjectURL(blob);
          addGPX(this.options.layers, file.name, url, {
            color: randomColor(),
            legend: 'user supplied file',
          });
        };
        reader.readAsText(file);
      });
    });

    return div;
  },
});

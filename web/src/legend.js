import L from 'leaflet';
import {log, debounce} from './utils';
import './legend.less';

function llog(...args) {
  log('Legend', 'green', ...args);
}

export function legend(layerControl, options = {
  title: 'Legende',
  position: 'bottomright'
}) {

  const Legend = L.Control.extend({
    onAdd: function (map) {
      this._map = map;
      llog('onAdd', this.options);
      this._container = L.DomUtil.create('div', 'legend leaflet-bar');
      L.DomEvent.disableClickPropagation(this._container);
      this._onLayerChange = this._onLayerChange.bind(this);
      map.on('layeradd', this._onLayerChange);
      map.on('layerremove', this._onLayerChange);
      return this._container;
    },

    onRemove: function () {
      this._map.off('layeradd', this._onLayerChange);
      this._map.off('layerremove', this._onLayerChange);
    },

    _onLayerChange: function (e) {
      var content = '';
      Object.values(layerControl._layers).forEach(e => {
        if (!this._map.hasLayer(e.layer)) return;
        const opts = e.layer.options;
        if (!(e.name && opts.color && opts.legend)) return;
        // llog('entry', e.name, opts);
        content += `<li title="${opts.legend}"><span class="symbol" style="background: ${opts.color}"></span>${e.name}</li>`;
      })
      if (content) {
        this._container.innerHTML = `<h1>${this.options.title}</h1><ul>${content}</ul>`;
      } else {
        this._container.innerHTML = '';
      }

      this._container.querySelectorAll('li').forEach((li) => {
        const text = li.getAttribute('title');
        if (text) {
          const name = li.textContent;
          li.addEventListener('click', () => {
            alert(`${name}\n${text}`);
          });
        }
      });
    },
  });

  new Legend(options).addTo(layerControl._map);

}

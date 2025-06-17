import {logger} from './utils';
import $ from 'jquery';
import './wattsegler.less';
import './wattsegler.json';

const log = logger('wattsegler', 'green');

export function addWattSegler(map) {
  fetch('/wattsegler.json')
    .then(r => r.json())
    .then(data => {
      log(data);
      const locations = data.locations;
      const layer = L.layerGroup().addTo(map);

      fetch(data.url.replace(/https:\/\/.*?\//, '/wattsegler/'))
        .then(r => r.text())
        .then(html => {
          // log(html);
          const $html = $('<div>').html(html);
          $html.find('table tr').each((i, tr) => {
            let tds = $(tr).find('td');
            if (tds.length != 4) return;
            const name = tds.map((i, e) => $(e).text().trim()).get()[0];
            if (!name) return;
            // log(name);
            const loc = locations[name];

            let tab = `<tr><th>Info</th><th>Tiefe bei MHW</th><th>Datum</th></tr>`;
            tab += `<tr>${$(tr).html().replace(/style=".*?"/g, '').replace('&nbsp;', '').replace(/^.*?<\/td>/s, '').replace(/(\d)\s+m/g, '$1m')}</tr>`;
            tab = `<table>${tab}</table>`;
            // log(tab);

            if (!loc) return;
            let m = L.circleMarker(loc, {
              radius: 4,
              weight: 3,
              color: 'green',
            })
              .bindPopup(`<div class="wattsegler"><div class="name">${name}</div>${tab}<div class="source">source <a href="${data.url}" target="_blank">wattsegler.de</a></div></div>`)
              .addTo(layer);
          });
        }).catch(log);


      map.on('zoomend', () => {
        if (map.getZoom() >= 9) {
          if (!map.hasLayer(layer)) map.addLayer(layer);
        } else {
          if (map.hasLayer(layer)) map.removeLayer(layer);
        }
      });
    });
}

import L from "leaflet";
import 'leaflet.tilelayer.fallback';
import './slider';
import {logger} from './utils';
import './tides.less';

const clog = logger('tides', 'lightblue');

const baseurl = 'https://freenauticalchart.net';
const attrTides = '<a href="/download/tides/">Tidal Atlas</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH</a>)';

export function addTides(map, gauges = false) {

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
    title: 'Tidal Atlas',
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

  if (!gauges) return;

  const gaugesLayer = L.layerGroup();
  gaugesLayer.addTo(map);
  const group_colors = {1: 'white', 2: 'lightblue', 3: 'gray'};

  function showPopup(marker, g) {
    clog(g);
    fetch(`/tides/data/DE_${g.bshnr.padStart(5, '_')}_tides.json`)
      .then(r => r.json())
      .then(data => {
        clog(data);

        const now = new Date();
        const year = now.getFullYear().toString();
        let ydata;
        data.years.every(y => {
          ydata = y[year];
          return !ydata;
        });
        clog(ydata);

        const pred = ydata.hwnw_prediction;
        clog(pred);
        const o = pred.level == 'PNP' ? -ydata['SKN (ueber PNP)'] : 0;

        let i = 0;
        for (; i < pred.data.length; i++) {
          const ts = new Date(pred.data[i].timestamp);
          // clog(pred.data[i], now, ts, ts >= now);
          if (ts > now) break;
        }
        i = Math.max(0, i - 1);

        const tform = new Intl.DateTimeFormat(undefined, {timeZoneName: 'short'});
        const parts = tform.formatToParts(now);
        const tz = parts.find(part => part.type === 'timeZoneName')?.value;

        let tab = `<tr><th>🕑 ${tz}</th><th>↕</th><th>m</th><th>🌝</th></tr>`;
        for (let k = i; k < Math.min(i + 8, pred.data.length); k++) {
          clog(pred.data[k]);
          const d = pred.data[k];
          const t = new Date(d.timestamp).toLocaleString('de-DE', {
            month: '2-digit', day: '2-digit',   // year: 'numeric',
            hour: '2-digit', minute: '2-digit',
          });
          const height = d.height != null ? (d.height + o) / 100 : '-';
          tab += `<tr class="${d.type}"><td>${t}</td><td>${d.type}</td><td>${height}</td><td class="${d.phase} moon${d.moon}">${d.phase}</td></tr>\n`;
        }
        tab = `<table>${tab}</table>`;
        // clog(tab);

        marker
          .bindPopup(`<div class="tides"><a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}">${g.station_name}</a>${tab}data source <a target="_blank" href="https://gezeiten.bsh.de">BSH</a></div>`)
          .openPopup();
      });
  }

  fetch('/tides/data/tides_overview.json')
    .then(r => r.json())
    .then(data => {
      // clog(data);
      data.gauges.some(g => {
        // clog(g);
        let m = L.circleMarker([g.latitude, g.longitude], {
          radius: 4,
          weight: 3,
          color: g.station_name.includes('Helgoland') ? 'darkred' : 'blue',
          fillColor: group_colors[g.gauge_group],
          fillOpacity: 1,
        })
          .bindPopup(`<a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}">${g.station_name}</a>`)
          .on('click', e => showPopup(e.target, g))
          .addTo(gaugesLayer);
        // showPopup(m, g);
        // return false;
      });
    });
}

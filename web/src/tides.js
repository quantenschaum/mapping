import L from "leaflet";
import 'leaflet.tilelayer.fallback';
import './slider';
import {logger} from './utils';
import './tides.less';

const clog = logger('tides', 'lightblue');

const baseurl = 'https://freenauticalchart.net';
const attrTides = '<a href="/download/tides/">Tidal Atlas</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH</a>)';

export function addTidealAtlas(map, gauges = false) {

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
}

export async function addTideGauges(map) {
  const gaugesLayer = L.layerGroup();
  gaugesLayer.addTo(map);
  const group_colors = {1: 'white', 2: 'lightblue', 3: 'gray'};

  async function showPopup(marker, g, forecast_map) {
    // clog(g);
    const tidedata = await fetch(`/tides/data/DE_${g.bshnr.padStart(5, '_')}_tides.json`).then(r => r.json());
    clog('tidedata', tidedata);
    const forecastdata = await fetch(`/forecast/data/DE_${g.bshnr.padStart(5, '_')}.json`).then(r => r.json()).catch(e => {
    });
    clog('forecastdata', forecastdata);

    const now = new Date();
    const year = now.getFullYear().toString();
    let ydata;
    tidedata.years.every(y => {
      ydata = y[year];
      return !ydata;
    });

    const prediction = ydata.hwnw_prediction.data;
    const level = ydata.hwnw_prediction.level;
    const forecast = forecastdata?.hwnw_forecast?.data;
    const forecast_text = forecast_map?.forecast_text;
    const curve = forecastdata?.curve_forecast?.data;

    const offsets = {
      PNP: -ydata['SKN (ueber PNP)'],
      SKN: 0,
    };

    let i = 0;
    var moon;
    for (; i < prediction.length; i++) {
      const ts = new Date(prediction[i].timestamp);
      // clog(pred.data[i], now, ts, ts >= now);
      let m = prediction[i].moon;
      if (m != undefined) moon = m;
      if (ts > now) break;
    }
    clog('moon', moon);
    i = Math.max(0, i - 1);

    const locale = undefined;
    const tform = new Intl.DateTimeFormat(locale, {timeZoneName: 'short'});
    const parts = tform.formatToParts(now);
    const tz = parts.find(part => part.type === 'timeZoneName')?.value;

    function getForcast(timestamp) {
      if (!forecast) return '';
      const ts = new Date(timestamp).getTime();
      const fc = forecast.find(f => new Date(f.timestamp).getTime() === ts);
      clog(fc);
      if (fc?.forecast) return `${fc.forecast.replace(' m', '')}`;
      return '';
    }

    let date0;
    let tab = `<tr><th>📅</th><th>${tz}</th><th>🌊</th><th>m</th><th>↝</th><th class="moon${moon}"></th></tr>`;
    for (let k = i; k < Math.min(i + 8, prediction.length); k++) {
      clog(prediction[k]);
      const d = prediction[k];
      let date = new Date(d.timestamp).toLocaleString(locale, {
        month: '2-digit', day: '2-digit', weekday: 'short', // year: 'numeric',
      }).replace(',', '');
      if (date0 === date) date = '';
      else date0 = date;
      const time = new Date(d.timestamp).toLocaleString(locale, {
        hour: '2-digit', minute: '2-digit',
      });
      const height = d.height != null ? (d.height + offsets[level]) / 100 : '-';
      const deviation = getForcast(d.timestamp);
      tab += `<tr class="${d.type}"><td>${date}</td><td>${time}</td><td>${d.type}</td><td>${height}</td><td class="forecast">${deviation}</td><td class="${d.phase} moon${d.moon}">${d.phase}</td></tr>\n`;
    }
    tab = `<table>${tab}</table>`;
    // clog(tab);


    const forecast_link = curve ? `target="_blank" href="https://wasserstand-nordsee.bsh.de/${g.seo_id}?zeitraum=tag1bis2"` : '';

    marker
      .bindPopup(`<div class="tides"><a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}" class="stationname">${g.station_name}</a>${tab}<div class="forecast"><a ${forecast_link}>${forecast_text || ''}</a></div><div id="plot"></div><div class="source">data source <a target="_blank" href="https://gezeiten.bsh.de">BSH</a></div></div>`)
      // .on('popupopen', e => {
      //   if (!curve) return;
      //   clog('plot', curve);
      //   import('plotly.js-dist-min').then(Plotly => {
      //     const x = [], y = [];
      //     for (let i = 0; i <= 360; i++) {
      //       const rad = i * Math.PI / 180;
      //       x.push(i);
      //       y.push(Math.sin(rad));
      //     }
      //
      //     const data = [{
      //       x,
      //       y,
      //       type: 'scatter',
      //       mode: 'lines',
      //       name: 'sin(x)',
      //       line: {color: 'blue'}
      //     }];
      //
      //     const layout = {
      //       margin: {t: 10, r: 10, b: 30, l: 40},
      //       xaxis: {title: 'Degrees'},
      //       yaxis: {title: 'sin(x)'},
      //     };
      //
      //     Plotly.newPlot('plot', data, layout, {displayModeBar: false});
      //
      //   });
      // })
      .openPopup();
  }

  let forecast = await fetch('/forecast/data/map.json').then(r => r.json()).catch(e => {
  });
  clog(forecast);

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
          .on('click', e => showPopup(e.target, g, forecast))
          .addTo(gaugesLayer);
        // showPopup(m, g);
        // return false;
      });
    });
}

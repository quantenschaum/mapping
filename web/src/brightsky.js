import L from "leaflet";
import {logger} from './utils';
import './brightsky.less';
import {init_ais} from "./ais";

const log = logger('BSky', 'lightblue');
const apibase = 'https://api.brightsky.dev/';
// const apibase = 'https://freenauticalchart.net/brightsky/';
// const apibase = '/brightsky/';

const colors = {
  forecast: 'green',
  synop: 'red',
  current: 'blue',
  historical: 'yellow',
};

const icons = {
  "thunderstorm": "thunderstorms",
};

function icon(key) {
  const name = icons[key] || key;
  return `https://basmilius.github.io/weather-icons/production/fill/all/${name}.svg`;
}

function windicon(kmh) {
  const knots = Math.round(kmh / 1.852 / 5) * 5;
  return `https://raw.githubusercontent.com/qulle/svg-wind-barbs/refs/heads/main/svg/${knots.toFixed(0)}.svg`;
  const bft = kmhToBeaufort(kmh);
  return icon(`wind-beaufort-${bft}`);
}

const scale = [
  {max: 1, beaufort: 0},
  {max: 6, beaufort: 1},
  {max: 12, beaufort: 2},
  {max: 20, beaufort: 3},
  {max: 29, beaufort: 4},
  {max: 39, beaufort: 5},
  {max: 50, beaufort: 6},
  {max: 62, beaufort: 7},
  {max: 75, beaufort: 8},
  {max: 89, beaufort: 9},
  {max: 103, beaufort: 10},
  {max: 118, beaufort: 11},
  {max: Infinity, beaufort: 12}
];

function kmhToBeaufort(speed) {
  for (let i = 0; i < scale.length; i++) {
    if (speed < scale[i].max) {
      return scale[i].beaufort;
    }
  }
}

const units = {
  cloud_cover: '%',
  condition: '',
  dew_point: '℃',
  temperature: '℃',
  precipitation_60: 'mm',
  pressure_msl: 'hPa',
  visibility: 'm',
  wind_direction_10: '°',
  wind_speed_10: 'km/h',
  wind_gust_direction_10: '°',
  wind_gust_speed_10: 'km/h',
  relative_humidity: '%',
};

export function addBrightSky(map, sun_icons = false) {
  const layer = L.layerGroup([], {attribution: '<a href="https://brightsky.dev/" target="_blank">BrightSky</a>'}).addTo(map);
  fetch(apibase + 'sources?lat=57.5&lon=9.6&max_dist=500000')
    .then(r => r.json())
    .then(data => {
      data.sources
        .filter(s => ['synop'].includes(s.observation_type))
        .forEach(s => {
          // log(s);
          if (0)
            L.circleMarker([s.lat, s.lon], {
              radius: 4,
              weight: 3,
              color: 'red',
              // fillColor: colors[s.observation_type],
              // fillOpacity: 1,
            }).bindPopup(`<div class="brightsky">${s.station_name}<br/>${s.observation_type}<br/>${s.id}/${s.dwd_station_id}/${s.wmo_station_id}</div>`)
              .addTo(layer);

          fetch(apibase + `current_weather?lat=${s.lat}&lon=${s.lon}&maxdist=1000`)
            .then(r => r.json())
            .then(data => {
              const w0 = data.weather;
              if (!w0) return;
              if (sun_icons) {
                var svgIcon = L.divIcon({
                  className: '',
                  html: `<img src="${icon(w0.icon)}" />`,
                  iconSize: [32, 32],
                  iconAnchor: [16, 16],
                });
              } else {
                var svgIcon = L.divIcon({
                  className: '',
                  html: `<img src="${windicon(w0.wind_speed_10)}" style="transform: rotate(${w0.wind_direction_10}deg);" />`,
                  iconSize: [128, 128],
                  iconAnchor: [64, 64],
                });
              }
              const m = L.marker([s.lat, s.lon], {icon: svgIcon}).addTo(layer);
              m.bindPopup(() => {
                fetch(apibase + `current_weather?lat=${s.lat}&lon=${s.lon}&maxdist=1000`)
                  .then(r => r.json())
                  .then(data => {
                    log(data);
                    let tab = '<table>';
                    const w = data.weather;
                    if (!w) return;
                    for (let [key, value] of Object.entries(w)) {
                      let unit = units[key];
                      if (value != null && unit != null) {
                        if (unit == 'km/h') {
                          value = (value / 1.852).toFixed(1);
                          unit = 'kn';
                        }
                        tab += `<tr><td>${key}</td><td>${value} ${unit || ''}</td></tr>`;
                      }
                    }
                    tab += '</table>';
                    const ts = new Date(w.timestamp);
                    m.bindPopup(`<div class="brightsky"><b>${s.station_name}</b><br/>${ts.toISOString()}<br/><img src="${icon(w.icon)}" width="100em"/><img src="${windicon(w.wind_speed_10)}" width="100em" style="transform: rotate(${w.wind_direction_10}deg) scale(2); transform-origin: center; overflow: clip; object-fit: cover;"/><br/>` + tab + '</div>').openPopup();
                  }).catch(log);
                return `<div class="brightsky">${s.station_name}<br/>${s.observation_type}<br/>${s.id}/${s.dwd_station_id}/${s.wmo_station_id}</div>`;
              });
            }).catch(log);

        })
    }).catch(log);
  return layer;
}

const dwd_icon = 'data:image/png;base64,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';

export const WeatherButton = L.Control.extend({
  options: {
    icon: dwd_icon,
    position: 'topleft',
  },
  onAdd: function (map) {
    log('button added');
    var div = L.DomUtil.create('div', 'nightswitch leaflet-bar leaflet-control');
    var button = L.DomUtil.create('a');
    button.innerHTML = `<img src="${this.options.icon}" width="24" style="margin: 0 0 -8px 0;"/>`;
    button.title = 'toggle weather data';
    div.appendChild(button);
    button.addEventListener('click', () => {
      if (this._layer) {
        this._layer.remove();
        this._layer = null;
      } else {
        this._layer = addBrightSky(map, 1);
      }
    });
    button.addEventListener('dblclick', () => {
      if (this._layer) {
        this._layer.remove();
        this._layer = null;
      } else {
        this._layer = addBrightSky(map, 0);
      }
    });
    L.DomEvent.disableClickPropagation(div);
    return div;
  },
});

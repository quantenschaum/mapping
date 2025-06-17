import L from "leaflet";
import 'leaflet.tilelayer.fallback';
import './slider';
import {logger} from './utils';
import './tides.less';

const isDevMode = process.env.NODE_ENV === 'development';
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

async function reproject(geojson, fromCRS = "EPSG:25831", toCRS = "EPSG:4326") {
  const proj4 = (await import('proj4')).default;
  proj4.defs("EPSG:25831", "+proj=utm +zone=31 +ellps=GRS80 +units=m +no_defs");

  function reprojectCoord(coord) {
    return proj4(fromCRS, toCRS, coord);
  }

  function processGeometry(geom) {
    if (geom.type === "Point") {
      geom.coordinates = reprojectCoord(geom.coordinates);
    } else if (geom.type === "LineString" || geom.type === "MultiPoint") {
      geom.coordinates = geom.coordinates.map(reprojectCoord);
    } else if (geom.type === "Polygon" || geom.type === "MultiLineString") {
      geom.coordinates = geom.coordinates.map(ring => ring.map(reprojectCoord));
    } else if (geom.type === "MultiPolygon") {
      geom.coordinates = geom.coordinates.map(
        poly => poly.map(ring => ring.map(reprojectCoord))
      );
    } else if (geom.type === "GeometryCollection") {
      geom.geometries.forEach(processGeometry);
    }
    return geom;
  }

  let converted = JSON.parse(JSON.stringify(geojson)); // Deep clone
  if (converted.type === "FeatureCollection") {
    converted.features.forEach(f => processGeometry(f.geometry));
  } else if (converted.type === "Feature") {
    processGeometry(converted.geometry);
  } else {
    processGeometry(converted);
  }

  return converted;
}

export async function addTideGauges(map) {
  await Promise.all([
    addTideGaugesDE(map),
    addTideGaugesNL(map),
  ]);
}

export async function addTideGaugesDE(map, preFetch = false) {

  async function showPopup(marker, g) {
    // clog(g);
    const tidedata = await fetch(`/tides/de/data/DE_${g.bshnr.padStart(5, '_')}_tides.json`)
      .then(r => r.json()).catch(clog);
    clog('tidedata', tidedata);
    if (!tidedata) return;

    const forecast_map = await fetch('/forecast/de/data/map.json')
      .then(r => r.json()).catch(clog);
    clog('forecast_map', forecast_map);

    const forecastdata = await fetch(`/forecast/de/data/DE_${g.bshnr.padStart(5, '_')}.json`)
      .then(r => r.json()).catch(clog);
    clog('forecastdata', forecastdata);

    const now = new Date();
    const today = new Date(now)
    today.setHours(0);
    today.setMinutes(0);
    today.setSeconds(0);
    today.setMilliseconds(0);
    const year = now.getFullYear().toString();
    let ydata;
    tidedata.years.every(y => {
      ydata = y[year];
      return !ydata;
    });

    const locale = undefined;
    const prediction = ydata.hwnw_prediction.data;
    const level = ydata.hwnw_prediction.level;
    const forecast = forecastdata?.hwnw_forecast?.data;
    const curve = forecastdata?.curve_forecast?.data;
    const fc_date = new Date(forecast_map?.creation_forecast);
    const forecast_date = fc_date.toLocaleString(locale, {
      month: '2-digit', day: '2-digit', weekday: 'short', hour: '2-digit', minute: '2-digit',
    });
    const forecast_text = forecast_map?.forecast_text ? forecast_map?.forecast_text + ` (${forecast_date})` : '';
    const forecast_link = curve ? `https://wasserstand-nordsee.bsh.de/${g.seo_id}?zeitraum=tag1bis2` : 'https://wasserstand-nordsee.bsh.de';
    const forecast_cls = (now - fc_date) > 8 * 3600_000 ? 'old' : 'new';

    const offsets = {
      PNP: -ydata['SKN (ueber PNP)'],
      SKN: 0,
    };
    const offset = offsets[level];

    const basevalues = ydata.MHW ? `MHW=${(ydata.MHW + offset) / 100} MNW=${(ydata.MNW + offset) / 100} MTH=${ydata.MTH / 100}` : '';

    let i = 0;
    var moon;
    for (; i < prediction.length; i++) {
      const ts = new Date(prediction[i].timestamp);
      // clog(pred.data[i], now, ts, ts >= now);
      let m = prediction[i].moon;
      if (m != undefined) moon = m;
      if (ts > today) break;
    }
    clog('moon', moon);

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
    let rows = `<tr><th>📅</th><th>${tz}</th><th>🌊 m</th><th class="moon${moon}"></th></tr>\n`;
    for (let k = i; k < Math.min(i + 8, prediction.length); k++) {
      clog(prediction[k]);
      const r = prediction[k];
      const ts = new Date(r.timestamp);
      let date = ts.toLocaleString(locale, {
        month: '2-digit', day: '2-digit', weekday: 'short', // year: 'numeric',
      }).replace(',', '');
      if (date0 === date) date = '';
      else date0 = date;
      const time = ts.toLocaleString(locale, {
        hour: '2-digit', minute: '2-digit',
      });
      const height = r.height != null ? ((r.height + offset) / 100).toFixed(2) : '-';
      const deviation = getForcast(r.timestamp);
      const when = ts > now ? 'future' : 'past';
      rows += `<tr class="${r.type} ${when}"><td>${date}</td><td>${time}</td><td>${height} <span class="forecast">${deviation}</span></td><td class="${r.phase} moon${r.moon}">${r.phase}</td></tr>\n`;
    }
    const table = `<table>\n${rows}</table>`;
    // clog(table);

    await marker
      .bindPopup(`<div class="tides"><a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}" class="stationname">${g.station_name}</a>${table}<div class="basevalues">${basevalues}</div><div class="forecast"><a href="${forecast_link}" target="_blank" class="${forecast_cls}">${forecast_text}</a></div><div id="plot"></div><div class="source">source <a target="_blank" href="https://gezeiten.bsh.de">BSH</a></div></div>`)
      .openPopup();

    if (!curve) return;

    const Plotly = await import('plotly.js-dist-min');
    clog(curve[0]);

    const t0 = new Date(now.getTime() - 6 * 3600_000);
    const t1 = new Date(now.getTime() + 18 * 3600_000);
    const x = curve.map(d => new Date(d.timestamp));
    const trace1 = {
      name: 'astro',
      x: x, y: curve.map(d => (d.astro + offset) / 100),
      type: 'scatter', mode: 'lines',
      line: {color: '#3a99e8'},
    };
    const trace2 = {
      name: 'forecast',
      x: x, y: curve.map(d => (d.curveforecast + offset) / 100).map(v => v > 0 ? v : null),
      type: 'scatter', mode: 'lines',
      line: {color: 'orange'},
    };
    const trace3 = {
      name: 'measured',
      x: x, y: curve.map(d => (d.measurement + offset) / 100).map(v => v > 0 ? v : null),
      type: 'scatter', mode: 'lines',
      line: {color: 'red'},
    };
    const layout = {
      title: 'Time Series from Object Array',
      margin: {l: 15, r: 0, t: 0, b: 15,},
      xaxis: {title: 'Date', type: 'date', fixedrange: !true, tickformat: '%a %H:%M', range: [t0, t1],},
      yaxis: {title: 'Height', fixedrange: true, tickangle: -90},
      shapes: [
        {
          type: 'line',
          x0: now, x1: now, xref: 'x',
          y0: 0, y1: 1, yref: 'paper',
          line: {color: 'gray', width: 1},
        }
      ],
      dragmode: 'pan',
      legend: {
        x: 0, y: -0.05,
        orientation: 'h',
        bgcolor: 'rgba(255,255,255,0)',
      },
      hovermode: 'x unified',
    };
    const config = {
      scrollZoom: true,
    };
    Plotly.newPlot('plot', [trace1, trace2, trace3], layout, config);
  }

  const gaugesLayer = L.layerGroup().addTo(map);
  const group_colors = {1: 'white', 2: 'lightblue', 3: 'gray'};

  fetch('/tides/de/data/tides_overview.json')
    .then(r => r.json())
    .then(data => {
      // clog(data);
      data.gauges.forEach(g => {
        // clog(g);
        if (g.gauge_group == 3) return;
        if (preFetch) fetch(`/tides/de/data/DE_${g.bshnr.padStart(5, '_')}_tides.json`);
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
        // if (isDevMode && g.station_name.includes('Helgoland')) showPopup(m, g);
      });
    }).catch(clog);
}

export function addTideGaugesNL(map) {
  fetch('/tides/nl/api/point/latestmeasurement?parameterId=astronomische-getij')
    .then(r => r.json())
    .then(data => reproject(data))
    .then(data => {
      L.geoJSON(data, {
        pointToLayer: function (feature, latlng) {
          // clog(feature.properties)
          return L.circleMarker(latlng, {
            radius: 4,
            weight: 3,
            color: '#4e91ea',
            fillColor: feature.properties.locationColor,
            fillOpacity: 1,
          })
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          const link = `https://waterinfo.rws.nl/publiek/astronomische-getij/${p.locationCode}/details`;
          if (feature.properties.name) {
            layer.bindPopup(`<a href="${link}" target="_blank">${feature.properties.name}</a>`);
          }
          layer.on('click', e => {
            clog(p);
            const now = new Date();
            const start = new Date(now);
            start.setHours(0);
            start.setMinutes(0);
            start.setSeconds(0);
            start.setMilliseconds(0);
            const end = new Date(start);
            end.setHours(48);
            end.setMinutes(0);
            end.setSeconds(0);
            end.setMilliseconds(0);

            fetch(`/tides/nl/api/chart/get?mapType=astronomische-getij&locationCodes=${p.locationCode}&getijReference=LAT&timeZone=GMT&startDate=${start.toISOString()}&endDate=${end.toISOString()}`, {
              headers: {
                'Accept': 'application/json',
              }
            })
              .then(r => r.json())
              .then(data => {
                clog(data);

                const locale = undefined;
                const tform = new Intl.DateTimeFormat(locale, {timeZoneName: 'short'});
                const parts = tform.formatToParts(now);
                const tz = parts.find(part => part.type === 'timeZoneName')?.value;

                const extremes = data.series[0].extremes;

                let date0, height0;
                let rows = `<tr><th>📅</th><th>${tz}</th><th>🌊 m</th></tr>\n`;
                extremes.forEach(r => {
                  clog(r);
                  const ts = new Date(r.dateTime);
                  let date = ts.toLocaleString(locale, {
                    month: '2-digit', day: '2-digit', weekday: 'short', // year: 'numeric',
                  }).replace(',', '');
                  if (date0 === date) date = '';
                  else date0 = date;
                  const time = ts.toLocaleString(locale, {
                    hour: '2-digit', minute: '2-digit',
                  });
                  const when = ts > now ? 'future' : 'past';
                  const height = r.value / 100;
                  rows += `<tr class="${r.sign} ${when}"><td>${date}</td><td>${time}</td><td>${height?.toFixed(2)}</td></tr>\n`;
                });
                const ref = p.measurements[0].qualityCode == 'MSL' ? 'reference=MSL' : '';
                const table = `<table>\n${rows}</table>${ref}`;
                // clog(table);

                layer
                  .bindPopup(`<div class="tides"><a target="_blank" href="${link}" class="stationname">${p.name}</a>${table}<div class="source">source <a target="_blank" href="https://waterinfo.rws.nl/publiek/astronomische-getij">RWS</a></div></div>`)
                  .openPopup();
              }).catch(clog);
          });
        }
      }).addTo(map);
    }).catch(clog);
}

import L from "leaflet";
import "leaflet.tilelayer.fallback";
import "./slider";
import { logger } from "./utils";
import "./tides.less";
import stations_de from "./tides.json";
import { ackee } from "./ackee";

function track(x) {
  ackee.action("378af0c9-00ff-46c2-9eac-d16f2ad7bb36", {
    key: "popup_" + x,
    value: 1,
  });
}

const log = logger("tides", "lightblue");

const PARAMS = new URLSearchParams(window.location.search);
const baseurl = "https://freenauticalchart.net";
const attrTides =
  '<a href="/download/tides/">Tidal Atlas *</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH</a>)';
const locale =
  PARAMS.get("locale") || navigator.language || navigator.userLanguage;
const german = locale.startsWith("de");
const dutch = locale.startsWith("nl");
const lang = german ? "de" : "en";
const SOURCE = german ? "Quelle" : dutch ? "bron" : "source";
const DATE = german ? "Tag" : dutch ? "Dag" : "Day";
const HEIGHT = german ? "Höhe" : dutch ? "Hoogte" : "Height";
const TIMEZONE =
  PARAMS.get("tz") || Intl.DateTimeFormat().resolvedOptions().timeZone;

let tideDataHelgoland;

async function hwHelgoland() {
  if (tideDataHelgoland == null) {
    tideDataHelgoland = await fetch(
      "/forecast/de/items/helgoland_binnenhafen",
    ).then((r) => r.json());
  }
  log(tideDataHelgoland);
  const props = tideDataHelgoland.properties;
  const pred = props.high_water_low_water;
  const now = new Date();
  let hdg0;
  let currentHW = null;
  for (const p of pred) {
    p.timestamp = p.event_timestamp;
    p.height = p.tidal_prediction_value;
    const ts = new Date(p.timestamp);
    if (p.event == "HW") currentHW = p;
    if (hdg0)
      currentHW.coeff =
        (100 * Math.abs(p.height - hdg0)) /
        (props.mean_high_water - props.mean_low_water);
    if (ts > now) break;
    hdg0 = p.height;
  }
  log("currentHW", currentHW);
  return currentHW;
}

export function addTidealAtlas(map, gauges = false) {
  const layers = [];

  for (let i = -6; i <= 6; i++) {
    let s = (i >= 0 ? "+" : "") + i;
    layers.push(
      L.tileLayer.fallback(baseurl + "/tides/hw" + s + "/{z}/{x}/{y}.png", {
        attribution: attrTides.replace(
          "*",
          `HW Helgoland ${s}h`.replace("+0h", ""),
        ),
      }),
    );
  }
  layers.push(
    L.tileLayer.fallback(baseurl + "/tides/fig/{z}/{x}/{y}.png", {
      attribution: attrTides.replace("*", "Figures"),
    }),
  );

  L.control
    .timelineSlider({
      title: "tidal current relative to HW Helgoland",
      button: "Tidal Atlas",
      timelineItems: [
        "off",
        "-6h",
        "-5h",
        "-4h",
        "-3h",
        "-2h",
        "-1h",
        "HW",
        "+1h",
        "+2h",
        "+3h",
        "+4h",
        "+5h",
        "+6h",
        "fig",
      ],
      changeMap: async (p) => {
        let x = p.label.replace("HW", "+0h").replace("h", "");
        if (x.startsWith("-") || x.startsWith("+")) {
          let title = p.slider.title.innerHTML;
          title = title.replace(/ \(.*\)$/, "");
          const hwh = await hwHelgoland();
          const td = formatTimestamp(hwh.timestamp);
          title += ` (${td.time}&thinsp;${td.zone} C&thinsp;${hwh.coeff.toFixed(0)})`;
          p.slider.title.innerHTML = title;
        }
        layers.forEach((l) => {
          if (l._url.includes(x)) {
            map.addLayer(l);
            l.bringToFront();
            ackee.action("378af0c9-00ff-46c2-9eac-d16f2ad7bb36", {
              key: "atlas",
              value: 1,
            });
          } else {
            map.removeLayer(l);
          }
        });
      },
    })
    .addTo(map);
}

async function reproject(geojson, fromCRS = "EPSG:25831", toCRS = "EPSG:4326") {
  const proj4 = (await import("proj4")).default;
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
      geom.coordinates = geom.coordinates.map((ring) =>
        ring.map(reprojectCoord),
      );
    } else if (geom.type === "MultiPolygon") {
      geom.coordinates = geom.coordinates.map((poly) =>
        poly.map((ring) => ring.map(reprojectCoord)),
      );
    } else if (geom.type === "GeometryCollection") {
      geom.geometries.forEach(processGeometry);
    }
    return geom;
  }

  let converted = JSON.parse(JSON.stringify(geojson)); // Deep clone
  if (converted.type === "FeatureCollection") {
    converted.features.forEach((f) => processGeometry(f.geometry));
  } else if (converted.type === "Feature") {
    processGeometry(converted.geometry);
  } else {
    processGeometry(converted);
  }

  return converted;
}

function localTZ(date) {
  const tform = new Intl.DateTimeFormat(locale, {
    timeZoneName: "short",
    timeZone: TIMEZONE,
  });
  const parts = tform.formatToParts(date ?? new Date());
  return parts.find((part) => part.type === "timeZoneName")?.value;
  // return tform.resolvedOptions().timeZone;
}

function formatTimestamp(timestamp) {
  const ts = new Date(timestamp);
  let date = ts
    .toLocaleString(locale, {
      weekday: "short",
      month: "2-digit",
      day: "2-digit",
      // year: "numeric",
    })
    .replace(",", "");
  const time = ts.toLocaleString(locale, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: TIMEZONE,
  });
  const zone = localTZ(ts);
  const tz = TIMEZONE;
  return { date, time, zone, locale, tz };
}

function toISOString(date) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    fractionalSecondDigits: 3,
  }).formatToParts(date);

  const get = (type) => parts.find((p) => p.type === type).value;
  const str = `${get("year")}-${get("month")}-${get("day")}T${get("hour")}:${get("minute")}:${get("second")}`;
  // log(date, str);
  return str;
}

log("now", formatTimestamp(new Date()));

function mergeNoClobber(target, source) {
  for (const [key, value] of Object.entries(source)) {
    if (!(key in target)) {
      target[key] = value;
    }
  }
  return target;
}

const plotNames = ["astro", "forecast", "measured"];
const plotColors = ["blue", "red", "green"];

async function tidePlot(traces) {
  const now = new Date();
  const t0 = new Date(now.getTime() - 6 * 3600_000);
  const t1 = new Date(now.getTime() + 18 * 3600_000);
  if (Array.isArray(traces[0])) {
    const times = traces[0].map((t) => toISOString(new Date(t)));
    traces = traces.slice(1).map((t, i) => {
      return {
        name: plotNames[i] || `trace_${i}`,
        x: times,
        y: t,
        type: "scatter",
        mode: "lines",
        line: { color: plotColors[i] || "black" },
      };
    });
  } else {
    traces = traces.map((t, i) =>
      mergeNoClobber(t, {
        name: plotNames[i] || `trace_${i}`,
        type: "scatter",
        mode: "lines",
        line: { color: plotColors[i] || "black" },
      }),
    );
  }
  const layout = {
    title: "Tide Forecast",
    margin: { l: 15, r: 0, t: 0, b: 15 },
    xaxis: {
      title: "Date",
      type: "date",
      fixedrange: !true,
      tickformat: "%a %H:%M",
      range: [t0, t1],
    },
    yaxis: { title: "Height", fixedrange: true, tickangle: -90 },
    shapes: [
      {
        type: "line",
        x0: now,
        x1: now,
        xref: "x",
        y0: 0,
        y1: 1,
        yref: "paper",
        line: { color: "gray", width: 1 },
      },
    ],
    dragmode: "pan",
    legend: {
      x: 0,
      y: -0.05,
      orientation: "h",
      bgcolor: "rgba(255,255,255,0)",
    },
    hovermode: "x unified",
  };
  const config = {
    scrollZoom: true,
  };
  const Plotly = await import("plotly.js-basic-dist");
  Plotly.newPlot("plot", traces, layout, config);
}

export async function addTideGauges(map) {
  return Promise.all([
    addTideGaugesDE(map),
    addTideGaugesNL(map),
    // addTideGaugesNL(map, "waterhoogte"),
    addTideGaugesUK(map),
    addTideGaugesFR(map),
  ]);
}

export async function addTideGaugesDE(map, preFetch = false) {
  const colors = { 1: "white", 2: "lightblue", 3: "gray" };
  const layer = L.layerGroup().addTo(map);
  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  });

  async function showPopup(marker, f) {
    const now = new Date();
    const today = new Date(now);
    today.setHours(0);
    today.setMinutes(0);
    today.setSeconds(0);
    today.setMilliseconds(0);
    // refetch if data is old
    if (now - new Date(f.properties.forecast_timestamp) > 6 * 3600_000) {
      const g = await fetch(`/forecast/de/items/${f.id}?lang=en&f=json`)
        .then((r) => r.json())
        .catch(console.error);
      // log(g);
      if (g?.gauge_label) f = g;
    }
    const p = f.properties;
    // log(p);
    track("de");
    const offset =
      p.chartdatum_relative_to_gaugezero ??
      stations_de[f.id]["SKN (ueber PNP)"];
    const mhw = (p.mean_high_water - offset) / 100;
    const mlw = (p.mean_low_water - offset) / 100;
    const basevalues = p.region.includes("baltic")
      ? ""
      : `<span>MHW ${mhw.toFixed(2)}</span><span>MNW ${mlw.toFixed(2)}</span><span>MTH ${(mhw - mlw).toFixed(2)}</span>`;
    const forecast_ts = new Date(p.forecast_timestamp);
    const forecast_date = formatTimestamp(forecast_ts);
    const forecast_text = p.forecast_text[lang];
    const forecast_cls = now - forecast_ts > 8 * 3600_000 ? "old" : "new";
    const notice = stations_de[f.id]?.notice || [];

    let table = "";
    const prediction = p.high_water_low_water;
    if (prediction) {
      let rows = `<tr><th>${DATE}</th><th>${localTZ()}</th><th title="Höhe der Gezeit in Metern (astronomisch), Abweichung K durch Wettereinfluss">HdG&nbsp;&nbsp;&nbsp;K</th><th title="C = 100 × (Stieg|Fall)/MSpTH">Coeff</th></tr>\n`;
      let last_date = "";
      let c = 0;
      let height0 = null;
      prediction.forEach((r) => {
        const ts = new Date(r.event_timestamp);
        if (ts >= today && c++ < 8) {
          // log("row", r);
          const td = formatTimestamp(ts);
          const when = ts > now ? "future" : "past";
          const date = td.date == last_date ? "" : td.date;
          const height = (r.tidal_prediction_value - offset) / 100;
          const d = (r.forecast_value - r.tidal_prediction_value) / 100;
          const deviation = d ? (d < 0 ? "" : "+") + d.toFixed(1) : "";
          const MSpTH = stations_de[f.id]?.MSpTH / 100 || mhw - mlw;
          const c = (100 * Math.abs(height - height0)) / MSpTH;
          const coeff = height0 && c ? c.toFixed(0) : "";
          rows += `<tr class="${r.event} ${when}"><td>${date}</td><td title="${r.event_timestamp}">${td.time}</td><td>${height.toFixed(2)} <span class="deviation" title="M${r.event}${r.forecast_deviation}">${deviation}</span><td><span class="coeff">${coeff}</span></td></tr>\n`;
          last_date = td.date;
          height0 = height;
        }
      });
      table = `<table>\n${rows}</table>`;
    }

    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="${p.bsh_url_waterlevel ?? "https://gezeiten.bsh.de/" + f.id}" class="stationname">${p.gauge_label}</a>
        ${table}
        <div class="basevalues">${basevalues}</div>
        <div class="notice">${notice.join("<br/>")}</div>
        <div class="section">${p.official_warning_level_region ?? p.automated_gauge_warning}</div>
        <div class="forecast ${forecast_cls}">${forecast_text} (${forecast_date.date} ${forecast_date.time} ${forecast_date.zone})</div>
        <div id="plot"></div>
        <div class="source">${SOURCE} <a target="_blank" href="https://wasserstand.bsh.de">BSH</a></div></div>`,
      )
      .openPopup();

    const curve = p.curve;
    if (!curve) return;
    tidePlot([
      curve.map((d) => d.timestamp),
      curve.map((d) => ((d.tidal_prediction ?? NaN) - offset) / 100),
      curve
        .map((d) => (d.automated_curve_forecast - offset) / 100)
        .map((v) => (v > 0 ? v : null)),
      curve
        .map((d) => (d.measurement - offset) / 100)
        .map((v) => (v > 0 ? v : null)),
    ]);
  }

  fetch("/forecast/de/items?lang=en&f=json")
    .then((r) => r.json())
    .then((data) => {
      // log(data);
      data.features.forEach((f) => {
        const p = f.properties;
        // log(p);
        // if (!p.bsh_url_waterlevel) return;
        if (f.id == "helgoland_binnenhafen") tideDataHelgoland = f;
        let m = L.circleMarker([p.latitude, p.longitude], {
          radius: 4,
          weight: 3,
          color: p.gauge_label.includes("Helgoland") ? "darkred" : "blue",
          fillColor: colors[p.bsh_url_waterlevel ? 1 : 2],
          fillOpacity: 1,
        })
          .bindPopup(
            `<a target="_blank" href="${p.bsh_url_waterlevel ?? "https://gezeiten.bsh.de/" + f.id}">${p.gauge_label}</a>`,
          )
          .on("click", (e) => showPopup(e.target, f))
          .addTo(layer);
        // if (isDevMode && g.station_name.includes('Helgoland')) showPopup(m, g);
      });
    })
    .catch(log);

  return;
  fetch("/tides/de/data/tides_overview.json")
    .then((r) => r.json())
    .then((data) => {
      // log(data);
      let stations = {};
      data.gauges.forEach(async (g) => {
        // log(g);
        const x = await fetch(
          `/tides/de/data/DE_${g.bshnr.padStart(5, "_")}_tides.json`,
        ).then((r) => r.json());
        // log(x);
        stations[x.seo_id] = x.years[0][2026];
        delete stations[x.seo_id].hwnw_prediction;
        Object.keys(stations[x.seo_id]).forEach((key) => {
          if (stations[x.seo_id][key] === null) delete stations[x.seo_id][key];
        });
        log(JSON.stringify(stations));
      });
    });
}

export async function addTideGaugesNL(map, kind = "astronomische-getij") {
  const iswh = kind == "waterhoogte";
  const data = await fetch(
    `/tides/nl/api/point/latestmeasurement?parameterId=${kind}`,
  )
    .then((r) => r.json())
    .then((data) => reproject(data))
    .catch(log);

  const layer = L.geoJSON(data, {
    pointToLayer: function (feature, latlng) {
      const props = feature.properties;
      // log(props);
      return L.circleMarker(latlng, {
        radius: 4,
        weight: 3,
        color: iswh ? props.locationColor : "#4e91ea",
        fillColor: "white",
        fillOpacity: 1,
      });
    },
    onEachFeature: (feature, layer) => {
      const p = feature.properties;
      const link = `https://waterinfo.rws.nl/publiek/${kind}/${p.locationCode}/details`;
      if (p.name) {
        layer.bindPopup(`<a href="${link}" target="_blank">${p.name}</a>`);
      }
      layer.on("click", (e) => {
        // log(p);
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

        fetch(
          `/tides/nl/api/chart/get?mapType=${kind}&locationCodes=${p.locationCode}&getijReference=LAT&timeZone=GMT&startDate=${start.toISOString()}&endDate=${end.toISOString()}`,
          {
            headers: {
              Accept: "application/json",
            },
          },
        )
          .then((r) => r.json())
          .then((data) => {
            log(data);

            const extremes = data.series[0].extremes;

            let table = "";
            if (extremes) {
              let date0;
              let rows = `<tr><th>${DATE}</th><th>${localTZ()}</th><th>${HEIGHT}</th></tr>\n`;
              extremes.forEach((r) => {
                // log(r);
                const ts = new Date(r.dateTime);
                const td = formatTimestamp(ts);
                let date = td.date;
                if (date0 === date) date = "";
                else date0 = date;
                const time = td.time;
                const when = ts > now ? "future" : "past";
                const height = r.value / 100;
                rows += `<tr class="${r.sign} ${when}"><td>${date}</td><td title="${r.dateTime}">${time}</td><td>${height?.toFixed(2)}</td></tr>\n`;
              });
              const ref =
                p.measurements[0].qualityCode == "MSL" ? "reference=MSL" : "";
              table = `<table>\n${rows}</table>${ref}`;
              // log(table);
            } else table = `<div>${p.locationLabel} (NAP)</div>`;

            track("nl");
            layer
              .bindPopup(
                `<div class="tides"><a target="_blank" href="${link}" class="stationname">${p.name}</a>${table}<div class="basevalues"></div><div id="plot"></div><div class="source">${SOURCE} <a target="_blank" href="https://waterinfo.rws.nl/publiek/astronomische-getij">RWS</a></div></div>`,
              )
              .openPopup();

            if (!iswh) {
              tidePlot([
                data.series[0].data.map((d) => d.dateTime),
                data.series[0].data.map((d) => d.value / 100),
              ]);
            } else {
              function sname(name) {
                if (name.includes("astro")) return "astro";
                if (name.includes("verwacht")) return "forecast";
                return "measured";
              }
              function scolor(name) {
                if (name.includes("astro")) return "blue";
                if (name.includes("verwacht")) return "red";
                return "green";
              }
              fetch(
                `/tides/nl/api/chart/get?mapType=waterhoogte&locationCodes=${p.locationCode}&values=-48%2C48`,
                {
                  headers: {
                    Accept: "application/json",
                  },
                },
              )
                .then((r) => r.json())
                .then((d) => {
                  tidePlot(
                    d.series.map((s) => {
                      return {
                        name: sname(s.meta.displayName),
                        x: s.data.map((d) => new Date(d.dateTime)),
                        y: s.data.map((d) => d.value / 100),
                        line: { color: scolor(s.meta.displayName) },
                      };
                    }),
                  );
                });
            }
          })
          .catch(log);
      });
    },
  }).addTo(map);

  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  });
}

export async function addTideGaugesUK(map, preFetch = false) {
  const layer = L.layerGroup().addTo(map);

  async function showPopup(marker, f) {
    // log(marker, f);
    const ID = f.properties.Id;
    const name = f.properties.Name;
    const data = await fetch(`/tides/uk/GetPredictionData?stationId=${ID}`)
      .then((r) => r.json())
      .catch(log);
    if (!data) return;
    log(data);
    const note = data.footerNote;
    const events = data.tidalEventList;
    const curve = data.tidalHeightOccurrenceList;
    const lunar = data.lunarPhaseList;
    log(lunar);
    const ldate1 = new Date(lunar[0]?.dateTime + "Z");
    const ldate2 = new Date(ldate1.getTime() + 6 * 3600_000);
    const phase = (lunar[0]?.lunarPhaseType || 0) - 1;

    const now = new Date();
    const now0 = new Date();
    now0.setUTCHours(0, 0, 0, 0);

    const moon = 2;

    let date0;
    let approx = false;
    let rows = `<tr><th>${DATE}</th><th>${localTZ()}</th><th>${HEIGHT}</th><th class="moon${moon}"></th></tr>\n`;
    events.forEach((e) => {
      // log(e);
      const ts = new Date(e.dateTime + "Z");
      if (ts - now0 < 0) return;
      if (ts - now0 > 2 * 86400_000) return;
      const type = e.eventType ? "" : "HW";
      const when = ts > now ? "future" : "past";
      const td = formatTimestamp(ts);
      let date = td.date;
      if (date0 === date) date = "";
      else date0 = date;
      const tapprox = e.isApproximateTime ? "*" : "";
      const time = td.time + tapprox;
      const happrox = e.isApproximateHeight ? "*" : "";
      const height = e.height?.toFixed(1) + happrox;
      const moon = ldate1 < ts && ts < ldate2 ? phase : -1;
      approx = approx || tapprox || happrox;
      rows += `<tr class="${type} ${when}"><td>${date}</td><td title="${e.dateTime + "Z"}">${time}</td><td>${height || ""}</td><td class="${phase} moon${moon}"></td></tr>\n`;
    });

    const table = `<table>\n${rows}</table>`;
    approx = approx ? "* approximated" : "";
    // log(table);
    track("uk");
    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://easytide.admiralty.co.uk/?PortID=${ID}" class="stationname">${name}</a>${table}<div class="basevalues">above chart datum${approx}</div><div class="forecast">${note}</div><div id="plot"></div><div class="source">${SOURCE} <a target="_blank" href="https://easytide.admiralty.co.uk/">UKHO</a></div></div>`,
      )
      .openPopup();

    if (!curve || !curve[0]) return;

    tidePlot([curve.map((d) => d.dateTime), curve.map((d) => d.height)]);
  }

  fetch("/tides/uk/GetStations")
    .then((r) => r.json())
    .then((data) => {
      // log(data);
      data.features.forEach((f) => {
        // log(f);
        const ID = f.properties.Id;
        const name = f.properties.Name;
        const [lon, lat] = f.geometry.coordinates;
        const continuous = f.properties.ContinuousHeightsAvailable;
        let m = L.circleMarker([lat, lon], {
          radius: 4,
          weight: 3,
          color: "darkblue",
          fillColor: continuous ? "white" : "gray",
          fillOpacity: 1,
        })
          .bindPopup(
            `<a target="_blank" href="https://easytide.admiralty.co.uk/?PortID=${ID}">${name}</a>`,
          )
          .on("click", (e) => showPopup(e.target, f))
          .addTo(layer);
      });
    })
    .catch(log);

  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  });
}

export async function addTideGaugesFR(map, preFetch = false) {
  const layer = L.layerGroup().addTo(map);

  async function showPopup(marker, f) {
    log(f);
    const ID = f.properties.cst;
    const name = f.properties.toponyme;
    const today = new Date().toISOString().split("T")[0];
    const data = await fetch(
      `/tides/fr/b2q8lrcdl4s04cbabsj4nhcb/hdm/spm/hlt?harborName=${ID}&duration=2&date=${today}&utc=0&correlation=1`,
    )
      .then((r) => r.json())
      .catch(log);
    if (!data) return;
    // log(data);

    const events = [];
    Object.entries(data).forEach(([k, v]) => {
      // log(k, v);
      v.forEach((e) => {
        if (e[0].includes("none")) return;
        events.push({
          datetime: k + "T" + e[1] + "Z",
          event: e[0].includes("high") ? "HW" : "LW",
          height: parseFloat(e[2]),
          coeff: e[3] == "---" ? null : parseInt(e[3]),
        });
      });
    });

    const now = new Date();

    let date0;
    let rows = `<tr><th>${DATE}</th><th>${localTZ()}</th><th>${HEIGHT}</th><th>Coeff</th></tr>\n`;
    events.forEach((e) => {
      // log(e);
      const ts = new Date(e.datetime);
      const type = e.event;
      const when = ts > now ? "future" : "past";
      const td = formatTimestamp(ts);
      let date = td.date;
      if (date0 === date) date = "";
      else date0 = date;
      const time = td.time;
      const height = e.height?.toFixed(1);
      rows += `<tr class="${type} ${when}"><td>${date}</td><td title="${e.datetime}">${time}</td><td>${height}</td><td>${e.coeff || ""}</td></tr>\n`;
    });

    const table = `<table>\n${rows}</table>`;
    // log(table);

    track("fr");
    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://maree.shom.fr/harbor/${ID}" class="stationname">${name}</a>${table}<div class="basevalues"></div><div class="forecast"></div><div id="plot"></div><div class="source">${SOURCE} <a target="_blank" href="https://maree.shom.fr/">SHOM</a></div></div>`,
      )
      .openPopup();

    const curve = await fetch(
      `/tides/fr/b2q8lrcdl4s04cbabsj4nhcb/hdm/spm/wl?harborName=${ID}&duration=2&date=${today}&utc=0&nbWaterLevels=288`,
    ).then((r) => r.json());
    // log(curve);

    if (!curve) return;

    const curve1 = [];
    Object.entries(curve).forEach(([k, v]) => {
      // log(k, v);
      v.forEach((e) => {
        curve1.push({
          datetime: k + "T" + e[0] + "Z",
          height: e[1],
        });
      });
    });

    tidePlot([curve1.map((d) => d.datetime), curve1.map((d) => d.height)]);
  }

  fetch(
    "/tides/fr/x13f1b4faeszdyinv9zqxmx1/wfs?service=WFS&version=1.0.0&srsName=EPSG:4326&request=GetFeature&typeName=SPM_PORTS_WFS:liste_ports_spm_h2m&outputFormat=application/json",
  )
    .then((r) => r.json())
    .then((data) => {
      // log(data);
      data.features.forEach((f) => {
        // log(f);
        if (!f.properties.official) return;
        const ID = f.properties.cst;
        const name = f.properties.toponyme;
        const [lon, lat] = f.geometry.coordinates;
        let m = L.circleMarker([lat, lon], {
          radius: 4,
          weight: 3,
          color: "purple",
          fillColor: "white",
          fillOpacity: 1,
        })
          .bindPopup(
            `<a target="_blank" href="https://maree.shom.fr/harbor/${ID}">${name}</a>`,
          )
          .on("click", (e) => showPopup(e.target, f))
          .addTo(layer);
      });
    })
    .catch(log);

  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  });
}

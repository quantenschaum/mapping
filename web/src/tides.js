import L from "leaflet";
import "leaflet.tilelayer.fallback";
import "./slider";
import { logger } from "./utils";
import "./tides.less";
import { ackee } from "./ackee";

function track(x) {
  ackee.action("378af0c9-00ff-46c2-9eac-d16f2ad7bb36", {
    key: "popup_" + x,
    value: 1,
  });
}

const isDevMode = process.env.NODE_ENV === "development";
const log = logger("tides", "lightblue");

const baseurl = "https://freenauticalchart.net";
const attrTides =
  '<a href="/download/tides/">Tidal Atlas *</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/gezeitenstromatlas">BSH</a>)';
const locale = navigator.language || navigator.userLanguage;
const german = locale.startsWith("de");
const lang = german ? "de" : "en";
log("locale", locale, "german", german, "lang", lang);

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
      changeMap: (p) => {
        let x = p.label.replace("HW", "+0h").replace("h", "");
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

function localTZ() {
  const tform = new Intl.DateTimeFormat(locale, { timeZoneName: "short" });
  const parts = tform.formatToParts(new Date());
  return parts.find((part) => part.type === "timeZoneName")?.value;
}

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
  const t0 = new Date(now.getTime() - 6 * 3600_000).toISOString();
  const t1 = new Date(now.getTime() + 18 * 3600_000).toISOString();

  if (Array.isArray(traces[0])) {
    traces = traces.slice(1).map((t, i) => {
      return {
        name: plotNames[i] || `trace_${i}`,
        x: traces[0],
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
        x0: now.toISOString(),
        x1: now.toISOString(),
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
  await Promise.all([
    addTideGaugesDE(map),
    addTideGaugesNL(map),
    // addTideGaugesNL(map, "waterhoogte"),
    addTideGaugesUK(map),
    addTideGaugesFR(map),
    addTideGaugesBaltic(map),
  ]);
}

export async function addTideGaugesDE(map, preFetch = false) {
  async function showPopup(marker, g) {
    // log(g);
    const tidedata = await fetch(
      `/tides/de/data/DE_${g.bshnr.padStart(5, "_")}_tides.json`,
    )
      .then((r) => r.json())
      .catch(log);
    log("tidedata", tidedata);
    if (!tidedata) return;

    const forecast_map = await fetch("/forecast/de/data/map.json")
      .then((r) => r.json())
      .catch(log);
    log("forecast_map", forecast_map);

    const forecastdata = await fetch(
      `/forecast/de/data/DE_${g.bshnr.padStart(5, "_")}.json`,
    )
      .then((r) => r.json())
      .catch(log);
    log("forecastdata", forecastdata);

    const now = new Date();
    const today = new Date(now);
    today.setHours(0);
    today.setMinutes(0);
    today.setSeconds(0);
    today.setMilliseconds(0);
    const year = now.getFullYear().toString();
    let ydata;
    tidedata.years.every((y) => {
      ydata = y[year];
      return !ydata;
    });

    const prediction = ydata.hwnw_prediction.data;
    const level = ydata.hwnw_prediction.level;
    const forecast = forecastdata?.hwnw_forecast?.data;
    const curve = forecastdata?.curve_forecast?.data;
    const fc_date = new Date(forecast_map?.creation_forecast);
    const forecast_date = fc_date.toLocaleString(locale, {
      month: "2-digit",
      day: "2-digit",
      weekday: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
    const forecast_text = forecast_map?.forecast_text
      ? forecast_map?.forecast_text[lang] + ` (${forecast_date})`
      : "";
    const forecast_link = curve
      ? `https://wasserstand-nordsee.bsh.de/${g.seo_id}?zeitraum=tag1bis2`
      : "https://wasserstand-nordsee.bsh.de";
    const forecast_cls = now - fc_date > 8 * 3600_000 ? "old" : "new";

    const offsets = {
      PNP: -ydata["SKN (ueber PNP)"],
      SKN: 0,
    };
    const offset = offsets[level];

    const basevalues = ydata.MHW
      ? `MHW: ${(ydata.MHW + offset) / 100} MNW: ${(ydata.MNW + offset) / 100} MTH: ${ydata.MTH / 100}`
      : "";

    let i = 0;
    var moon;
    for (; i < prediction.length; i++) {
      const ts = new Date(prediction[i].timestamp);
      // log(pred.data[i], now, ts, ts >= now);
      let m = prediction[i].moon;
      if (m != undefined) moon = m;
      if (ts > today) break;
    }
    log("moon", moon);

    const tz = localTZ();

    function getForcast(timestamp) {
      if (!forecast) return "";
      const ts = new Date(timestamp).getTime();
      const fc = forecast.find((f) => new Date(f.timestamp).getTime() === ts);
      log(fc);
      if (fc?.forecast) return `${fc.forecast.replace(" m", "")}`;
      return "";
    }

    let date0;
    let rows = `<tr><th>Datum</th><th>${tz}</th><th>HdG [m]</th><th class="moon${moon}"></th></tr>\n`;
    for (let k = i; k < Math.min(i + 8, prediction.length); k++) {
      const r = prediction[k];
      log("prediction", r);
      const ts = new Date(r.timestamp);
      let date = ts
        .toLocaleString(locale, {
          month: "2-digit",
          day: "2-digit",
          weekday: "short", // year: 'numeric',
        })
        .replace(",", "");
      if (date0 === date) date = "";
      else date0 = date;
      const time = ts.toLocaleString(locale, {
        hour: "2-digit",
        minute: "2-digit",
      });
      const hi_lo = r.type;
      const height_astro = r.height / 100;
      let deviation = getForcast(r.timestamp);
      if (deviation) {
        // make forecasted deviation relative to astronomical forecast
        const dev = deviation
          .split(/\s+/)
          .map((s) => parseFloat(s.replace(",", ".")))
          .filter((v) => !isNaN(v));
        const mean_height = (hi_lo == "HW" ? ydata.MHW : ydata.MNW) / 100;
        const dev2 = dev.map((d) => d + mean_height - height_astro);
        deviation = dev2.map((d) => d.toFixed(1)).join(" bis ");
      }
      const height =
        r.height != null ? ((r.height + offset) / 100).toFixed(2) : "-";
      const when = ts > now ? "future" : "past";
      rows += `<tr class="${r.type} ${when}"><td>${date}</td><td>${time}</td><td>${height} <span class="forecast">${deviation}</span></td><td class="${r.phase} moon${r.moon}">${r.phase}</td></tr>\n`;
    }
    const table = `<table>\n${rows}</table>`;
    // log(table);
    //
    track("de");
    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}" class="stationname">${g.station_name}</a>${table}<div class="basevalues">${basevalues}</div><div class="forecast"><a href="${forecast_link}" target="_blank" class="${forecast_cls}">${forecast_text}</a></div><div id="plot"></div><div class="source">source <a target="_blank" href="https://gezeiten.bsh.de">BSH</a></div></div>`,
      )
      .openPopup();

    if (!curve) return;

    tidePlot([
      curve.map((d) => d.timestamp),
      curve.map((d) => (d.astro + offset) / 100),
      curve
        .map((d) => (d.curveforecast + offset) / 100)
        .map((v) => (v > 0 ? v : null)),
      curve
        .map((d) => (d.measurement + offset) / 100)
        .map((v) => (v > 0 ? v : null)),
    ]);
  }

  const layer = L.layerGroup().addTo(map);
  const colors = { 1: "white", 2: "lightblue", 3: "gray" };

  fetch("/tides/de/data/tides_overview.json")
    .then((r) => r.json())
    .then((data) => {
      // log(data);
      data.gauges.forEach((g) => {
        // log(g);
        if (g.gauge_group == 3) return;
        if (preFetch)
          fetch(`/tides/de/data/DE_${g.bshnr.padStart(5, "_")}_tides.json`);
        let m = L.circleMarker([g.latitude, g.longitude], {
          radius: 4,
          weight: 3,
          color: g.station_name.includes("Helgoland") ? "darkred" : "blue",
          fillColor: colors[g.gauge_group],
          fillOpacity: 1,
        })
          .bindPopup(
            `<a target="_blank" href="https://gezeiten.bsh.de/${g.seo_id}">${g.station_name}</a>`,
          )
          .on("click", (e) => showPopup(e.target, g))
          .addTo(layer);
        // if (isDevMode && g.station_name.includes('Helgoland')) showPopup(m, g);
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

            const tz = localTZ();

            const extremes = data.series[0].extremes;

            let table = "";
            if (extremes) {
              let date0;
              let rows = `<tr><th>📅</th><th>${tz}</th><th>🌊 m</th></tr>\n`;
              extremes.forEach((r) => {
                // log(r);
                const ts = new Date(r.dateTime);
                let date = ts
                  .toLocaleString(locale, {
                    month: "2-digit",
                    day: "2-digit",
                    weekday: "short", // year: 'numeric',
                  })
                  .replace(",", "");
                if (date0 === date) date = "";
                else date0 = date;
                const time = ts.toLocaleString(locale, {
                  hour: "2-digit",
                  minute: "2-digit",
                });
                const when = ts > now ? "future" : "past";
                const height = r.value / 100;
                rows += `<tr class="${r.sign} ${when}"><td>${date}</td><td>${time}</td><td>${height?.toFixed(2)}</td></tr>\n`;
              });
              const ref =
                p.measurements[0].qualityCode == "MSL" ? "reference=MSL" : "";
              table = `<table>\n${rows}</table>${ref}`;
              // log(table);
            } else table = `<div>${p.locationLabel} (NAP)</div>`;

            track("nl");
            layer
              .bindPopup(
                `<div class="tides"><a target="_blank" href="${link}" class="stationname">${p.name}</a>${table}<div class="basevalues"></div><div id="plot"></div><div class="source">source <a target="_blank" href="https://waterinfo.rws.nl/publiek/astronomische-getij">RWS</a></div></div>`,
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
                  log(d);
                  tidePlot(
                    d.series.map((s) => {
                      return {
                        name: sname(s.meta.displayName),
                        x: s.data.map((d) => d.dateTime),
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
    // log(data);
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

    // const tz = localTZ();
    const tz = "UTC";
    const moon = 2;

    let date0;
    let approx = false;
    let rows = `<tr><th>📅</th><th>${tz}</th><th>🌊 m</th><th class="moon${moon}"></th></tr>\n`;
    events.forEach((e) => {
      // log(e);
      const ts = new Date(e.dateTime + "Z");
      if (ts - now0 < 0) return;
      if (ts - now0 > 2 * 86400_000) return;
      const type = e.eventType ? "" : "HW";
      const when = ts > now ? "future" : "past";
      let date = ts
        .toLocaleString(locale, {
          timeZone: tz,
          month: "2-digit",
          day: "2-digit",
          weekday: "short", // year: 'numeric',
        })
        .replace(",", "");
      if (date0 === date) date = "";
      else date0 = date;
      const tapprox = e.isApproximateTime ? "*" : "";
      const time =
        ts.toLocaleString(locale, {
          timeZone: tz,
          hour: "2-digit",
          minute: "2-digit",
        }) + tapprox;
      const happrox = e.isApproximateHeight ? "*" : "";
      const height = e.height?.toFixed(1) + happrox;
      const moon = ldate1 < ts && ts < ldate2 ? phase : -1;
      approx = approx || tapprox || happrox;
      rows += `<tr class="${type} ${when}"><td>${date}</td><td title="${ts}">${time}</td><td>${height || ""}</td><td class="${phase} moon${moon}"></td></tr>\n`;
    });

    const table = `<table>\n${rows}</table>`;
    approx = approx ? "* approximated" : "";
    // log(table);
    track("uk");
    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://easytide.admiralty.co.uk/?PortID=${ID}" class="stationname">${name}</a>${table}<div class="basevalues">above chart datum${approx}</div><div class="forecast">${note}</div><div id="plot"></div><div class="source">source <a target="_blank" href="https://easytide.admiralty.co.uk/">UKHO</a></div></div>`,
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
    const tz = localTZ();

    let date0;
    let rows = `<tr><th>📅</th><th>${tz}</th><th>🌊 m</th><th>coeff</th></tr>\n`;
    events.forEach((e) => {
      // log(e);
      const ts = new Date(e.datetime);
      const type = e.event;
      const when = ts > now ? "future" : "past";
      let date = ts
        .toLocaleString(locale, {
          month: "2-digit",
          day: "2-digit",
          weekday: "short", // year: 'numeric',
        })
        .replace(",", "");
      if (date0 === date) date = "";
      else date0 = date;
      const time = ts.toLocaleString(locale, {
        hour: "2-digit",
        minute: "2-digit",
      });
      const height = e.height?.toFixed(1);
      rows += `<tr class="${type} ${when}"><td>${date}</td><td title="${ts}">${time}</td><td>${height}</td><td>${e.coeff || ""}</td></tr>\n`;
    });

    const table = `<table>\n${rows}</table>`;
    // log(table);

    track("fr");
    await marker
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://maree.shom.fr/harbor/${ID}" class="stationname">${name}</a>${table}<div class="basevalues"></div><div class="forecast"></div><div id="plot"></div><div class="source">source <a target="_blank" href="https://maree.shom.fr/">SHOM</a></div></div>`,
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

export async function addTideGaugesBaltic(map) {
  const layer = L.layerGroup().addTo(map);

  gauges_baltic.forEach((g) => {
    const name = g.id.charAt(0).toUpperCase() + g.id.slice(1);
    L.circleMarker(g.pos, {
      radius: 4,
      weight: 3,
      color: "blue",
      fillColor: "gray",
      fillOpacity: 1,
    })
      .bindPopup(
        `<div class="tides"><a target="_blank" href="https://www.bsh.de/aktdat/wvd/ostsee/pegelkurve/de/${g.id}" class="stationname">${name}<br />
        <img src="/forecast/balt/${g.id}-wasserstand-mobile.png" style="max-width: 100%;" /></a>
        <div id="plot">
        <div class="source">source <a target="_blank" href="https://www.bsh.de/DE/DATEN/Vorhersagen/Wasserstand_Ostsee/wasserstand_ostsee_node.html">BSH</a></div>
        </div>`,
      )
      .on("click", (e) => track("baltic"))
      .addTo(layer);
  });

  map.on("zoomend", () => {
    if (map.getZoom() >= 8) {
      if (!map.hasLayer(layer)) map.addLayer(layer);
    } else {
      if (map.hasLayer(layer)) map.removeLayer(layer);
    }
  });
}

const gauges_baltic = [
  {
    pos: [53.8436648730873, 13.858494243912],
    id: "karnin",
  },
  {
    pos: [53.750310387515, 14.0664775589393],
    id: "ueckermuende",
  },
  {
    pos: [54.3717574942496, 12.4189604829756],
    id: "althagen",
  },
  {
    pos: [54.4345393131129, 13.0322210328025],
    id: "barhoeft",
  },
  {
    pos: [54.1697309881668, 12.1033882570632],
    id: "warnemuende",
  },
  {
    pos: [54.3712205767312, 12.7232205648675],
    id: "barth",
  },
  {
    pos: [54.3056821786853, 13.1190147979804],
    id: "stralsund",
  },
  {
    pos: [54.2344610993266, 13.2897144931285],
    id: "stahlbrode",
  },
  {
    pos: [54.0417373644072, 13.7703795207791],
    id: "wolgast",
  },
  {
    pos: [54.5244936484629, 13.0935551573537],
    id: "neuendorf",
  },
  {
    pos: [54.5847664432537, 13.1113622406783],
    id: "kloster",
  },
  {
    pos: [54.5575935956121, 13.2451345829697],
    id: "wittower-faehre",
  },
  {
    pos: [54.3416033935843, 13.4996964003141],
    id: "lauterbach",
  },
  {
    pos: [54.5082930590658, 13.6366513556098],
    id: "sassnitz",
  },
  {
    pos: [54.280666589378, 13.7097569727335],
    id: "thiessow",
  },
  {
    pos: [54.2043478526933, 13.7719056374206],
    id: "ruden",
  },
  {
    pos: [54.2413133375738, 13.9072081427742],
    id: "greifswalder-oie",
  },
  {
    pos: [54.1078601243791, 13.8076220385415],
    id: "karlshagen",
  },
  {
    pos: [54.0603783352471, 14.0008229194429],
    id: "koserow",
  },
  {
    pos: [54.0977113519667, 13.4571529234706],
    id: "greifswald-wieck",
  },
  {
    pos: [54.795056780405, 9.43301766621292],
    id: "flensburg",
  },
  {
    pos: [54.8232672918699, 9.65414099231528],
    id: "langballigau",
  },
  {
    pos: [54.672736033682, 10.0366885843959],
    id: "schleimuende",
  },
  {
    pos: [53.9919967667161, 11.3756421426989],
    id: "timmendorf-poel",
  },
  {
    pos: [53.8987616054927, 11.4579177844637],
    id: "wismar",
  },
  {
    pos: [54.3729593653957, 11.0056641681444],
    id: "heiligenhafen",
  },
  {
    pos: [54.3720866822911, 10.1570496121807],
    id: "kiel-holtenau",
  },
  {
    pos: [54.4995887917968, 10.2732678650434],
    id: "kiel-leuchtturm",
  },
  {
    pos: [54.0965230966469, 10.8049878297893],
    id: "neustadt",
  },
  {
    pos: [54.4966302631479, 11.23887433814],
    id: "marienleuchte",
  },
  {
    pos: [54.6643839117666, 9.93793813426306],
    id: "kappeln",
  },
  {
    pos: [54.5114316939266, 9.56905851883919],
    id: "schleswig",
  },
  {
    pos: [54.474702770338, 9.83600726774434],
    id: "eckernfoerde",
  },
  {
    pos: [53.8930077557352, 10.7030650688505],
    id: "luebeck",
  },
  {
    pos: [53.9580237174946, 10.8721815274298],
    id: "travemuende",
  },
  {
    pos: [54.0830643023035, 12.1551089607214],
    id: "rostock",
  },
  {
    pos: [54.45899747, 12.57181925],
    id: "prerow",
  },
  {
    pos: [54.3722, 12.62228],
    id: "bodstedt",
  },
  {
    pos: [54.24741, 12.4669],
    id: "ribnitz",
  },
  {
    pos: [54.43144, 12.68975],
    id: "zingst",
  },
  {
    pos: [54.47516, 13.44748],
    id: "ralswiek",
  },
  {
    pos: [53.9805, 14.04969],
    id: "pudagla",
  },
  {
    pos: [53.75316, 14.02415],
    id: "grambin",
  },
  {
    pos: [54.226108, 11.090759],
    id: "dahme-seebruecke",
  },
  {
    pos: [54.336143, 10.645835],
    id: "lippe",
  },
  {
    pos: [54.535813, 9.642506],
    id: "fuesing",
  },
];

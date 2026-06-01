import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.tilelayer.fallback";
import "@kvforksorg/leaflet.polylinemeasure";
import "@kvforksorg/leaflet.polylinemeasure/Leaflet.PolylineMeasure.css";
import "leaflet.control.opacity";
// import {LocateControl} from 'leaflet.locatecontrol';
// import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
// import 'leaflet-mouse-position';
// import 'leaflet-mouse-position/src/L.Control.MousePosition.css';
import { OpenLocationCode } from "open-location-code";
// npx png-to-ico src/favicon.png >src/favicon.ico
import "./style.less";
import { log, debounce, logger } from "./utils";
import { legend } from "./legend";
import { degmin } from "./graticule";
// import './scale';
import { NightSwitch } from "./nightmode";
import { WeatherForecast } from "./weather";
import { PrintButton } from "./print";
import { restoreLayers } from "./restore";
import { addVectorLayer } from "./vector";
import { addWattSegler } from "./wattsegler";
import "./boating";
import { registerSW } from "virtual:pwa-register";
import { showDialog } from "./infobox";
import { ackee } from "./ackee";
import {
  addTidealAtlas,
  addTideGauges,
  addTideGaugesDE,
  addTideGaugesNL,
} from "./tides";
import { addBfS, addNfS } from "./bfs";
import "leaflet-mouse-position";
import "leaflet-mouse-position/src/L.Control.MousePosition.css";
import { ChartTools } from "./charttools/charttools";
import { declination } from "./charttools/declination";

const params = new URLSearchParams(window.location.search);
function isSet(name) {
  return params.get(name) == "1";
}
const isDevMode = import.meta.env.DEV;
const isTouch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
const isStandalone = !!(
  window.matchMedia("(display-mode: standalone)").matches ||
  window.navigator.standalone
);
const locale = navigator.language || navigator.userLanguage;
const german = locale.startsWith("de");
const dutch = locale.startsWith("nl");
const langsuffix = german ? "de/" : dutch ? "nl/" : "";

log("PWA", "red", "standalone", isStandalone, "development", isDevMode);

if (isStandalone || isSet("sw")) {
  log("PWA", "red", "registering service worker");
  ackee.record("aed13eec-f7d3-43f5-8483-b12753abd188");
  registerSW({ onNeedRefresh() {}, onOfflineReady() {} });
} else {
  ackee.record("f1a69ffa-afc4-4085-9c7d-044315d27165");
}

const baseurl = "";
// const baseurl = 'https://freenauticalchart.net';
const boundsDE = L.latLngBounds([53.0, 3.3], [56.0, 14.4]);
const boundsNL = L.latLngBounds([51.2, 3.0], [53.8, 7.3]);
const cors = window.location.hostname != "freenauticalchart.net";

function addClass(cls) {
  return function (e) {
    e.target.getContainer().classList.add(cls);
  };
}

const basemaps = {
  "🌍 OpenStreetMap": L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        '<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    },
  ).on("add", addClass("grayscale")),
  "🌍 OpenStreetMap (color)": L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      attribution:
        '<a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    },
  ),
  "🌍 Worldy Imagery": L.tileLayer(
    "https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
      attribution:
        '<a target="_blank" href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">World Imagery</a>',
    },
  ),
  // "🇳🇱 ENC (RWS)": L.tileLayer.wms(
  //   "https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/WMSServer",
  //   {
  //     layers: "0,2,3,4,5,6,7",
  //     version: "1.3.0",
  //     transparent: "true",
  //     format: "image/png",
  //     tiled: true,
  //     attribution:
  //       '<a target="_blank" href="https://rijkswaterstaat.nl/">RWS</a> <a target="_blank" href="https://geo.rijkswaterstaat.nl/arcgis/rest/services/ENC/mcs_inland/MapServer/exts/MaritimeChartService/">Chart Server</a>',
  //     bounds: boundsNL,
  //   },
  // ),
  "🇳🇱 Luchtfoto": L.tileLayer.wms(
    "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0",
    {
      layers: "Actueel_ortho25",
      version: "1.3.0",
      transparent: "true",
      format: "image/jpg",
      tiled: true,
      attribution: '<a target="_blank" href="https://www.pdok.nl/">PDOK</a>',
      bounds: boundsNL,
    },
  ),
};

const overlays = {
  Grid: L.latlngGraticule({ opacityControl: false }),
  "🇪🇺 EMODnet Bathymetry": L.tileLayer
    .wms("https://ows.emodnet-bathymetry.eu/wms", {
      version: "1.3.0",
      transparent: "true",
      format: "image/png",
      tiled: true,
      layers: "emodnet:mean_multicolour",
      attribution:
        '<a target="_blank" href="https://emodnet.ec.europa.eu/">EMODnet</a>',
    })
    .on("add", addClass("invert")),
  // "🇪🇺 IGKB Tiefenschärfe": L.tileLayer.wms(
  //   "https://www.lfu.bayern.de/gdi/wms/wasser/bodenseetiefenvermessung",
  //   {
  //     version: "1.3.0",
  //     transparent: "true",
  //     format: "image/png",
  //     tiled: true,
  //     layers: "bodensee_wassertiefen",
  //     attribution:
  //       '<a target="_blank" href="https://www.igkb.org/forschungsprojekte/tiefenschaerfe">IGKB</a>',
  //   },
  // ),
  "🇳🇱 FNC NL": L.tileLayer.fallback(baseurl + "/fnc-nl/{z}/{x}/{y}.png", {
    attribution:
      '<a href="/download/">FNC NL</a> (<a target="_blank" href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS</a>)',
    bounds: boundsNL,
    crossOrigin: cors,
  }),
  "🇩🇪 FNC DE": L.tileLayer.fallback(baseurl + "/fnc-de/{z}/{x}/{y}.png", {
    attribution:
      '<a href="/download/">FNC DE</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH</a>)',
    bounds: boundsDE,
    crossOrigin: cors,
  }),
  "🌍 OpenSeaMap": L.tileLayer(
    "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
    {
      attribution:
        '<a target="_blank" href="https://openseamap.org/">OpenSeaMap</a>',
      opacityControl: false,
    },
  ),
};

if (isDevMode || params.get("pm") == "1") {
  const { PMTiles, leafletRasterLayer } = await import("pmtiles");
  let pm = {
    "🇳🇱 FNC NL (pmtiles)": leafletRasterLayer(new PMTiles("/fnc-nl.pmtiles"), {
      attribution:
        '<a href="/download/">FNC NL</a> (<a target="_blank" href="https://www.vaarweginformatie.nl/frp/main/#/page/infra_enc">RWS</a>)',
      bounds: boundsNL,
      crossOrigin: cors,
    }),
    "🇩🇪 FNC DE (pmtiles)": leafletRasterLayer(new PMTiles("/fnc-de.pmtiles"), {
      attribution:
        '<a href="/download/">FNC DE</a> (<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH</a>)',
      bounds: boundsDE,
      crossOrigin: cors,
    }),
  };
  Object.assign(overlays, pm);
}

if (!isStandalone) {
  overlays["QMAP DE 2025-02"] = L.tileLayer.fallback(
    baseurl + "/qmap-de.2025-02-06/{z}/{x}/{y}.png",
    {
      attribution: '<a href="/download/">QMAP DE 2025-02</a>',
      bounds: boundsDE,
      crossOrigin: cors,
    },
  );
  overlays["QMAP DE 2026-03"] = L.tileLayer.fallback(
    baseurl + "/qmap-de.2026-03-02/{z}/{x}/{y}.png",
    {
      attribution: '<a href="/download/">QMAP DE 2026-03</a>',
      bounds: boundsDE,
      crossOrigin: cors,
    },
  );
  overlays["QMAP NL 2026-03"] = L.tileLayer.fallback(
    baseurl + "/qmap-nl.2026-03-08/{z}/{x}/{y}.png",
    {
      attribution: '<a href="/download/">QMAP NL 2026-03</a>',
      bounds: boundsDE,
      crossOrigin: cors,
    },
  );
}

if (isDevMode) {
  overlays["FNC NL tileserver"] = L.tileLayer(
    "http://localhost:8000/styles/fnc-nl/256/{z}/{x}/{y}.png",
    { bounds: boundsNL },
  );
  overlays["FNC DE tileserver"] = L.tileLayer(
    "http://localhost:8000/styles/fnc-de/256/{z}/{x}/{y}.png",
    { bounds: boundsDE },
  );
  overlays["FNC NL mapproxy"] = L.tileLayer(
    "http://localhost:8001/tiles/1.0.0/fnc-nl/EPSG3857/{z}/{x}/{y}.png",
    { bounds: boundsNL },
  );
  overlays["FNC DE mapproxy"] = L.tileLayer(
    "http://localhost:8001/tiles/1.0.0/fnc-de/EPSG3857/{z}/{x}/{y}.png",
    { bounds: boundsDE },
  );
}

if (isSet("bsh")) {
  const bsh = {
    "BSH Bathymetry": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/ELC_INSPIRE/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        layers: "EL.GridCoverage",
        attribution:
          '<a target="_blank" href="https://inspire-geoportal.ec.europa.eu/srv/api/records/5afbd3f9-8bd8-4bfc-a77c-ac3de4ace07f">BSH Bathymetry</a>',
        bounds: boundsDE,
      },
    ),
    "BSH SkinOfEarth": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/NAUTHIS_SkinOfTheEarth/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        layers: "Coastal_Depth_area,Approach_Depth_area,Harbour_Depth_area",
        attribution:
          '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
        bounds: boundsDE,
      },
    ),
    "BSH Hydro": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/NAUTHIS_Hydrography/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        layers:
          "Approach_Depths,Approach_Fishing_Facility_Marine_Farm_Areas,Approach_Offshore_Installations,Approach_Areas_Limits",
        attribution:
          '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
        bounds: boundsDE,
      },
    ),
    "BSH NavAids": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/NAUTHIS_AidsAndServices/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        layers:
          "Coastal_Lights,Coastal_Lateral_Beacons,Coastal_Cardinal_Beacons,Coastal_All_Other_Beacons,Coastal_Lateral_Buoys,Coastal_Cardinal_Buoys,Coastal_All_Other_Buoys,Coastal_Fog_Signals_Daymarks,Approach_Lights,Approach_Lateral_Beacons,Approach_Cardinal_Beacons,Approach_All_Other_Beacons,Approach_Lateral_Buoys,Approach_Cardinal_Buoys,Approach_All_Other_Buoys,Approach_Fog_Signals_Daymarks,Harbour_Lights,Harbour_Lateral_Beacons,Harbour_Cardinal_Beacons,Harbour_All_Other_Beacons,Harbour_Lateral_Buoys,Harbour_Cardinal_Buoys,Harbour_All_Other_Buoys,Harbour_Fog_Signals_Daymarks",
        attribution:
          '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
        bounds: boundsDE,
      },
    ),
    "BSH Topo": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/NAUTHIS_Topography/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        layers: "4_Approach,5_Harbour",
        attribution:
          '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
        bounds: boundsDE,
      },
    ),
    "BSH Obstr": L.tileLayer.wms(
      "https://gdi.bsh.de/mapservice_gs/NAUTHIS_RocksWrecksObstructions/ows",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        layers: "4_Approach,5_Harbour",
        attribution:
          '<a target="_blank" href="https://www.geoseaportal.de/mapapps/resources/apps/navigation/">BSH GeoSeaPortal</a>',
      },
    ),
    "BSH Contours": L.tileLayer.wms(
      "https://gdi.bsh.de/en/mapservice/Elevation-depth-contours-WMS",
      {
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        layers: "EL.ContourLine",
        attribution:
          '<a target="_blank" href="https://inspire-geoportal.ec.europa.eu/srv/api/records/cee22cf8-60c0-401b-8a98-e01959b66f9b">BSH Contours</a>',
        bounds: boundsDE,
      },
    ),
    "Vaarweg Markeringen": L.tileLayer.wms(
      "https://geo.rijkswaterstaat.nl/services/ogc/gdr/vaarweg_markeringen/ows",
      {
        layers: "vaarweg_markering_drijvend,vaarweg_markering_vast",
        version: "1.3.0",
        transparent: "true",
        format: "image/png",
        tiled: true,
        attribution:
          '<a target="_blank" href="https://data.overheid.nl/dataset/5eb0f65c-e90f-464e-8f46-01c5eeb6adf5">RWS Buoys</a> <a target="_blank" href="https://data.overheid.nl/dataset/2bf96f3b-128d-4506-85e0-08e8fc19a11c">RWS Beacons</a>',
      },
    ),
  };
  Object.assign(overlays, bsh);
}

const map = L.map("map", {
  center: [54.264, 9.196],
  zoom: 8,
  minZoom: 6,
  maxZoom: 18,
  zoomControl: false,
  layers: [
    basemaps["🌍 OpenStreetMap"],
    overlays["Grid"],
    overlays["🇩🇪 FNC DE"],
    overlays["🇳🇱 FNC NL"],
  ],
});

new ChartTools().addTo(map);

// if (!isStandalone)
{
  let deferredPrompt;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
  });

  showDialog({
    img: "logo.webp",
    title: "FreeNauticalChart.net",
    button: german ? "Verstanden!" : dutch ? "Accord!" : "Got it!",
    text: `
        <img src="https://healthchecks.io/b/3/908ee633-599b-4691-ae79-101e8725752c.svg" style='margin-bottom: -0.4ex;' /> <span id='updated'></span>

        <div id="info-en">
          <p class="info">is an open source and open data project that aims to provide free nautical charts for sailors, water and mapping enthousiasts and developers. It focuses on making official chart data easy to access. It is based on data that is available as open data.</p>

          <p style="background:yellow; padding:1ex;">Further parts of the previously freely accessible data have been removed from the BSH server, and access has been made more difficult. <b>The German part of the map now reflects the status as of 2026-04-27 and the last available depth data from 2026-03-02, including corrections based on the NTM.</b> More information: <a href="download/de/opendata/">Open Data</a>.</p>

          <p>For more details, usage instructions and downloads, see the <a href="download/">documentation</a>. Please read the important notes.</p>

          <p style="color:red">The charts provided are for informational and reference purposes only.<br/><span style="font-weight:bold;">They are not intended for navigation. Use at own risk!</span></p>

          <p style="color:blue;">The German BSH now states: "Use of the data for navigation purposes is not permitted."</p>
        </div>

        <div id="info-de" style="display:none;">
          <p class="info">ist ein Open-Source- und Open-Data-Projekt, das kostenlose Seekarten für Segler, Wasser- und Kartografie-Enthusiasten sowie Entwickler bereitstellt. Es hat zum Ziel, amtliche Kartendaten leicht zugänglich zu machen. Es basiert auf Daten, die als Open Data verfügbar sind.</p>

          <p style="background:yellow; padding:1ex;">Auf dem Server des BSH wurden weitere Teile der bislang frei zugänglichen Daten entfernt und der Zugriff erschwert. <b>Der deutsche Teil der Karte zeigt jetzt den Stand vom 27.04.2026 und die zuletzt verfügbaren Tiefenangaben vom 02.03.2026 sowie Korrekturen auf Basis der NfS.</b> Weitere Informationen: <a href="download/de/opendata/">Open Data</a>.</p>

          <p>Weitere Informationen, Anleitungen und Downloads finden Sie in der <a href="download/de/">Dokumentation</a>. Beachten Sie die wichtigen Hinweise.</p>

          <p style="color:red">Die zur Verfügung gestellten Karten dienen nur zu Informations- und Referenzzwecken.<br/><span style="font-weight:bold;">Sie sind nicht für die Navigation geeignet. Verwendung auf eigene Gefahr!</span></p>

          <p style="color:blue;">Das BSH weist jetzt darauf hin: "Die Nutzung der Daten für Navigationszwecke ist nicht gestattet."</p>
        </div>

        <div id="info-nl" style="display:none;">
          <p class="info">is een open-source en open-data project dat gratis zeekaarten biedt voor zeilers, watersport- en cartografie‑enthousiastelingen en ontwikkelaars. Het heeft als doel officiële kaartgegevens gemakkelijker toegankelijk te maken. Het is gebaseerd op gegevens die als open data beschikbaar zijn.</p>

          <p style="background:yellow; padding:1ex;">Op de server van het BSH zijn nog meer delen van de voorheen vrij toegankelijke gegevens verwijderd en is de toegang bemoeilijkt. <b>Het Duitse deel van de kaart toont nu de stand van 27-04-2026 en de laatst beschikbare dieptegegevens van 02-03-2026, inclusief correcties op basis van de BaZ.</b> Meer informatie: <a href="download/de/opendata/">Open Data</a>.</p>

          <p>Meer informatie, gebruiksaanwijzingen en downloads vind je in de <a href="download/nl/">documentatie</a>. Lees de belangrijke opmerkingen.</p>

          <p style="color:red">De verstrekte kaarten zijn uitsluitend voor informatie- en referentiedoeleinden.<br/><span style="font-weight:bold;">Ze zijn niet bedoeld voor navigatie. Gebruik op eigen risico!</span></p>

          <p style="color:blue;">Het Duitse BSH wijst er nu op: "Het gebruik van de gegevens voor navigatiedoeleinden is niet toegestaan."</p>
        </div>

        <button id="installpwa">Install App</button>
        <p style="font-size:0.7em; text-align:right;">version ${import.meta.env.GIT_HASH}</p>`,
    callback: () => {
      fetch(baseurl + "/updated")
        .then((response) => {
          console.log("updated", response);
          if (!response.ok) return;
          const date = new Date(response.headers.get("Last-Modified"))
            .toISOString()
            .slice(0, 10);
          document.getElementById("updated").innerText = `last update ${date}`;
        })
        .catch(console.error);
      console.log(locale);
      if (german) {
        document.getElementById("info-de").style.display = null;
        document.getElementById("info-en").style.display = "none";
      }
      if (dutch) {
        document.getElementById("info-nl").style.display = null;
        document.getElementById("info-en").style.display = "none";
      }
      const installButton = document.getElementById("installpwa");
      if (!deferredPrompt) {
        installButton.style.display = "none";
      } else {
        installButton.addEventListener("click", () => {
          deferredPrompt.prompt();
          deferredPrompt = null;
        });
      }
    },
  });
}

const SteplessControl = L.Control.extend({
  onAdd: function (map) {
    const div = L.DomUtil.create(
      "div",
      "zoom-step-toggle leaflet-bar leaflet-control",
    );
    var button = L.DomUtil.create("a");
    button.innerHTML = "&#x1f512;"; // 🔒
    button.title = "toggle stepless zoom";
    div.appendChild(button);

    L.DomEvent.on(button, "click", function (e) {
      L.DomEvent.stopPropagation(e);
      L.DomEvent.preventDefault(e);

      const isStepless = map.options.zoomSnap === 0;

      if (isStepless) {
        map.options.zoomSnap = 1;
        map.options.zoomDelta = 1;
        button.innerHTML = "&#x1f512;"; // 🔒
        map.setZoom(map.getZoom());
      } else {
        map.options.zoomSnap = 0;
        map.options.zoomDelta = 0.1;
        button.innerHTML = "&#x1f513;"; // 🔓
      }
    });

    L.DomEvent.disableClickPropagation(div);
    return div;
  },
});

// --- Add control to map ---
map.addControl(new SteplessControl({ position: "topleft" }));

function updateAttribution(online = true) {
  const attrib = `<a class="highlight" href="/download/${langsuffix}">freenauticalchart.net (?)</a> | <a target="_blank" href="https://leafletjs.com/">Leaflet</a>`;

  if (!online) {
    map.attributionControl.setPrefix(attrib.replace("(?)", "(offline)"));
    return;
  }

  map.attributionControl.setPrefix(attrib);

  fetch(baseurl + "/updated")
    .then((response) => {
      console.log("updated", response);
      if (!response.ok) return;
      const date = new Date(response.headers.get("Last-Modified"))
        .toISOString()
        .slice(0, 10);
      map.attributionControl.setPrefix(attrib.replace("(?)", `(${date})`));
    })
    .catch(console.error);
}

updateAttribution();
window.addEventListener("online", () => updateAttribution(true));
window.addEventListener("offline", () => updateAttribution(false));

const layers = L.control
  .layers(basemaps, overlays, { collapsed: true })
  .addTo(map);

L.control
  .polylineMeasure({
    unit: "nauticalmiles",
    clearMeasurementsOnStop: false,
    showBearings: true,
    showClearControl: true,
    showUnitControl: true,
    unitControlUnits: ["kilometres", "nauticalmiles"],
  })
  .addTo(map);

map.on("contextmenu", (e) => {
  const lat = e.latlng.lat.toFixed(6);
  const lng = e.latlng.lng.toFixed(6);
  const coords = `${lat}, ${lng}`;
  const olc = new OpenLocationCode().encode(e.latlng.lat, e.latlng.lng);
  const latDM = degmin(e.latlng.lat, 3, true, true);
  const lngDM = degmin(e.latlng.lng, 3, false, true);
  const VAR = declination(e.latlng);
  if (isDevMode) navigator.clipboard.writeText(coords);
  L.popup()
    .setLatLng(e.latlng)
    .setContent(
      `${latDM} ${lngDM}<br/>${coords}<br/>${olc}<br/>VAR ${degmin(VAR, 0, 0)} (${VAR.toFixed(1)}°)`,
    )
    .openOn(map);
  if (isDevMode && navigator.clipboard)
    navigator.clipboard.writeText(e.originalEvent.shiftKey ? olc : coords);
});

let opacity = L.control.opacity();
let activeOverlays = {};
function updateOpacityControl() {
  map.removeControl(opacity);
  activeOverlays = Object.fromEntries(
    Object.entries(overlays).filter(
      ([k, v]) => v.options.opacityControl !== false && map.hasLayer(v),
    ),
  );
  log("opacity", "cyan", activeOverlays);
  if (Object.keys(activeOverlays).length) {
    opacity = L.control.opacity(activeOverlays, { collapsed: true });
    map.addControl(opacity);
  }
}

map.on("click", (e) => {
  if (e.originalEvent.altKey) {
    const layer = Object.values(activeOverlays).at(-1);
    layer._container.classList.toggle("blink");
  }
});

updateOpacityControl();

map.on("overlayadd overlayremove", debounce(updateOpacityControl));

if (isDevMode || isStandalone) {
  L.control.boating().addTo(map);
  new NightSwitch().addTo(map);
  new WeatherForecast().addTo(map);
}

if (!isTouch) {
  L.control
    .mousePosition({
      latFormatter: (v) => degmin(v, 3, 1, 1),
      lngFormatter: (v) => degmin(v, 3, 0, 1),
      prefix: "",
      separator: "\n ",
      emptyString: "",
    })
    .addTo(map);
}
// map.addControl(new L.Control.ScaleNautic());

if (isSet("ais")) {
  import("./ais").then(({ AISButton }) => {
    new AISButton().addTo(map);
  });
}

if (isSet("dwd")) {
  import("./brightsky").then(({ WeatherButton }) => {
    new WeatherButton(map).addTo(map);
  });
}

if (isDevMode || !isStandalone) new PrintButton().addTo(map);

if (isSet("gpx")) {
  import("./gpx").then(({ GPXbutton }) =>
    new GPXbutton({ position: "topleft", layers: layers }).addTo(map),
  );
}

addTidealAtlas(map);
if (isStandalone || params.get("tides")) {
  addTideGauges(map);
  if (params.get("tides") == "2") {
    addWattSegler(map);
  }
} else {
  Promise.all([addTideGaugesDE(map), addTideGaugesNL(map)]);
}

if (params.get("bfs")) {
  addBfS(map, params.get("bfs") == "1");
}
if (params.get("nfs") == "1") {
  addNfS(map);
}

legend(layers);

if (isSet("vector")) {
  Promise.all([
    import("@maplibre/maplibre-gl-leaflet"),
    import("maplibre-gl"),
    import("pmtiles"),
  ]).then(([, maplibregl, { Protocol }]) => {
    const protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    layers.addBaseLayer(
      L.maplibreGL({
        style: baseurl + "vector/bsh.json",
      }),
      "FNC-DE Vector (experimental)",
    );
    layers.addBaseLayer(
      L.maplibreGL({
        style: baseurl + "vector/rws.json",
      }),
      "FNC-NL Vector (experimental)",
    );
  });
}

if (isSet("zones")) {
  (async () => {
    const attr =
      '<a target="_blank" href="https://www.nationalpark-wattenmeer.de/wissensbeitrag/befahrensverordnung-karte/">NordSBefV</a>';
    await addVectorLayer(
      layers,
      "allg. Schutzgebiete",
      "/zones/allgemeine.json",
      {
        active: false,
        color: "green",
        legend:
          "Befahren erlaubt, Betreten verboten. Diese Bereiche entsprechen den Kernzonen der Nationalparke, also der „Schutzzone I“ (Schleswig-Holstein), der „Ruhezone (Zone I)“ (Niedersachsen) bzw. der „Zone I“ (Hamburg).",
        attribution: attr,
      },
    );
    await addVectorLayer(
      layers,
      "bes. Schutzgebiete",
      "/zones/besondere.json",
      {
        active: true,
        color: "red",
        legend:
          "Bereiche, die während der jeweiligen Schutzzeit – vom 15. April bis 1. Oktober eines Jahres oder ganzjährig – außerhalb der Fahrwasser grundsätzlich nicht befahren werden dürfen. Innerhalb der Fahrwasser darf ein maschinengetriebenes Wasserfahrzeug maximal mit 12kn (Fahrt über Grund) fahren. Außerhalb der Fahrwasser – soweit außerhalb der jeweiligen Schutzzeit – gilt eine zulässige Höchstgeschwindigkeit von 8kn (Fahrt über Grund). Das Trockenfallen ist in diesen Bereichen untersagt.",
        attribution: attr,
      },
    );
    await addVectorLayer(layers, "Kitesurf-Gebiete", "/zones/kite.json", {
      active: false,
      color: "orange",
      legend:
        "Erlaubniszone, in der Kitesurfen und ähnliche Sportarten wie Wingsurfen erlaubt sind. Außerhalb der Kitesurfgebiete sind diese Sportarten bis auf Windsurfen nicht zulässig.",
      attribution: attr,
    });
    await addVectorLayer(layers, "Schutzgebietsrouten", "/zones/routen.json", {
      active: true,
      color: "purple",
      legend:
        "Routen zum Befahren der Besonderen Schutzgebiete für Wasserfahrzeuge mit einer Breite von 250m, die auch zum Aufenthalt genutzt werden können. Diese Wasserwanderwege sind im Gebiet nicht gekennzeichnet.",
      attribution: attr,
    });
    await addVectorLayer(layers, "Wasserwanderwege", "/zones/wege.json", {
      active: true,
      color: "brown",
      legend:
        "Zusätzliche Routen zum Befahren der Besonderen Schutzgebiete nur für muskelkraftbetriebene Wasserfahrzeuge (Kajaks) mit einer Breite von 250m, die auch zum Aufenthalt genutzt werden können. Diese Wasserwanderwege sind im Gebiet nicht gekennzeichnet.",
      attribution: attr,
    });
    await addVectorLayer(
      layers,
      "Ausstiegsstellen, allg.",
      "/zones/ausstiegeA.json",
      {
        active: true,
        color: "blue",
        legend:
          "Das Trockenfallen und der sonstige Aufenthalt sind in diesen Bereichen in einem Radius von 200m um einen durch Koordinaten bestimmten Punkt erlaubt. Einige Ausstiegs- und Aufenthaltsstellen sind nur für Kanuten und ähnliche muskelkraftbetriebene Kleinfahrzeuge bestimmt. Die Ausstiegs- und Aufenthaltsstellen sind im Gebiet nicht gekennzeichnet.",
        attribution: attr,
      },
    );
    await addVectorLayer(
      layers,
      "Ausstiegsstellen, Kayak",
      "/zones/ausstiegeK.json",
      {
        active: true,
        color: "#09a9ff",
        legend:
          "Das Trockenfallen und der sonstige Aufenthalt sind in diesen Bereichen in einem Radius von 200m um einen durch Koordinaten bestimmten Punkt erlaubt. Einige Ausstiegs- und Aufenthaltsstellen sind nur für Kanuten und ähnliche muskelkraftbetriebene Kleinfahrzeuge bestimmt. Die Ausstiegs- und Aufenthaltsstellen sind im Gebiet nicht gekennzeichnet.",
        attribution: attr,
      },
    );
    await addVectorLayer(layers, "Rotzone", "/zones/rot.json", {
      active: true,
      color: "red",
      legend:
        "Gesperrt für alle - In der Rotzone liegen besonders sensible Lebensräume. Dort ist jegliches Befahren für Wasserfahrzeuge untersagt.",
      attribution:
        '<a target="_blank" href="https://www.nationalpark-vorpommersche-boddenlandschaft.de/karte#&e=3000,3200&c=0,3201,3202">NPVB</a>',
    });
    await addVectorLayer(layers, "Grünzone", "/zones/gruen.json", {
      active: true,
      color: "green",
      legend:
        "Gesperrt für Motoren - In der Grünzone ist ein Befahren mit motorgetriebenen Wasserfahrzeugen verboten. Dort darf sich mit Muskel- oder Windkraft fortbewegt werden.",
      attribution:
        '<a target="_blank" href="https://www.nationalpark-vorpommersche-boddenlandschaft.de/karte#&e=3000,3200&c=0,3201,3202">NPVB</a>',
    });
    restoreLayers(layers, params.get("l"));
  })();
} else {
  restoreLayers(layers, params.get("l"));
}

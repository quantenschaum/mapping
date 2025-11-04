import L from "leaflet";
import { log } from "./utils";

function xlog(...args) {
  log("Vector", "magenta", ...args);
}

export async function addVectorLayer(
  control,
  name,
  url,
  opts = { color: "blue" },
) {
  xlog("add", name, url);
  await fetch(url)
    .then((response) => response.json())
    .then((json) => {
      // xlog('json', json);
      const layer = L.geoJSON(json, {
        ...opts,
        onEachFeature: (f, l) => {
          if (f.properties && f.properties.name) {
            l.bindPopup(f.properties.name);
          }
        },
        style: (f) => {
          if (f.geometry.type == "Point") return {};
          return {
            weight: 4,
            opacity: 0.8,
            color: opts.color,
            fillOpacity: 0.1,
          };
        },
        pointToLayer: (f, latlng) =>
          L.circleMarker(latlng, {
            radius: 6,
            fillColor: opts.color,
            weight: 0,
            fillOpacity: 1,
          }),
      });
      // xlog('add', name, layer);
      control.addOverlay(layer, name);
      if (opts.active) layer.addTo(control._map);
    });
}

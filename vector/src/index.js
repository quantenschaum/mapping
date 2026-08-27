import "maplibre-gl/dist/maplibre-gl.css";
import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";
import "./index.css";

let protocol = new Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

var style =
  (new URL(document.location).searchParams.get("style") ?? "fnc-de") + ".json";

const map = new maplibregl.Map({
  container: "map",
  style: style,
  // center: [9.239, 54.397],
  // zoom: 7,
  hash: true,
});
map.addControl(new maplibregl.NavigationControl(), "top-left");
// map.addControl(new maplibregl.FullscreenControl(), "top-left");
map.addControl(new maplibregl.GeolocateControl(), "top-left");
map.addControl(new maplibregl.ScaleControl(), "bottom-left");

function buttonControl({ text, title, onClick }) {
  return {
    onAdd(map) {
      this._map = map;
      this._el = document.createElement("div");
      this._el.className = "maplibregl-ctrl maplibregl-ctrl-group";

      this._btn = document.createElement("button");
      this._btn.type = "button";
      this._btn.textContent = text;
      this._btn.title = title || text;
      this._btn.addEventListener("click", () => onClick(map));

      this._el.appendChild(this._btn);
      return this._el;
    },
    onRemove() {
      this._el.remove();
      this._map = undefined;
    },
  };
}

function layerToggle({ text, title, prefix, position = "top-right" }) {
  map.addControl(
    buttonControl({
      text,
      title,
      onClick: (map) => {
        const style = map.getStyle();
        const layers0 = style?.layers ?? [];
        const layers1 = layers0.filter((l) =>
          typeof prefix === "string" ? l.id === prefix : prefix.test(l.id),
        );
        if (layers1.length === 0) return;
        const vis0 = layers1.some(
          (l) => map.getLayoutProperty(l.id, "visibility") != "none",
        );
        const vis1 = vis0 ? "none" : "visible";
        layers1.forEach((l) => map.setLayoutProperty(l.id, "visibility", vis1));
      },
    }),
    position,
  );
}

layerToggle({
  text: "Q",
  title: "Quality",
  prefix: /^quality-/,
});

layerToggle({
  text: "L",
  title: "Lights",
  prefix: /^light/,
});

layerToggle({
  text: "B",
  title: "Buoy Labels",
  prefix: /^label-(buoy|beacon|landmark)/,
});

layerToggle({
  text: "O",
  title: "OSM",
  prefix: "openseamarks",
});

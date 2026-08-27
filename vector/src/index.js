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

map.addControl(
  buttonControl({
    text: "Q",
    title: "Data Quality",
    onClick: (map) => {
      const v = map.getLayoutProperty("quality-area", "visibility");
      map.setLayoutProperty(
        "quality-area",
        "visibility",
        v == "none" ? "visible" : "none",
      );
      map.setLayoutProperty(
        "quality-label",
        "visibility",
        v == "none" ? "visible" : "none",
      );
    },
  }),
  "top-right",
);

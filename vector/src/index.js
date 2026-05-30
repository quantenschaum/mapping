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
  center: [9.239, 54.397],
  zoom: 7,
  hash: true,
});
map.addControl(new maplibregl.NavigationControl(), "top-left");

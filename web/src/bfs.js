import L from "leaflet";
import { logger } from "./utils";
import { parse } from "date-fns";
import "./bfs.less";
import { ackee } from "./ackee";

function track(x) {
  ackee.action("2b265eb7-b233-45ad-9fa6-51d7c04c9f9f", {
    key: "popup_" + x,
    value: 1,
  });
}

export async function addBfS(map, only_valid = true) {
  const log = logger("BfS", "orange");
  const now = new Date();
  const index = await fetch("/bfs/index.json")
    .then((r) => r.json())
    .catch(log);
  index.forEach(async (i) => {
    log("BfS", i);
    const data = await fetch(`/bfs/${i}.json`)
      .then((r) => r.json())
      .catch(log);
    const props = data.properties;
    // log(props);
    const { bfs, amt, url, text } = props;
    const t0 = parse(props.from, "yyyy-MM-dd", new Date());
    const t1 = parse(props.to, "yyyy-MM-dd", new Date());
    const expired = t1 < now;
    const valid = props.valid && t0 <= now && now <= t1;
    const temp = props.temporary || bfs.includes("T");
    log(bfs, valid, temp);

    if (!valid && only_valid) return;

    const layer = L.geoJSON(data, {
      // ...opts,
      onEachFeature: (f, l) => {
        const fp = f.properties;
        l.bindPopup(`<div class="bfs">
          <div class="title">${fp.name}</div>
          <div class="source"><a href="${url}" target="_blank">BfS ${bfs} ${amt}</a></div>
            <div class="date ${expired ? "expired" : valid ? "" : "invalid"}">${t0.toISOString().replace(/T.*/, "")} - ${t1.toISOString().replace(/T.*/, "")}</div>
          <div class="text">${fp.desc}</div>
            </div>`);
        if (fp.name) {
          let desc = fp.desc || "";
          if (desc.length > 20) desc = desc.slice(0, 20) + "...";
          l.bindTooltip(fp.name + ": " + desc);
        }
        l.on;
      },
      pointToLayer: (f, latlng) =>
        L.circleMarker(latlng, {
          radius: 4,
          weight: 3,
          color: "gold",
          fillColor: valid ? "green" : "darkred",
          fillOpacity: 1,
        }),
    });

    layer.addTo(map);
  });
}

export async function addNfS(map, year = 2025) {
  const log = logger("NfS", "gold");
  const now = new Date();
  const index = await fetch(`/nfs/${year}/index.json`)
    .then((r) => r.json())
    .catch(log);
  index.forEach(async (i) => {
    log("NfS", i);
    const data = await fetch(`/nfs/${year}/${String(i).padStart(2, "0")}.json`)
      .then((r) => r.json())
      .catch(log);
    if (!data) return;
    const props = data.properties;
    log(props);
    const { number, source, issued } = props;

    const layer = L.geoJSON(data, {
      // ...opts,
      onEachFeature: (f, l) => {
        const fp = f.properties;
        log(fp);
        l.bindPopup(`<div class="bfs">
          <div class="title">${fp.action}</div>
          <div class="text">${fp.desc}</div>
          <div class="source"><a href="${source}" target="_blank">NfS ${number}/${year}</a> ${issued}</div>
          </div>`);
        if (fp.action) {
          let desc = fp.desc || "";
          if (desc.length > 30) desc = desc.slice(0, 30) + "...";
          l.bindTooltip(fp.action + ": " + desc);
        }
      },
      pointToLayer: (f, latlng) => {
        const fp = f.properties;
        return L.circleMarker(latlng, {
          radius: 4,
          weight: 3,
          color: "lightblue",
          fillColor: fp.action.includes("del")
            ? "darkred"
            : fp.action.includes("ins")
              ? "green"
              : fp.action.includes("re")
                ? "orange"
                : "white",
          fillOpacity: 1,
        });
      },
    });

    layer.addTo(map);
  });
}

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

export async function addBfS(map, start_date) {
  const log = logger("BfS", "orange");
  const now = new Date();
  const index = await fetch("/bfs/index.json")
    .then((r) => r.json())
    .catch(log);
  index.forEach(async (i) => {
    // log("BfS", i);
    const data = await fetch(`/bfs/${i}.json`)
      .then((r) => r.json())
      .catch(log);
    const p = data.properties;
    const { bfs, amt, url } = p;
    const text = (p.text || "").replace(/\n/g, "<br>");
    const t0 = parse(p.from, "yyyy-MM-dd", new Date());
    const t1 = parse(p.to, "yyyy-MM-dd", new Date());
    t1.setHours(23, 59, 59, 999);
    const expired = t1 < now;
    const valid = p.valid && t0 <= now && now <= t1;
    const temp = p.temporary || bfs.includes("T");
    if (!valid) return;
    if (!!start_date && start_date.length == 10 && p.from < start_date) return;
    log(i, bfs, valid, temp);
    log(p);

    const layer = L.geoJSON(data, {
      // ...opts,
      onEachFeature: (f, l) => {
        const fp = f.properties;
        l.bindPopup(`<div class="bfs">
          <div class="title">${fp?.name || bfs}</div>
          <div class="source"><a href="${url}" target="_blank">BfS ${bfs} ${amt}</a></div>
            <div class="date ${expired ? "expired" : valid ? "" : "invalid"}">${p.from} - ${p.to}</div>
          <div class="text">${fp?.desc || text}</div>
            </div>`);
        // if (fp?.name || bfs) {
        //   let desc = fp?.desc || "";
        //   if (desc.length > 20) desc = desc.slice(0, 20) + "...";
        //   l.bindTooltip((fp?.name || bfs) + ": " + desc);
        // }
        // l.on;
      },
      pointToLayer: (f, latlng) =>
        L.circleMarker(latlng, {
          radius: 4,
          weight: 3,
          color: "red",
          fillColor: valid ? (temp ? "blue" : "white") : "black",
          fillOpacity: 1,
        }),
    });

    layer.addTo(map);
  });
}

export async function addNfS(map) {
  const log = logger("NfS", "gold");
  const now = new Date();
  const data = await fetch(`/nfs/nfs.json`)
    .then((r) => r.json())
    .catch(log);
  log(data);
  const layer = L.geoJSON(data, {
    onEachFeature: (f, l) => {
      const p = f.properties;
      log(p);
      const [nr, year] = p.nfs.split("/");
      l.bindPopup(`<div class="bfs">
        <div class="title">${p.name}</div>
        <div class="text">${p.desc}</div>
        <div class="source"><a href="https://www2.bsh.de/daten/NFS/NfS${year}/nfs-heft${nr}-${year}.pdf" target="_blank">NfS ${p.nfs}</a><br/>${p.bfs}</div>
        </div>`);
      // if (p.action) {
      //   let desc = p.desc || "";
      //   if (desc.length > 30) desc = desc.slice(0, 30) + "...";
      //   l.bindTooltip(p.action + ": " + desc);
      // }
    },
    pointToLayer: (f, latlng) => {
      const p = f.properties;
      return L.circleMarker(latlng, {
        radius: 4,
        weight: 3,
        color: "green",
        // fillColor: "lightblue",
        fillColor: p?.desc.includes("insert")
          ? "lightgreen"
          : p?.desc.includes("delete")
            ? "red"
            : p?.desc.includes("reloc")
              ? "orange"
              : "lightblue",
        fillOpacity: 1,
      });
    },
  });

  layer.addTo(map);
}

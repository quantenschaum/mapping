import L from "leaflet";
import 'leaflet-geometryutil';
import {debounce, log} from "./utils";

const isDevMode = process.env.NODE_ENV === 'development';

function xlog(...args) {
  log('AIS', 'purple', ...args);
}

export function init_ais(map, wsurl) {
  xlog('init');
  var ws;

  const updateBounds = debounce(() => {
    const bounds = map.getBounds();
    xlog("bounds:", bounds.toBBoxString());
    try {
      var nw = bounds.getNorthWest(), se = bounds.getSouthEast();
      ws.send(JSON.stringify({bbox: [[nw.lat, nw.lng], [se.lat, se.lng]]}));
    } catch (e) {
      console.error("AIS bounds error:", e);
    }
  }, 5000);

  map.on("moveend zoomend", updateBounds);

  const aisLayer = L.layerGroup().addTo(map);

  function boatIcon(hdt, color = 'blue', scale = 1) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="-20 -20 40 40">  <polygon points="0,-15 8,15 -8,15" fill="${color}" fill-opacity="0.3" stroke="black" stroke-width="1.5" transform="rotate(${hdt}) scale(${scale})"/></svg>`;
    const svgUrl = "data:image/svg+xml;base64," + btoa(svg);
    return L.icon({
      iconUrl: svgUrl,
      iconAnchor: [20, 20],
    });
  }

  const aisStatus = {
    0: 'Under way using engine',
    1: 'At anchor',
    2: 'Not under command',
    3: 'Restricted manoeuverability',
    4: 'Constrained by her draught',
    5: 'Moored',
    6: 'Aground',
    7: 'Engaged in Fishing',
    8: 'Under way sailing',
  }

  const aisColor = {
    0: 'blue',
    1: 'black',
    2: 'red',
    3: 'orange',
    4: 'purple',
    5: 'gray',
    6: 'yellow',
    7: 'green',
    8: 'white',
  }

  function formatMMSS(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }

  function addAIS(data) {
    // xlog(data);
    const type = data.MessageType;
    const meta = data.MetaData;
    const mmsi = meta.MMSI;
    const name = meta.ShipName.trim();
    const time = new Date(meta.time_utc);
    const now = new Date();

    aisLayer.eachLayer(l => {
      if (now - l.options.time > 10 * 60000) {
        l.remove();
      }
    });

    if (type == 'PositionReport'
      || type == 'StandardClassBPositionReport'
      || type == 'ExtendedClassBPositionReport') {
      const classB = type != 'PositionReport';
      const pr = data.Message.PositionReport ?? data.Message.StandardClassBPositionReport ?? data.Message.ExtendedClassBPositionReport;
      const status = pr.NavigationalStatus;
      const lat = pr.Latitude, lng = pr.Longitude;
      const pos = [lat, lng];
      let cog = pr.Cog, sog = pr.Sog;
      sog = sog > 100 ? 0 : sog;
      let hdt = pr.TrueHeading > 360 ? cog : pr.TrueHeading;
      xlog(mmsi, name, cog, sog, hdt, aisStatus[status]);

      aisLayer.eachLayer(l => {
        if (l.options.mmsi == mmsi) {
          l.remove();
        }
      });

      const m = L.marker(pos, {
        icon: boatIcon(hdt, aisColor[status] ?? 'blue', classB ? 0.6 : 1),
        mmsi: mmsi,
        time: time,
      }).addTo(aisLayer)
        .bindPopup(() => `<b>${name}</b><br/><a href="https://www.vesselfinder.com/vessels/details/${mmsi}" target="_blank">${mmsi}</a><br/>COG ${cog}° SOG ${sog}kn<br/><i>${aisStatus[status] ?? ''}</i><br/>age ${formatMMSS(new Date() - time)}`);

      if (sog > 0) {
        const src = L.latLng(lat, lng);
        const dest = L.GeometryUtil.destination(src, cog, sog * 1852 / 6);
        const vector = L.polyline([src, dest], {
          color: sog >= 10 ? 'darkred' : 'blue',
          weight: classB ? 1.2 : 1.8,
          mmsi: mmsi,
          time: time,
        }).addTo(aisLayer);
      }

    }
  }


  function connect(url) {
    xlog('connect:', url);

    ws = new WebSocket(url);

    ws.onopen = () => {
      xlog("connected");
      updateBounds();
    };

    ws.onmessage = (e) => {
      // xlog("AIS:", e.data);
      addAIS(JSON.parse(e.data))
    };

    ws.onclose = () => {
      xlog("closed");
      debounce(connect, isDevMode ? 1000 : 5000)(url);
    };

    ws.onerror = (err) => {
      console.error("AIS error:", err);
    };
  }

  connect(wsurl);
}


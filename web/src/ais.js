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
  }, isDevMode ? 1000 : 5000);

  map.on("moveend zoomend", updateBounds);

  const aisLayer = L.layerGroup().addTo(map);

  function boatIcon(hdt, color = 'green') {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="-20 -20 40 40">  <polygon points="0,-15 8,15 -8,15" fill="${color}" fill-opacity="0.3" stroke="black" stroke-width="1.5" transform="rotate(${hdt})"/></svg>`;
    const svgUrl = "data:image/svg+xml;base64," + btoa(svg);
    return L.icon({
      iconUrl: svgUrl,
      iconAnchor: [20, 20],
    });
  }

  function addAIS(data) {
    // xlog(data);
    if (data.MessageType == 'PositionReport') {
      const pr = data.Message.PositionReport;
      const meta = data.MetaData;
      const mmsi = meta.MMSI;
      const now = new Date();
      const time = new Date(meta.time_utc);
      const name = meta.ShipName.trim();
      const lat = pr.Latitude, lng = pr.Longitude;
      const cog = pr.Cog, sog = pr.Sog, hdt = pr.TrueHeading;
      xlog(mmsi, name, time, cog, sog, hdt, data);

      aisLayer.eachLayer(l => {
        // xlog(l);
        if (l.options.mmsi == mmsi) {
          l.remove();
          // if (l instanceof L.Polyline) {
          //   l.remove();
          // }
          // l.setStyle({fillColor: 'gray'});
        }
        if (now - l.options.time > 5 * 60 * 1000) {
          // l.remove();
          // l.setStyle({
          //   color: 'gray',
          //   fillColor: 'gray'
          // });
        }
        if (now - l.options.time > 10 * 60 * 1000) {
          l.remove();
        }
      });

      const marker = L.marker([lat, lng], {
        icon: boatIcon(hdt, sog >= 10 ? 'red' : 'blue'),
        mmsi: mmsi,
        time: time,
        data: data,
      }).addTo(aisLayer).bindPopup(`${name}<br/>${mmsi}<br/>${cog}° ${sog}kn`);

      if (sog > 0) {
        const src = L.latLng(lat, lng);
        const dest = L.GeometryUtil.destination(src, cog, sog * 1852 / 6);
        const vector = L.polyline([src, dest], {
          color: 'blue',
          weight: 1.8,
          mmsi: mmsi,
          time: time,
          data: data,
        }).addTo(aisLayer);
      }

      if (0) {
        L.circleMarker([lat, lng], {
          radius: 5,
          color: sog >= 8 ? 'red' : 'blue',
          weight: 2,
          fillColor: 'blue',
          fillOpacity: 0.6,
          mmsi: mmsi,
          time: time,
          data: data,
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


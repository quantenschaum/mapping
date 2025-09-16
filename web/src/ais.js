import L from "leaflet";
import 'leaflet-geometryutil';
import {debounce, log} from "./utils";

const isDevMode = process.env.NODE_ENV === 'development';

function xlog(...args) {
  log('AIS', 'purple', ...args);
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
};

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
};

const MID_TO_COUNTRY = {
  201: 'AL', 202: 'AD', 203: 'AT', 204: 'PT', 205: 'BE', 206: 'BY', 207: 'BG', 208: 'VA',
  209: 'CY', 210: 'CY', 211: 'DE', 212: 'CY', 213: 'GE', 214: 'MD', 215: 'MT', 216: 'AM',
  218: 'DE', 219: 'DK', 220: 'DK', 224: 'ES', 225: 'ES', 226: 'FR', 227: 'FR', 228: 'FR',
  229: 'MT', 230: 'FI', 231: 'FO', 232: 'GB', 233: 'GB', 234: 'GB', 235: 'GB', 236: 'GI',
  237: 'GR', 238: 'HR', 239: 'GR', 240: 'GR', 241: 'GR', 242: 'MA', 243: 'HU', 244: 'NL',
  245: 'NL', 246: 'NL', 247: 'IT', 248: 'MT', 249: 'MT', 250: 'IE', 251: 'IS', 252: 'LI',
  253: 'LU', 254: 'MC', 255: 'PT', 256: 'MT', 257: 'NO', 258: 'NO', 259: 'NO', 261: 'PL',
  262: 'ME', 263: 'PT', 264: 'RO', 265: 'SE', 266: 'SE', 267: 'SK', 268: 'SM', 269: 'CH',
  270: 'CZ', 271: 'TR', 272: 'UA', 273: 'RU', 274: 'MK', 275: 'LV', 276: 'EE', 277: 'LT',
  278: 'SI', 279: 'RS', 301: 'AI', 303: 'US', 304: 'AG', 305: 'AG', 306: 'CW', 307: 'AW',
  308: 'BS', 309: 'BS', 310: 'BM', 311: 'BS', 312: 'BZ', 314: 'BB', 316: 'CA', 319: 'KY',
  321: 'CR', 323: 'CU', 325: 'DM', 327: 'DO', 329: 'GP', 330: 'GD', 331: 'GL', 332: 'GT',
  335: 'HN', 336: 'HT', 338: 'US', 339: 'JM', 341: 'KN', 343: 'LC', 345: 'MX', 347: 'MQ',
  348: 'MS', 350: 'NI', 351: 'PA', 352: 'PA', 353: 'PA', 354: 'PA', 355: 'PA', 356: 'PA',
  357: 'PA', 358: 'PR', 359: 'SV', 361: 'PM', 362: 'TT', 364: 'TC', 366: 'US', 367: 'US',
  368: 'US', 369: 'US', 370: 'PA', 371: 'PA', 372: 'PA', 373: 'PA', 374: 'PA', 375: 'VC',
  376: 'VC', 377: 'VC', 378: 'VG', 379: 'VI', 401: 'AF', 403: 'SA', 405: 'BD', 408: 'BH',
  410: 'BT', 412: 'CN', 413: 'CN', 414: 'CN', 416: 'TW', 417: 'LK', 419: 'IN', 422: 'IR',
  423: 'AZ', 425: 'IQ', 428: 'IL', 431: 'JP', 432: 'JP', 434: 'TM', 436: 'KZ', 437: 'UZ',
  438: 'JO', 440: 'KR', 441: 'KR', 443: 'PS', 445: 'KP', 447: 'KW', 450: 'LB', 451: 'KG',
  453: 'MO', 455: 'MV', 457: 'MN', 459: 'NP', 461: 'OM', 463: 'PK', 466: 'QA', 468: 'SY',
  470: 'AE', 472: 'TJ', 473: 'YE', 475: 'YE', 477: 'HK', 478: 'BA', 501: 'FR', 503: 'AU',
  506: 'MM', 508: 'BN', 510: 'FM', 511: 'PW', 512: 'NZ', 514: 'KH', 515: 'KH', 516: 'CX',
  518: 'CK', 520: 'FJ', 523: 'CC', 525: 'ID', 529: 'KI', 531: 'LA', 533: 'MY', 536: 'MP',
  538: 'MH', 540: 'NC', 542: 'NU', 544: 'NR', 546: 'PF', 548: 'PH', 553: 'PG', 555: 'PN',
  557: 'SB', 559: 'AS', 561: 'WS', 563: 'SG', 564: 'SG', 565: 'SG', 566: 'SG', 567: 'TH',
  570: 'TO', 572: 'TV', 574: 'VN', 576: 'VU', 577: 'VU', 578: 'WF', 601: 'ZA', 603: 'AO',
  605: 'DZ', 607: 'FR', 608: 'GB', 609: 'BI', 610: 'BJ', 611: 'BW', 612: 'CF', 613: 'CM',
  615: 'CG', 616: 'KM', 617: 'CV', 618: 'FR', 619: 'CI', 620: 'KM', 621: 'DJ', 622: 'EG',
  624: 'ET', 625: 'ER', 626: 'GA', 627: 'GH', 629: 'GM', 630: 'GW', 631: 'GQ', 632: 'GN',
  633: 'BF', 634: 'KE', 635: 'FR', 636: 'LR', 637: 'LR', 638: 'SS', 642: 'LY', 644: 'LS',
  645: 'MU', 647: 'MG', 649: 'ML', 650: 'MZ', 654: 'MR', 655: 'MW', 656: 'NE', 657: 'NG',
  659: 'NA', 660: 'RE', 661: 'RW', 662: 'SD', 663: 'SN', 664: 'SC', 665: 'SH', 666: 'SO',
  667: 'SL', 668: 'ST', 669: 'SZ', 670: 'TD', 671: 'TG', 672: 'TN', 674: 'TZ', 675: 'UG',
  676: 'CD', 677: 'TZ', 678: 'ZM', 679: 'ZW', 701: 'AR', 710: 'BR', 720: 'BO', 725: 'CL',
  730: 'CO', 735: 'EC', 740: 'FK', 745: 'GF', 750: 'GY', 755: 'PY', 760: 'PE', 765: 'SR',
  770: 'UY', 775: 'VE',
};

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
  }, 3000);

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

  function formatMMSS(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }

  function mmsi2country(mmsi) {
    const mid = parseInt(mmsi.toString().slice(0, 3));
    return MID_TO_COUNTRY[mid] ?? '';
  }

  function cc2flag(cc) {
    if (!cc || cc.length !== 2) return '';
    const A = 0x1F1E6; // Unicode code point for regional indicator 'A'
    const codePoints = [...cc.toUpperCase()].map(c => A + c.charCodeAt(0) - 65);
    return String.fromCodePoint(...codePoints);
  }

  function mmsi2Flag(mmsi) {
    const countryCode = mmsi2country(mmsi);
    return countryCode ? cc2flag(countryCode) : '';
  }

  function addAIS(data) {
    // xlog(data);
    const type = data.MessageType;
    const meta = data.MetaData;
    const mmsi = meta.MMSI;
    const country = mmsi2country(mmsi);
    const flag = mmsi2Flag(mmsi);
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
      xlog(mmsi, name, cog, sog, hdt, aisStatus[status], flag);

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
        .bindPopup(() => `<b>${name} <span title="${country}">${flag}</span></b><br/><a href="https://www.vesselfinder.com/vessels/details/${mmsi}" target="_blank">${mmsi}</a><br/>COG ${cog}° SOG ${sog}kn<br/><i>${aisStatus[status] ?? ''}</i><br/>age ${formatMMSS(new Date() - time)}`)
        .bindTooltip(() => `${name}`, {
          // permanent: true,
          className: 'ais-tooltip',
        });

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


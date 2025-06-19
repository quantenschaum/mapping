// based on https://github.com/Leaflet/Leaflet.Graticule

export function degmin(v, n = 2, lat = true) {
  var a = Math.abs(v);
  var d = Math.floor(a);
  var f = Math.pow(10, n);
  var m = Math.round(((60 * a) % 60) * f) / f;
  while (m >= 60) {
    m -= 60;
    d += 1;
  }
  var M = m == 0 ? "" : m.toFixed(n).replace(/\.?0+$/, "") + "'";
  if (lat) {
    var s = v < 0 ? 'S' : v > 0 ? 'N' : '';
  } else {
    v %= 360;
    v -= Math.abs(v) > 180 ? Math.sign(v) * 360 : 0;
    var s = v < 0 ? 'W' : v > 0 ? 'E' : '';
  }
  return `${s} ${d}° ${M}`;
}

L.LatLngGraticule = L.Layer.extend({
  options: {
    showLabel: true,
    borders: 10,
    opacity: 1,
    weight: 1,
    color: '#333',
    fontFamily: 'Open Sans, Verdana, sans-serif',
    fontSize: 12,
    fontColor: 'black',
    intervals: [
      {start: 2, interval: 30},
      {start: 5, interval: 20},
      {start: 6, interval: 10},
      {start: 7, interval: 5},
      {start: 8, interval: 2},
      {start: 9, interval: 1},
      {start: 10, interval: 30 / 60},
      {start: 11, interval: 15 / 60},
      {start: 12, interval: 10 / 60},
      {start: 13, interval: 5 / 60},
      {start: 14, interval: 2 / 60},
      {start: 15, interval: 1 / 60},
      {start: 16, interval: 1 / 60 / 2},
      {start: 17, interval: 1 / 60 / 5},
      {start: 18, interval: 1 / 60 / 10},
    ],
    latFormatTickLabel: v => degmin(v, 2, true),
    lngFormatTickLabel: v => degmin(v, 2, false),
  },

  initialize: function (options) {
    // console.log('init graticule');
    L.setOptions(this, options);
    if (this.options.borders) {
      var css = document.createElement('style');
      const m = this.options.borders + 1;
      css.innerHTML = `.grid .leaflet-control-attribution { margin-bottom: ${m}px !important; margin-left: ${m}px !important; margin-right: ${m}px !important; } .grid .leaflet-control-scale { margin-bottom: ${m + 5}px !important; margin-left: ${m + 5}px !important; }`;
      document.head.appendChild(css);
    }
  },

  onAdd: function (map) {
    // console.log('add graticule');
    this._map = map;
    if (!this._container) this._initCanvas();
    map.getPanes().overlayPane.appendChild(this._container);
    map.on('viewreset', this._reset, this);
    map.on('move', this._reset, this);
    map.on('moveend', this._reset, this);
    map.getContainer().classList.add('grid');
    this._reset();
  },

  onRemove: function (map) {
    // console.log('remove graticule');
    map.getPanes().overlayPane.removeChild(this._container);
    map.off('viewreset', this._reset, this);
    map.off('move', this._reset, this);
    map.off('moveend', this._reset, this);
    map.getContainer().classList.remove('grid');
  },

  addTo: function (map) {
    map.addLayer(this);
    return this;
  },

  setOpacity: function (opacity) {
    this.options.opacity = opacity;
    this._updateOpacity();
    return this;
  },

  bringToFront: function () {
    if (this._canvas) {
      this._map._panes.overlayPane.appendChild(this._canvas);
    }
    return this;
  },

  bringToBack: function () {
    var pane = this._map._panes.overlayPane;
    if (this._canvas) {
      pane.insertBefore(this._canvas, pane.firstChild);
    }
    return this;
  },

  getAttribution: function () {
    return this.options.attribution;
  },

  _initCanvas: function () {
    this._container = L.DomUtil.create('div', 'leaflet-image-layer');
    this._canvas = L.DomUtil.create('canvas', '');

    if (this._map.options.zoomAnimation && L.Browser.any3d) {
      L.DomUtil.addClass(this._canvas, 'leaflet-zoom-animated');
    } else {
      L.DomUtil.addClass(this._canvas, 'leaflet-zoom-hide');
    }

    this._updateOpacity();

    this._container.appendChild(this._canvas);

    L.extend(this._canvas, {
      onselectstart: L.Util.falseFn,
      onmousemove: L.Util.falseFn,
      onload: L.bind(this._onCanvasLoad, this)
    });
  },

  _reset: function () {
    var container = this._container;
    var canvas = this._canvas;
    var size = this._map.getSize();
    var lt = this._map.containerPointToLayerPoint([0, 0]);

    L.DomUtil.setPosition(container, lt);

    container.style.width = size.x + 'px';
    container.style.height = size.y + 'px';

    canvas.width = size.x;
    canvas.height = size.y;
    canvas.style.width = size.x + 'px';
    canvas.style.height = size.y + 'px';

    this.__calcInterval();

    this.__draw(true);
  },

  _onCanvasLoad: function () {
    this.fire('load');
  },

  _updateOpacity: function () {
    L.DomUtil.setOpacity(this._canvas, this.options.opacity);
  },

  __format_lat: function (lat) {
    return this.options.latFormatTickLabel(lat);
  },

  __format_lng: function (lng) {
    return this.options.lngFormatTickLabel(lng);
  },

  __calcInterval: function () {
    this._currLngInterval = 0;
    this._currLatInterval = 0;
    const zoom = this._map.getZoom();
    const latScale = 1 / Math.cos(this._map.getCenter().lat * Math.PI / 180);
    this.options.intervals.forEach(i => {
      if (i.start <= zoom) {
        this._currLngInterval = i.interval;
      }
      if (i.start <= zoom + Math.log2(latScale) + 0.3) {
        this._currLatInterval = i.interval;
      }
    });
  },

  __draw: function (label) {
    const canvas = this._canvas;
    const map = this._map;
    if (!L.Browser.canvas || !map) return;
    this.__calcInterval();
    const latInterval = this._currLatInterval, lngInterval = this._currLngInterval;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = this.options.weight;
    ctx.strokeStyle = this.options.color;
    ctx.fillStyle = this.options.fontColor;

    const textShift = (this.options.borders || 0) + 2;

    const txtHeight = this.options.fontSize;
    ctx.font = `${this.options.fontSize}px ${this.options.fontFamily}`;

    const width = canvas.width;
    const height = canvas.height;
    // console.log('width', width, 'height', height);

    const north_west = map.containerPointToLatLng(L.point(0, 0));
    const south_east = map.containerPointToLatLng(L.point(width, height));
    // console.log('north_west', north_west, 'south_east', south_east);

    const north = north_west.lat;
    const west = north_west.lng;
    const south = south_east.lat;
    const east = south_east.lng;

    // console.log('north', north, 'west', west, 'south', south, 'east', east);

    function lat_line(latitude) {
      const y = map.latLngToContainerPoint(L.latLng(latitude, 0)).y;
      const o = (ctx.lineWidth / 2) % 1;
      ctx.beginPath();
      ctx.moveTo(-1, y + o);
      ctx.lineTo(width + 1, y + o);
      ctx.stroke();
      if (this.options.showLabel) {
        const label = this.__format_lat(latitude);
        const txtWidth = ctx.measureText(label).width;
        const yt = y + (txtHeight / 2) - 2;
        const w = ctx.lineWidth, s = ctx.strokeStyle;
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'white';
        ctx.strokeText(label, 0 + textShift, yt);
        ctx.strokeText(label, width - txtWidth - textShift, yt);
        ctx.lineWidth = w;
        ctx.strokeStyle = s;
        ctx.fillText(label, 0 + textShift, yt);
        ctx.fillText(label, width - txtWidth - textShift, yt);
      }
    }

    lat_line = lat_line.bind(this);

    if (latInterval > 0) {
      const l0 = Math.floor(south / latInterval) * latInterval;
      for (let i = 0, l = l0; l < north; i++) {
        lat_line(l = l0 + i * latInterval);
      }
    }

    function lon_line(longitude) {
      const x = map.latLngToContainerPoint(L.latLng(0, longitude)).x;
      const o = (ctx.lineWidth / 2) % 1;
      ctx.beginPath();
      ctx.moveTo(x + o, -1);
      ctx.lineTo(x + o, height + 1);
      ctx.stroke();
      if (this.options.showLabel) {
        const label = this.__format_lng(longitude);
        const txtWidth = ctx.measureText(label).width;
        const w = ctx.lineWidth;
        const s = ctx.strokeStyle;
        ctx.lineWidth = 3;
        ctx.strokeStyle = 'white';
        ctx.strokeText(label, x - (txtWidth / 2), txtHeight - 1 + textShift);
        ctx.strokeText(label, x - (txtWidth / 2), height - 1 - textShift);
        ctx.lineWidth = w;
        ctx.strokeStyle = s;
        ctx.fillText(label, x - (txtWidth / 2), txtHeight - 1 + textShift);
        ctx.fillText(label, x - (txtWidth / 2), height - 1 - textShift);
      }
    }

    lon_line = lon_line.bind(this);

    if (lngInterval > 0) {
      const l0 = Math.floor(west / lngInterval) * lngInterval;
      for (let i = 0, l = l0; l < east; i++) {
        lon_line(l = l0 + i * lngInterval);
      }
    }

    function border(inset = 0, weight = 1, corners = false) {
      ctx.lineWidth = weight;
      ctx.beginPath();
      const o = (ctx.lineWidth / 2) % 1;
      ctx.rect(inset + o, inset + o, width - 2 * inset - o, height - 2 * inset - o);
      ctx.stroke();
      if (!corners) return;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(inset, inset);
      ctx.moveTo(width, 0);
      ctx.lineTo(width - inset, inset);
      ctx.moveTo(width, height);
      ctx.lineTo(width - inset, height - inset);
      ctx.moveTo(0, height);
      ctx.lineTo(inset, height - inset);
      ctx.stroke();
    }

    function zebras(border, bwidth = 12) {
      const lat = border == 'W' || border == 'E';
      const opposite = border == 'E' || border == 'S';
      if (lat) var lmin = south, lmax = north, size = height;
      else var lmin = west, lmax = east, size = width;
      const ppm = size / (lmax - lmin) / 60; // px per minute
      const interval = lat ? latInterval : lngInterval;
      const minutes = interval < 1;
      // console.log('zebras', border, lmin, lmax, size, ppm, interval, minutes);
      const step = minutes ? 60 : 1;
      const l0 = minutes ? Math.floor(lmin * step) / step : Math.floor(lmin);
      const n = Math.floor(lmin * step) % 2 == 0 ? 0 : 1;

      // minute zebra bars
      ctx.lineWidth = bwidth / 6;
      ctx.beginPath();
      // ctx.moveTo(...p);
      var o = (opposite ? -1 : +1) * ((ctx.lineWidth / 2) % 1);
      const z = opposite ? (lat ? width : height) - bwidth / 4 - o : bwidth / 4 + o;
      for (let i = 0, l = l0; l < lmax; i++) {
        l = l0 + i / step;
        const c = map.latLngToContainerPoint(lat ? [l, 0] : [0, l]);
        const x = Math.min(Math.max(lat ? c.y : c.x, bwidth), (lat ? height : width) - bwidth);
        const p = lat ? [z, x] : [x, z];
        if (i % 2 == n) ctx.moveTo(...p);
        else ctx.lineTo(...p);
      }
      ctx.stroke();

      // minute divisions
      function divisions(start, interval) {
        ctx.lineWidth = 1;
        o = ((ctx.lineWidth / 2) % 1);
        ctx.beginPath();
        for (let i = 0, l = l0; l < lmax; i++) {
          l = l0 + i / interval;
          const c = map.latLngToContainerPoint(lat ? [l, 0] : [0, l]);
          const x = (lat ? c.y : c.x) + o;
          if (x < bwidth || x > (lat ? height : width) - bwidth) continue;
          const a = opposite ? (lat ? width : height) - start : start;
          const p0 = lat ? [a, x] : [x, a];
          ctx.moveTo(...p0);
          const b = opposite ? (lat ? width : height) - bwidth : bwidth;
          const p1 = lat ? [b, x] : [x, b];
          ctx.lineTo(...p1);
        }
        ctx.stroke();
      }

      divisions(0, ppm > 100 ? 120 : minutes ? 60 : 2);
      divisions(bwidth / 2, ppm > 100 ? 600 : ppm > 30 ? 300 : minutes ? 120 : 6);
    }

    if (!this.options.borders) return;
    const border_width = this.options.borders;
    ctx.strokeStyle = 'white';
    border(border_width / 2, border_width);
    ctx.strokeStyle = this.options.color;
    border(0);
    border(border_width / 2);
    border(border_width, 1, true);
    zebras('W', border_width);
    zebras('N', border_width);
    zebras('E', border_width);
    zebras('S', border_width);
  }

});

L.latlngGraticule = function (options) {
  return new L.LatLngGraticule(options);
};

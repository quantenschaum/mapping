import L from 'leaflet';
import {OpenLocationCode} from 'open-location-code';
import './boating.less';
import {degmin} from "./graticule";

const isDevMode = process.env.NODE_ENV === 'development';

function cosDeg(deg) {
  return Math.cos(deg * Math.PI / 180);
}

function sinDeg(deg) {
  return Math.sin(deg * Math.PI / 180);
}

function atan2Deg(x, y) {
  return ((Math.atan2(x, y) * 180 / Math.PI) + 360) % 360;
}

L.Control.Boating = L.Control.extend({

  options: {
    position: 'topleft',
    legendPosition: 'bottomleft',
    smoothing: 0.5,
  },

  onAdd: function (map) {
    const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
    const link = L.DomUtil.create('a', 'leaflet-bar-part leaflet-bar-part-single', container);
    link.title = 'track position';
    this.icon = L.DomUtil.create('span', 'leaflet-control-boating-arrow', link);

    L.DomEvent.disableClickPropagation(container);

    L.DomEvent.on(link, 'click', this.onClick, this);

    this.legend = L.control({position: this.options.legendPosition});
    this.legend.onAdd = function (map) {
      this.container = L.DomUtil.create('div', 'leaflet-control leaflet-bar leaflet-control-boating-legend');
      return this.container;
    }

    this.circle = L.circle([0, 0], {
      stroke: false,
    });

    this.line = L.polyline([[0, 0], [0, 0]], {
      color: 'purple',
      weight: 2,
      dashArray: [6, 6],
    });

    this.boat = L.marker([0, 0]);

    this.olc = new OpenLocationCode();

    return container;
  },

  isRequesting: function () {
    return this.icon.classList.contains('requesting');
  },

  isLocating: function () {
    return this.icon.classList.contains('locating');
  },

  isFollowing: function () {
    return this.icon.classList.contains('following');
  },

  onClick: function () {
    if (this.isFollowing() || this.isRequesting()) {
      this.stop();
    } else if (this.isLocating()) {
      this._map.panTo(this.lastPosition.latlng, {animate: true});
      this.follow();
    } else if (!this.isRequesting()) {
      this.request();
    }
  },

  onDragStart: function () {
    if (this.isFollowing()) {
      this.unfollow();
    }
  },

  request: function () {
    this._map.on('moveend', this.onMoveEnd, this);
    this._map.on('dragstart', this.onDragStart, this);
    this._map.on('locationfound', this.onLocationFound, this);
    this._map.on('locationerror', this.onLocationError, this);
    this._map.locate({watch: true, enableHighAccuracy: true});
    this.icon.classList.remove('following');
    this.icon.classList.remove('locating');
    this.icon.classList.add('requesting');
  },

  follow: function () {
    this._map.options.scrollWheelZoom = 'center';
    this._map.options.doubleClickZoom = 'center';
    this.icon.classList.remove('requesting');
    this.icon.classList.remove('locating');
    this.icon.classList.add('following');
    this._map.getContainer().classList.add('boating');
  },

  unfollow: function () {
    this._map.options.scrollWheelZoom = true;
    this._map.options.doubleClickZoom = true;
    this.icon.classList.remove('requesting');
    this.icon.classList.remove('following');
    this.icon.classList.add('locating');
  },

  stop: function () {
    this._map.stopLocate();
    this._map.off('moveend', this.onMoveEnd, this);
    this._map.off('dragstart', this.onDragStart, this);
    this._map.off('locationfound', this.onLocationFound, this);
    this._map.off('locationerror', this.onLocationError, this);
    this._map.options.scrollWheelZoom = true;
    this._map.options.doubleClickZoom = true;
    this.icon.classList.remove('requesting');
    this.icon.classList.remove('following');
    this.icon.classList.remove('locating');
    this._map.removeControl(this.legend);
    this._map.removeLayer(this.circle);
    this._map.removeLayer(this.line);
    this._map.removeLayer(this.boat);
    this._map.getContainer().classList.remove('boating');
  },

  onLocationFound: function (e) {
    e.speedVector = this.smoothSpeed(e)
    if (this.isRequesting()) {
      this._map.addControl(this.legend);
      this._map.addLayer(this.circle);
      this._map.addLayer(this.line);
      this._map.addLayer(this.boat);
      this.follow();
    }
    if (this.isFollowing()) {
      this._map.panTo(e.latlng, {animate: true});
    }
    this.updateLegend(e);
    this.updateCircle(e);
    this.updateLine(e);
    this.updateBoat(e);
    this.lastPosition = e;
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.stop(), 60_000);
  },

  onLocationError: function (e) {
    console.error(e)
    if (e.code === 1) {
      alert('geolocation error: ' + e);
      this.stop();
    }
  },

  updateCircle: function (e) {
    this.circle.setLatLng(e.latlng);
    this.circle.setRadius(e.accuracy);
  },

  updateBoat: function (e) {
    const heading = e.speedVector.heading || e.heading || NaN;
    let svg;
    if (isNaN(heading)) {
      svg = '<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><path style="fill:#3a65ff;stroke-width:0;stroke-linecap:round;stroke-linejoin:bevel;paint-order:stroke fill markers" d="M 253.33441,95.638684 A 160.38347,160.38347 0 0 1 416.34461,252.46992 160.38347,160.38347 0 0 1 260.39448,416.32325 160.38347,160.38347 0 0 1 95.702768,261.25874 160.38347,160.38347 0 0 1 249.87715,95.733448"/></svg>';
    } else {
      svg = `<svg transform="rotate(${heading})" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><path d="M 128 512 C 128 512 128 128 256 0 C 384 128 384 512 384 512 Z" fill="#3388ff"/></svg>`;
    }
    this.boat.setLatLng(e.latlng);
    this.boat.setIcon(
      L.divIcon({
        iconAnchor: [12.5, 12.5],
        iconSize: [25, 25],
        className: 'boat',
        html: svg,
      }));
  },

  updateLine: function (e) {
    const speed = e.speedVector.speed;
    const heading = e.speedVector.heading;
    if (isNaN(speed) || isNaN(heading)) {
      this.line.setLatLngs([[0, 0], [0, 0]]);
      return;
    }
    const length = speed * 3600 / 1852 / 60 / 6; // distance covered in 10 minutes
    const p0 = e.latlng;
    const p1 = L.latLng(
      p0.lat + (length * cosDeg(heading)),
      p0.lng + (length * sinDeg(heading) / cosDeg(p0.lat)),
    );
    this.line.setLatLngs([p0, p1]);
  },

  updateLegend: function (e) {
    const lat = degmin(e.latlng.lat, 2, true, true);
    const lng = degmin(e.latlng.lng, 2, false, true);
    let html = '';
    let heading = e.speedVector.heading || e.heading || NaN;
    if (!isNaN(heading)) html += `<div class="heading">${heading.toFixed(0).padStart(3, '0')}&deg;</div>`;
    let speed = (e.speedVector.speed || e.speed || NaN) * 3600 / 1852;
    if (!isNaN(speed)) html += `<div class="speed">${speed.toFixed(1)}&ThinSpace;kn</div>`;
    html += `<div class="position">${lat}<br/>${lng}<br/>${this.olc.encode(e.latlng.lat, e.latlng.lng)}</div>`;
    html += `<div class="line-legend">10&ThinSpace;min</div>`;
    this.legend.container.innerHTML = html;
  },

  smoothSpeed: (function () {
    let velocity = [NaN, NaN];
    return function (e) {
      if (isDevMode) {
        const t = this;
        const ee = {
          ...e,
          speed: 1852 / 3600 * (5 + Math.random() * 1),
          heading: 45 + Math.random() * 15,
        };
        setTimeout(() => t.onLocationFound(ee), 1000);
      }
      const v = [
        (e.speed) * cosDeg(e.heading),
        (e.speed) * sinDeg(e.heading),
      ];
      if (isNaN(velocity[0]) || isNaN(velocity[1])) velocity = v;
      const a = Math.max(0, Math.min(1 - this.options.smoothing, 1));
      velocity = [
        velocity[0] += a * (v[0] - velocity[0]),
        velocity[1] += a * (v[1] - velocity[1]),
      ];
      console.log(e, v, velocity);
      return {
        speed: Math.sqrt(Math.pow(velocity[0], 2) + Math.pow(velocity[1], 2)),
        heading: atan2Deg(velocity[1], velocity[0]),
      }
    };
  })(),
})

L.control.boating = function (options) {
  return new L.Control.Boating(options);
}

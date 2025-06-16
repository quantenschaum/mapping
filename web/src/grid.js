import L from 'leaflet';
import 'leaflet-graticule';

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

export function grid() {

  return L.latlngGraticule({
    showLabel: true,
    color: '#222',
    opacityControl: false,
    zoomInterval: [
      {start: 2, end: 4, interval: 30},
      {start: 5, end: 5, interval: 20},
      {start: 6, end: 6, interval: 10},
      {start: 7, end: 7, interval: 5},
      {start: 8, end: 8, interval: 2},
      {start: 9, end: 9, interval: 1},
      {start: 10, end: 10, interval: 30 / 60},
      {start: 11, end: 11, interval: 15 / 60},
      {start: 12, end: 12, interval: 10 / 60},
      {start: 13, end: 13, interval: 5 / 60},
      {start: 14, end: 14, interval: 2 / 60},
      {start: 15, end: 15, interval: 1 / 60},
      {start: 16, end: 16, interval: 1 / 60 / 2},
      {start: 17, end: 17, interval: 1 / 60 / 5},
      {start: 18, end: 18, interval: 1 / 60 / 10},
    ],
    latFormatTickLabel: v => degmin(v, 2, true),
    lngFormatTickLabel: v => degmin(v, 2, false),
  });
}

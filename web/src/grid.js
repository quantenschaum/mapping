import L from 'leaflet';
import './graticule';

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
    opacityControl: false,
  });
}

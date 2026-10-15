import L from "leaflet";
import { logger } from "./utils";
import { degmin } from "./graticule";
const isDevMode = import.meta.env.DEV;
const log = logger("KF", "red");
const params = new URLSearchParams(window.location.search);
const COLOR = "red";
// const COLOR = "#3a65ff";

// ---------- small linear algebra helpers (plain arrays) ----------
const isMat = (a) => Array.isArray(a[0]);
const zeros = (r, c) => Array.from({ length: r }, () => new Array(c).fill(0));
const eye = (n) => zeros(n, n).map((row, i) => ((row[i] = 1), row));
const diag = (v) =>
  zeros(v.length, v.length).map((row, i) => ((row[i] = v[i]), row));
const transpose = (A) => A[0].map((_, j) => A.map((row) => row[j]));
const copy = (a) => (isMat(a) ? a.map((r) => r.slice()) : a.slice());
const norm = (v) => Math.sqrt(v.reduce((s, a) => s + a * a, 0));
const radians = (deg) => (deg * Math.PI) / 180;
const degrees = (rad) => (rad * 180) / Math.PI;
const topi = (a) => a - 2 * Math.PI * Math.round(a / (2 * Math.PI)); // wrap angle to [-pi, pi]
const to360 = (d) => (d + 360) % 360;
const nm = 1 / 1852; // m -> nm
const kn = 3600 / 1852; // m/s -> kn
const kmh = 3600 / 1000; // m/s -> km/h

/** M[idx[a]][idx[b]] += S[a][b]  (equivalent of M[np.ix_(idx, idx)] += S) */
function addBlock(M, idx, S) {
  for (let a = 0; a < idx.length; a++)
    for (let b = 0; b < idx.length; b++) M[idx[a]][idx[b]] += S[a][b];
}

// elementwise add/sub for vectors or matrices
const add = (a, b) =>
  isMat(a)
    ? a.map((r, i) => r.map((v, j) => v + b[i][j]))
    : a.map((v, i) => v + b[i]);
const sub = (a, b) =>
  isMat(a)
    ? a.map((r, i) => r.map((v, j) => v - b[i][j]))
    : a.map((v, i) => v - b[i]);

/** Equivalent of numpy's @ for 1D/2D arrays:
 *  vec@vec -> scalar, mat@vec -> vec, vec@mat -> vec, mat@mat -> mat */
function dot(A, B) {
  const aM = isMat(A),
    bM = isMat(B);
  if (!aM && !bM) return A.reduce((s, v, i) => s + v * B[i], 0);
  if (aM && !bM)
    return A.map((row) => row.reduce((s, v, k) => s + v * B[k], 0));
  if (!aM && bM)
    return B[0].map((_, j) => A.reduce((s, v, k) => s + v * B[k][j], 0));
  const Bt = transpose(B);
  return A.map((row) =>
    Bt.map((col) => row.reduce((s, v, k) => s + v * col[k], 0)),
  );
}

/** Matrix inverse via Gauss-Jordan elimination with partial pivoting */
function inv(M) {
  const n = M.length;
  const A = M.map((row, i) => [...row, ...eye(n)[i]]); // augmented [M | I]
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++)
      if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    if (Math.abs(A[p][c]) < 1e-14) throw new Error("Matrix is singular");
    [A[c], A[p]] = [A[p], A[c]];
    const piv = A[c][c];
    for (let j = 0; j < 2 * n; j++) A[c][j] /= piv;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const f = A[r][c];
      if (f !== 0) for (let j = 0; j < 2 * n; j++) A[r][j] -= f * A[c][j];
    }
  }
  return A.map((row) => row.slice(n));
}

/** Cholesky decomposition: returns lower-triangular L with L Lᵀ = A */
function cholesky(A) {
  const n = A.length;
  const L = zeros(n, n);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let s = A[i][j];
      for (let k = 0; k < j; k++) s -= L[i][k] * L[j][k];
      if (i === j) {
        if (s <= 0) throw new Error("Matrix is not positive definite");
        L[i][j] = Math.sqrt(s);
      } else {
        L[i][j] = s / L[j][j];
      }
    }
  }
  return L;
}

/**
 * Coordinates of a covariance ellipse.
 * @param {number[]} center [cx, cy]
 * @param {number[][]} cova 2x2 covariance matrix
 * @param {number} confidence e.g. 0.5, 0.95
 * @param {number} npoints number of points on the ellipse
 * @returns {number[][]} [xs, ys] (same layout as ellipse.T in numpy)
 */
function covEllipse(center, cova, confidence = 0.5, npoints = 100) {
  const nsigma = Math.sqrt(-2 * Math.log(1 - confidence));
  const L = cholesky(cova);
  const xs = new Array(npoints);
  const ys = new Array(npoints);
  for (let i = 0; i < npoints; i++) {
    const t = (2 * Math.PI * i) / (npoints - 1); // like linspace(0, 2π, npoints), endpoint included
    const c = Math.cos(t),
      s = Math.sin(t);
    xs[i] = nsigma * (L[0][0] * c + L[0][1] * s) + center[0];
    ys[i] = nsigma * (L[1][0] * c + L[1][1] * s) + center[1];
  }
  return [xs, ys];
}

// ---------- Kalman filter ----------
class Kalman {
  /**
   * @param {number[]|number} x0 initial state vector, or state size (zeros)
   * @param {number} p0 initial variance on the covariance diagonal
   */
  constructor(x0, p0 = 0) {
    this.t = 0;
    if (typeof x0 === "number") x0 = new Array(x0).fill(0);
    this.x = x0.slice();
    this.P = diag(new Array(this.x.length).fill(p0));
    this.Q = null; // default process noise (optional)
  }

  get n() {
    return this.x.length;
  }

  /**
   * Prediction step
   * @param {number[][]|function(number[]):number[][]} F state transition Jacobian (matrix or function of x)
   * @param {number[][]|null} Q process noise matrix
   * @param {function(number[]):number[]|null} f nonlinear state transition; if null, F @ x is used
   */
  prediction(F, Q = null, f = null) {
    const Fx = typeof F === "function" ? F(this.x) : F;
    // log("F", F);
    // log("x", this.x);
    this.x = f ? f(this.x) : dot(Fx, this.x);
    // log("x", this.x);
    this.P = dot(dot(Fx, this.P), transpose(Fx));
    const q = Q ?? this.Q;
    if (q) this.P = add(this.P, q);
    // log("P", this.P);
  }

  /**
   * Correction step (EKF, or iterated EKF if H is a function)
   * @param {number[]} z measurement
   * @param {number[][]} R measurement covariance
   * @param {number[][]|function(number[]):number[][]} H Jacobian dh/dx (constant or function of x)
   * @param {function(number[]):number[]} h predicted measurement as function of state
   * @param {function(number[]):number[]|null} r residual wrapper (e.g. angle wrapping)
   * @param {number} maxIter max iterations for the iterated EKF
   */
  correction(z, R, H, h, r = null, maxIter = 10) {
    const x = this.x.slice(); // state used during iteration
    const hIsFn = typeof H === "function";
    if (!hIsFn) maxIter = 0;

    let K,
      Hx,
      P,
      n,
      e = Infinity;

    for (let i = 0; i <= maxIter; i++) {
      const hx = h(x);
      let rx = sub(z, hx); // residual
      if (r) rx = r(rx);
      Hx = hIsFn ? H(x) : H;
      n = Hx[0].length; // size for reduced update
      P = this.P.slice(0, n).map((row) => row.slice(0, n)); // reduced P
      const S = add(dot(dot(Hx, P), transpose(Hx)), R); // residual covariance
      K = dot(dot(P, transpose(Hx)), inv(S)); // Kalman gain
      if (i && (maxIter === i || e < 1)) break; // IEKF convergence
      const dx = sub(x.slice(0, n), this.x.slice(0, n));
      const d = sub(dot(K, add(rx, dot(Hx, dx))), dx); // state change delta
      e = dot(d, dot(inv(P), d)); // step size w.r.t. P
      for (let k = 0; k < n; k++) x[k] += d[k]; // state update
      if (!maxIter) break; // plain EKF: single pass
    }

    this.x = x; // commit state
    const U = sub(eye(n), dot(K, Hx)); // error transition matrix
    const Pn = add(dot(dot(U, P), transpose(U)), dot(dot(K, R), transpose(K)));
    for (let a = 0; a < n; a++)
      for (let b = 0; b < n; b++) this.P[a][b] = Pn[a][b]; // write back top-left block
  }
}
// ---------- Boat ----------
class Boat extends Kalman {
  /**
   * State: [x, y, vtw_x, vtw_y] (reduced) or [x, y, vtw_x, vtw_y, vcr_x, vcr_y]
   * x = east, y = north, angles are clockwise from north (atan2(x, y)).
   */
  constructor(qv = 0.01, qw) {
    super(qw ? 6 : 4);
    this.qv = qv;
    this.qw = qw;
    this.t = 0;
  }

  get pos() {
    return this.x.slice(0, 2);
  } // position
  get posSigma() {
    return [Math.sqrt(this.P[0][0]), Math.sqrt(this.P[1][1])];
  }
  get vtw() {
    return this.x.slice(2, 4);
  } // water velocity
  get hdt() {
    const [vx, vy] = this.vtw;
    return to360(degrees(Math.atan2(vx, vy)));
  } // heading
  get stw() {
    return norm(this.vtw);
  } // speed through water
  get vcr() {
    return this.n === 4 ? [0, 0] : this.x.slice(4, 6);
  } // current velocity
  get set() {
    const [vx, vy] = this.vcr;
    return to360(degrees(Math.atan2(vx, vy)));
  } // current direction
  get dft() {
    return norm(this.vcr);
  } // current speed (drift)
  get vog() {
    const a = this.vtw,
      b = this.vcr;
    return [a[0] + b[0], a[1] + b[1]];
  } // ground velocity
  get vogSigma() {
    const [vx, vy] = this.vog;
    const P = this.P;
    return Math.sqrt(
      (vx ** 2 * P[2][2] + 2 * vx * vy * P[2][3] + vy ** 2 * P[3][3]) /
        this.sog,
    );
  }
  get cog() {
    const [vx, vy] = this.vog;
    return to360(degrees(Math.atan2(vx, vy)));
  } // course over ground
  get cogSigma() {
    const [vx, vy] = this.vog;
    const v = this.sog;
    const g = [vy / v ** 2, -vx / v ** 2];
    const P = [
      [this.P[2][2], this.P[2][3]],
      [this.P[3][2], this.P[3][3]],
    ];
    return degrees(Math.sqrt(dot(g, dot(P, g))));
  }
  get sog() {
    return norm(this.vog);
  } // speed over ground
  get sogSigma() {
    const [vx, vy] = this.vog;
    const v = this.sog;
    const g = [vx / v, vy / v];
    const P = [
      [this.P[2][2], this.P[2][3]],
      [this.P[3][2], this.P[3][3]],
    ];
    return Math.sqrt(dot(g, dot(P, g)));
  }

  predict(dt, qv = 0, qw = 0) {
    this.t += dt;
    qv = qv || this.qv;
    qw = qw || this.qw;

    const n = this.n;
    const F = eye(n);
    F[0][2] = F[1][3] = dt;
    if (n > 4) F[0][4] = F[1][5] = dt;

    // continuous time white acceleration noise
    const Q2x2 = (q, dt) => {
      const s = q ** 2;
      return [
        [(s * dt ** 3) / 3, (s * dt ** 2) / 2],
        [(s * dt ** 2) / 2, s * dt],
      ];
    };

    const Q = zeros(n, n);
    const Qv = Q2x2(qv, dt);
    addBlock(Q, [0, 2], Qv);
    addBlock(Q, [1, 3], Qv);
    if (n > 4) {
      const Qw = Q2x2(qw, dt);
      addBlock(Q, [0, 4], Qw);
      addBlock(Q, [1, 5], Qw);
    }

    this.prediction(F, Q);
  }

  /**
   * Velocity measurement. course in degrees, speed in speed units.
   * Pass NaN for course or speed if only one is available.
   */
  measureVelocity(course, speed, courseError = 2, speedError = 0.2 / kn) {
    course = radians(course);
    courseError = radians(courseError);

    let r = null;
    let z, R, h, H;

    if (speed < 1e-6 || Number.isNaN(course)) {
      // speed only (course ignored when stationary)
      if (this.stw < 1e-6) return; // avoids zero division
      z = [speed];
      R = [[speedError ** 2]];
      h = (x) => [Math.hypot(x[2], x[3])];
      H = (x) => {
        const vx = x[2];
        const vy = x[3];
        const v = Math.hypot(vx, vy);
        return [[0, 0, vx / v, vy / v]];
      };
    } else if (Number.isNaN(speed)) {
      // course only
      if (this.stw < 1e-6) return;
      z = [course];
      R = [[courseError ** 2]];
      h = (x) => [Math.atan2(x[2], x[3])];
      H = (x) => {
        const vx = x[2];
        const vy = x[3];
        const v2 = vx * vx + vy * vy;
        if (v2 < 1e-12) return [[0, 0, 0, 0]];
        return [[0, 0, vy / v2, -vx / v2]];
      };
      r = (x) => [topi(x[0])];
    } else if (this.stw < 1e-6) {
      // cartesian velocity measurement, avoids zero division
      const c = course;
      const s = speed;
      const sc = Math.sin(c);
      const cc = Math.cos(c);
      z = [s * sc, s * cc];
      const J = [
        [s * cc, sc],
        [-s * sc, cc],
      ]; // polar -> cartesian Jacobian
      R = dot(
        dot(J, [
          [courseError ** 2, 0],
          [0, speedError ** 2],
        ]),
        transpose(J),
      );
      h = (x) => x.slice(2, 4);
      H = [
        [0, 0, 1, 0],
        [0, 0, 0, 1],
      ]; // constant -> plain EKF
    } else {
      // polar
      z = [course, speed];
      R = [
        [courseError ** 2, 0],
        [0, speedError ** 2],
      ];
      h = (x) => {
        const vx = x[2];
        const vy = x[3];
        return [Math.atan2(vx, vy), Math.hypot(vx, vy)];
      };
      H = (x) => {
        const vx = x[2];
        const vy = x[3];
        const v2 = vx * vx + vy * vy;
        const v = Math.sqrt(v2);
        return [
          [0, 0, vy / v2, -vx / v2],
          [0, 0, vx / v, vy / v],
        ];
      };
      r = (x) => [topi(x[0]), x[1]];
    }

    this.correction(z, R, H, h, r);
  }

  /** Position measurement (x east, y north), error = std dev */
  measurePosition(x, y, error = 5) {
    const z = [x, y];
    const R = [
      [error ** 2, 0],
      [0, error ** 2],
    ];
    const h = (s) => s.slice(0, 2);
    const H = zeros(2, this.n);
    H[0][0] = H[1][1] = 1;
    this.correction(z, R, H, h);
  }

  /** Bearing (degrees) to a known point (x, y) */
  measureBearing(x, y, bearing, error = 2) {
    bearing = radians(bearing);
    error = radians(error);

    const z = [bearing];
    const R = [[error ** 2]];

    const h = (s) => [Math.atan2(x - s[0], y - s[1])];
    const H = (s) => {
      const dx = x - s[0];
      const dy = y - s[1];
      const d2 = dx * dx + dy * dy;
      const M = zeros(1, this.n);
      M[0][0] = -dy / d2;
      M[0][1] = dx / d2;
      return M;
    };
    const r = (v) => [topi(v[0])];

    this.correction(z, R, H, h, r);
  }

  /** Range (meters) to a known point (x, y) */
  measureRange(x, y, range, rangeError = 5) {
    const z = [range];
    const R = [[rangeError ** 2]];

    const h = (s) => {
      const dx = x - s[0];
      const dy = y - s[1];
      return [Math.sqrt(dx * dx + dy * dy)];
    };

    const H = (s) => {
      const dx = x - s[0];
      const dy = y - s[1];
      const d2 = dx * dx + dy * dy;
      const d = Math.sqrt(d2);
      const M = zeros(1, this.n);
      M[0][0] = -dx / d;
      M[0][1] = -dy / d;
      return M;
    };

    this.correction(z, R, H, h);
  }
}

function button(label, title, callback, className = "") {
  const ButtonControl = L.Control.extend({
    options: { position: "topleft" },
    onAdd: function (map) {
      const div = L.DomUtil.create(
        "div",
        `leaflet-bar leaflet-control ${className}`.trim(),
      );
      const button = L.DomUtil.create("a");
      button.innerHTML = label;
      button.title = title;
      div.appendChild(button);

      const container = map.getContainer();
      button.addEventListener("click", () => callback(container, map));

      L.DomEvent.disableClickPropagation(div);
      return div;
    },
  });
  return new ButtonControl();
}

const R = 6378137;

function toWebmercator(lon, lat) {
  const x = R * radians(lon);
  const y = R * Math.log(Math.tan(Math.PI / 4 + radians(lat) / 2));
  return [x, y];
}

function toWGS84(x, y) {
  const lon = degrees(x / R);
  const lat = degrees(2 * Math.atan(Math.exp(y / R)) - Math.PI / 2);
  return [lon, lat];
}

export function init(map) {
  log("kalman");

  map.onFix = (lon, lat) => log("fix", lon, lat);
  map.onBrg = (lon, lat, brg, dst) => log("brg", lon, lat, brg, dst);
  map.onDst = (lon, lat, dst) => log("dst", lon, lat, dst);
  map.onLoc = (e) => log("loc", e.heading, e.speed, e.latlng, e);

  let boat;
  let toGrid;
  let toLonLat;
  let x0, y0, s0, t0;
  let loop;

  function startFilter(lon, lat) {
    if (!boat) {
      button("🧭", "change course and speed", (c) => {
        askCourseSpeed(true);
      }).addTo(map);
      button("🛑", "stop filter", (c) => {
        stopFilter();
      }).addTo(map);
    }

    const qv = params.get("qv") || 0.02;
    const qw = params.get("qw");
    boat = new Boat(qv, qw);
    t0 = Date.now() / 1000;
    [x0, y0] = toWebmercator(lon, lat);
    s0 = Math.cos(radians(lat)); //local length scale factor
    toGrid = (lon, lat) => {
      const [x, y] = toWebmercator(lon, lat);
      return [(x - x0) * s0, (y - y0) * s0];
    };
    toLonLat = (x, y) => toWGS84(x / s0 + x0, y / s0 + y0);
    map.onFix = (lon, lat) => {
      updateTrack(1);
      const [x, y] = toGrid(lon, lat);
      boat.measurePosition(x, y);
      updateTrack(2);
      updateMarker();
    };
    map.onBrg = (lon, lat, brg, dst) => {
      updateTrack(1);
      const [x, y] = toGrid(lon, lat);
      if (brg != null) boat.measureBearing(x, y, brg);
      if (dst != null) boat.measureRange(x, y, dst / nm);
      updateTrack(2);
      updateMarker();
    };
    const g = params.get("g");
    if (g == 1) {
      map.onLoc = (e) => {
        updateTrack(1);
        map.loc = e;
        if (e.speed == null) return;
        if (e.heading == null) boat.measureVelocity(0, 0);
        else boat.measureVelocity(e.heading, e.speed);
        updateMarker();
      };
    }
    if (g == 2) {
      map.onLoc = (e) => {
        updateTrack(1);
        map.loc = e;
        if (e.latlng == null) return;
        log(e);
        const [x, y] = toGrid(e.latlng.lng, e.latlng.lat);
        boat.measurePosition(x, y, e.accuracy ?? 10);
        updateMarker();
      };
    }
    if (loop) clearInterval(loop);
    loop = setInterval(predict, 1000);
  }

  function stopFilter() {
    if (loop) clearInterval(loop);
    map.onFix = startFilter;
  }

  stopFilter();

  const speedup = params.get("s") || 1;
  const p = (params.get("p") || "50")
    .split(",")
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => Number.isFinite(n));
  log("p", p);

  function predict() {
    const now = Date.now() / 1000;
    boat.predict(speedup * (now - t0));
    t0 = now;
    updateMarker();
    updateSpeedVector();
    updateTrack();
    p.forEach(updateEllipse);
    // log("t", boat.t, "x", boat.x);
  }

  const cogVector = L.polyline([], {
    color: "blue",
    weight: 2,
    opacity: 0.9,
    pane: "overlayPane",
  }).addTo(map);
  const hdtVector = L.polyline([], {
    color: "blue",
    weight: 2,
    opacity: 0.9,
    dashArray: "6, 6",
    pane: "overlayPane",
  }).addTo(map);
  const tideVector = L.polyline([], {
    color: "green",
    weight: 2,
    opacity: 0.9,
    pane: "overlayPane",
  }).addTo(map);

  function updateSpeedVector(time = 360) {
    const [x, y] = boat.pos;
    const [lon1, lat1] = toLonLat(x, y);
    {
      const [vx, vy] = boat.vog;
      const [lon2, lat2] = toLonLat(x + vx * time, y + vy * time);
      cogVector.setLatLngs([
        [lat1, lon1],
        [lat2, lon2],
      ]);
    }
    if (boat.n > 4) {
      const [vx, vy] = boat.vtw;
      const [lon2, lat2] = toLonLat(x + vx * time, y + vy * time);
      hdtVector.setLatLngs([
        [lat1, lon1],
        [lat2, lon2],
      ]);
    }
    if (boat.n > 4) {
      const [vx, vy] = boat.vcr;
      const [lon2, lat2] = toLonLat(x + vx * time, y + vy * time);
      tideVector.setLatLngs([
        [lat1, lon1],
        [lat2, lon2],
      ]);
    }
  }

  const marker = L.circleMarker([0, 0], {
    radius: 6,
    color: COLOR,
    fillColor: COLOR,
    fillOpacity: 1,
    weight: 2,
    pane: "markerPane",
  }).addTo(map);

  function updateMarker() {
    const [x, y] = boat.pos;
    const [lon, lat] = toLonLat(x, y);
    marker.setLatLng([lat, lon]);
    marker.bringToFront();
    marker.bindPopup(
      `<span style="font-family: monospace;">` +
        `${degmin(lat, 3, true, true)} &pm; ${(boat.posSigma[0] * nm).toFixed(2)}&ThinSpace;nm<br>` +
        `${degmin(lon, 3, false, true)} &pm; ${(boat.posSigma[1] * nm).toFixed(2)}&ThinSpace;nm<br>` +
        `COG ${boat.cog.toFixed(0).padStart(3, "0")}&deg; &pm; ${boat.cogSigma.toFixed(1)}&deg;<br>` +
        `SOG ${(boat.sog * kn).toFixed(1)}&ThinSpace;kn &pm; ${(boat.sogSigma * kn).toFixed(1)}&ThinSpace;kn` +
        (boat.n > 4
          ? `<br>HDT ${boat.hdt.toFixed(0).padStart(3, "0")}&deg;<br>` +
            `STW ${(boat.stw * kn).toFixed(1)}&ThinSpace;kn<br>` +
            `SET ${boat.set.toFixed(0).padStart(3, "0")}&deg;<br>` +
            `DFT ${(boat.dft * kn).toFixed(1)}&ThinSpace;kn`
          : "") +
        `</span>`,
      // `<br>${map?.loc?.latlng.lat}`+
      // `<br>${map?.loc?.latlng.lng}` +
      // `<br>${map?.loc?.heading}` +
      // `<br>${map?.loc?.speed * kn}kn` +
      // `<br>${map?.loc?.speed * kmh}km/h`,
    );
  }

  const ellipses = new Map();

  function updateEllipse(p = 50) {
    let ellipse = ellipses.get(p);
    if (!ellipse) {
      ellipse = L.polygon([], {
        color: COLOR,
        weight: 0,
        opacity: 0.8,
        fill: true,
        fillColor: COLOR,
        fillOpacity: 0.1,
      }).addTo(map);
      ellipses.set(p, ellipse);
    }
    const Pxy = [
      [boat.P[0][0], boat.P[0][1]],
      [boat.P[1][0], boat.P[1][1]],
    ];
    {
      const [xs, ys] = covEllipse(boat.pos, Pxy, p / 100, 128);
      const latlngs = xs.map((x, i) => {
        const [lon, lat] = toLonLat(x, ys[i]);
        return [lat, lon];
      });
      ellipse.setLatLngs(latlngs);
    }
  }

  const track = L.polyline([], {
    color: COLOR,
    weight: 2,
    opacity: 0.8,
  }).addTo(map);

  const maxPoints = 1000;
  function updateTrack(n = 0) {
    const [x, y] = boat.pos;
    const [lon, lat] = toLonLat(x, y);
    const ll = track.getLatLngs();
    if (ll.length > 1 && n <= 0) ll.pop();
    if (n <= 0) n = 1;
    for (let i = 0; i < n; i++) ll.push([lat, lon]);
    if (maxPoints > 0 && ll.length > maxPoints) {
      ll.splice(0, ll.length - maxPoints); // trim from start
    }
    track.setLatLngs(ll);
  }

  function askCourseSpeed(hardSet = false) {
    const value = window.prompt(
      "Enter course and speed like '123 5' for 123° and 5kn",
    );
    if (!value) return;
    const parts = value.trim().split(/\s+/);
    if (parts.length < 2) return;
    const course = parseFloat(parts[0]);
    const speed = parseFloat(parts[1]);
    if (!Number.isFinite(course) || !Number.isFinite(speed)) return;
    if (hardSet) {
      const c = radians(course);
      boat.x[2] = (speed / kn) * Math.sin(c);
      boat.x[3] = (speed / kn) * Math.cos(c);
    }
    updateTrack(1);
    boat.measureVelocity(course, speed / kn);
  }
}

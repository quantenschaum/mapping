import L from "leaflet";
import "leaflet-rotatedmarker";
import "./charttools.less";
import { degmin } from "../graticule";
import { deg, rad, to180, to360 } from "../utils";
import geomagnetism from "geomagnetism";
const icons = import.meta.glob("./charttools-*.svg", { eager: true });

const isDevMode = process.env.NODE_ENV === "development";
const isTouch = "ontouchstart" in window || navigator.maxTouchPoints > 0;
console.log("touch device", isTouch);

const magModel = geomagnetism.model(new Date());
console.log("magModel", magModel);
let DEC = 0;
function declination(pos) {
  if (pos.lat < 46.5 && pos.lat > 45.6 && pos.lng > -6.42 && pos.lng < -5.57)
    return -7;
  return magModel.point([pos.lat, pos.lng]).decl;
}

function icon(name, size = 32) {
  if (name == "a3" && size == 32) size = 64;
  return L.icon({
    iconUrl: icons[`./charttools-${name}.svg`].default,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, 0],
    tooltipAnchor: [0, -size / 2],
  });
}

function pos(e, digits = 3, pad = true) {
  const lat = degmin(e._latlng.lat, digits, 1, pad);
  const lng = degmin(e._latlng.lng, digits, 0, pad);
  return lat + " " + lng;
}

function dir(a, digits = 0, magnetic = false) {
  const p = digits ? 0 : 3;
  let mag = "";
  if (magnetic)
    mag = `(${to360(a - DEC)
      .toFixed(digits)
      .padStart(p, "0")}°M)`;
  return `${to360(a).toFixed(digits).padStart(p, "0")}°` + mag;
}

function dist(d, digits = 2) {
  return `${d.toFixed(digits)}M`;
}

function dir_dist(a, d, adigits = 0, magnetic = false, ddigits = 2) {
  return dir(a, adigits, magnetic) + "/" + dist(d, ddigits);
}

function bearingGC(a, b) {
  const [lat1, lat2] = [rad(a.lat), rad(b.lat)];
  const dLon = rad(b.lng - a.lng);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  const bearing = Math.atan2(y, x);
  return to360(deg(bearing));
}

// function distance0(a, b) {  return a.distanceTo(b) / 1852;}

function distanceGC(a, b) {
  const R = 6371e3;
  const φ1 = rad(a.lat);
  const φ2 = rad(b.lat);
  const Δφ = rad(b.lat - a.lat);
  const Δλ = rad(b.lng - a.lng);
  const sinΔφ = Math.sin(Δφ / 2);
  const sinΔλ = Math.sin(Δλ / 2);
  const a_val = sinΔφ * sinΔφ + Math.cos(φ1) * Math.cos(φ2) * sinΔλ * sinΔλ;
  const c = 2 * Math.atan2(Math.sqrt(a_val), Math.sqrt(1 - a_val));
  return (R * c) / 1852;
}

function ll2merc(latlng) {
  const originShift = (2 * Math.PI * 6378137) / 2.0;
  const x = (latlng.lng * originShift) / 180.0;
  let y =
    Math.log(Math.tan(((90 + latlng.lat) * Math.PI) / 360.0)) /
    (Math.PI / 180.0);
  y = (y * originShift) / 180.0;
  return { x, y };
}

function merc2ll(merc) {
  const originShift = (2 * Math.PI * 6378137) / 2.0;
  const lng = (merc.x / originShift) * 180.0;
  let lat = (merc.y / originShift) * 180.0;
  lat =
    (180 / Math.PI) *
    (2 * Math.atan(Math.exp((lat * Math.PI) / 180.0)) - Math.PI / 2);
  return L.latLng(lat, lng);
}

function bearingRL(a, b) {
  const p1 = ll2merc(a);
  const p2 = ll2merc(b);
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const angle = Math.atan2(dx, dy);
  return to360(deg(angle));
}

function distanceRL(a, b) {
  const p1 = ll2merc(a);
  const p2 = ll2merc(b);
  const f = Math.cos(rad((a.lat + b.lat) / 2));
  const dx = (p2.x - p1.x) * f;
  const dy = (p2.y - p1.y) * f;
  return Math.sqrt(dx * dx + dy * dy) / 1852;
}

function projectGC(start, bearing, distance) {
  const R = 6378137;
  const δ = (distance * 1852) / R;
  const θ = rad(bearing);
  const φ1 = rad(start.lat);
  const λ1 = rad(start.lng);
  const φ2 = Math.asin(
    Math.sin(φ1) * Math.cos(δ) + Math.cos(φ1) * Math.sin(δ) * Math.cos(θ),
  );
  const λ2 =
    λ1 +
    Math.atan2(
      Math.sin(θ) * Math.sin(δ) * Math.cos(φ1),
      Math.cos(δ) - Math.sin(φ1) * Math.sin(φ2),
    );
  return L.latLng(deg(φ2), deg(λ2));
}

function projectRL(start, bearing, distance) {
  const p0 = ll2merc(start);
  const angle = rad(bearing);
  const f = Math.cos(rad(start.lat));
  const dx = (distance / f) * 1852 * Math.sin(angle);
  const dy = (distance / f) * 1852 * Math.cos(angle);
  const p2 = {
    x: p0.x + dx,
    y: p0.y + dy,
  };
  return merc2ll(p2);
}

const bearing = bearingRL;
const distance = distanceRL;
const project = projectRL;
// const bearing = bearingGC;
// const distance = distanceGC;
// const project = projectGC;

function mix(a, b, f = 0.5) {
  // return L.latLng(a.lat * (1 - f) + b.lat * f, a.lng * (1 - f) + b.lng * f);
  const brg = bearing(a, b);
  const dst = distance(a, b);
  return project(a, brg, dst * f);
}

export const ChartTools = L.Control.extend({
  options: { position: "topleft" },
  onAdd: function (map) {
    const div = L.DomUtil.create("div", "charttools leaflet-bar");
    L.DomEvent.disableClickPropagation(div);

    map.on("move", () => (DEC = declination(map.getCenter())));

    const layer = L.featureGroup().addTo(map);

    function toggleVisibility() {
      if (map.hasLayer(layer)) layer.removeFrom(map);
      else layer.addTo(map);
    }

    function clear() {
      if (confirm("Clear all markers?")) layer.clearLayers();
    }

    function clickThrough(marker) {
      marker.on("click", (e) => {
        e = e.originalEvent;
        const r = marker.getElement().getBoundingClientRect();
        map.getContainer().dispatchEvent(
          new MouseEvent("click", {
            bubbles: true,
            cancelable: true,
            clientX: r.left + r.width / 2,
            clientY: r.top + r.height / 2,
          }),
        );
      });
    }

    const mapContainer = map.getContainer();
    function touch(mouseEvent, offset = [0, -64]) {
      return (touchEvent) => {
        touchEvent.preventDefault();
        const touch = touchEvent.changedTouches[0];
        if (!touch) return;
        // console.log(touchEvent);
        map.dragging.disable();
        mapContainer.dispatchEvent(
          new MouseEvent(mouseEvent, {
            bubbles: true,
            cancelable: true,
            clientX: touch.clientX + offset[0],
            clientY: touch.clientY + offset[1],
            screenX: touch.screenX + offset[0],
            screenY: touch.screenY + offset[1],
            originalEvent: touchEvent,
            shiftKey: touchEvent.shiftKey,
          }),
        );
      };
    }
    const [touchmove, touchend] = [touch("mousemove"), touch("click")];
    function touch2mouse(enable) {
      if (enable) {
        const opts = { passive: false };
        mapContainer.addEventListener("touchmove", touchmove, opts);
        mapContainer.addEventListener("touchend", touchend, opts);
      } else {
        mapContainer.removeEventListener("touchmove", touchmove);
        mapContainer.removeEventListener("touchend", touchend);
        map.dragging.enable();
      }
    }
    // map.dragging.disable();
    // map.on("mousedown", console.log);
    // map.on("mousemove", console.log);
    // map.on("mouseup", console.log);

    let mouseAction = null;
    let cancelAction = null;

    function onMouse(action, layer) {
      function cancel() {
        console.log("cancelled", layer);
        offMouse();
        if (layer) layer.remove();
      }
      mouseAction = action;
      cancelAction = cancel;
      touch2mouse(1);
      map.on("click", mouseAction);
      map.on("mousemove", mouseAction);
      map.on("contextmenu", cancelAction);
    }

    function offMouse(layer) {
      touch2mouse(0);
      map.off("click", mouseAction);
      map.off("mousemove", mouseAction);
      map.off("contextmenu", cancelAction);
      if (layer) layer.on("contextmenu", layer.remove);
      cancelAction = null;
    }

    function drawMarker(name) {
      let marker = L.marker([0, 0], { icon: icon(name) }).addTo(layer);
      let q = null;
      const f = 600;
      function draw(e) {
        const p = e.latlng;
        if (e.originalEvent.shiftKey) {
          p.lat = Math.round(p.lat * f) / f;
          p.lng = Math.round(p.lng * f) / f;
        }
        if (e.originalEvent.ctrlKey) {
          const m = marker.getLatLng();
          const brg = Math.abs(to180(bearing(q, p)));
          if (brg < 45 || brg > 135) p.lng = q.lng;
          else p.lat = q.lat;
        } else q = p;
        marker.setLatLng(p);
        marker.bindTooltip(pos, {
          direction: "top",
          permanent: true,
        });
        if (e.type == "click") {
          clickThrough(marker);
          marker.bindTooltip(pos, {
            direction: "top",
          });
          offMouse(marker);
        }
      }
      onMouse(draw, marker);
    }

    const LINE_OPTS = { color: "black", weight: 2, opacity: 1 };
    const LINE_OPT2 = { ...LINE_OPTS, color: "red" };
    const LINE_OPT3 = { ...LINE_OPTS, color: "green" };
    const LINE_OPT4 = { ...LINE_OPTS, color: "lightgray" };

    function drawCircle() {
      let circle = null;
      let center = null;
      const group = L.featureGroup().addTo(layer);
      let xmark = L.marker([0, 0], { icon: icon("x") }).addTo(group);
      function draw(e) {
        // console.log(e);
        if (circle == null) {
          xmark.setLatLng(e.latlng);
        }
        if (circle == null && e.type == "click") {
          center = e.latlng;
          circle = L.circle(center, {
            ...LINE_OPT3,
            radius: 0,
            fillColor: "none",
          }).addTo(group);
        } else if (circle != null) {
          let dst = distance(e.latlng, center);
          if (e.originalEvent.shiftKey) dst = Math.round(dst * 10) / 10;
          circle.setRadius(dst * 1852);
          circle.bindTooltip(dist(dst), {
            permanent: e.type == "mousemove",
          });
          if (e.type == "click") {
            xmark.bindTooltip(pos, { direction: "top" });
            circle.setStyle(LINE_OPTS);
            offMouse(group);
          }
        }
      }
      onMouse(draw, group);
    }

    function drawBearing(then, style = LINE_OPTS) {
      let line = null;
      let points = [];
      let marker = null;
      const group = L.featureGroup().addTo(layer);
      let xmark = L.marker([0, 0], { icon: icon("x") }).addTo(group);
      function draw(e) {
        // console.log(e);
        if (points.length == 0) {
          xmark.setLatLng(e.latlng);
        }
        if (points.length == 0 && e.type == "click") {
          points = [e.latlng, e.latlng];
          line = L.polyline(points, LINE_OPT2).addTo(group);
          marker = L.marker(e.latlng, { icon: icon("arr") }).addTo(group);
        } else if (points.length) {
          points[1] = e.latlng;
          let brg0 = bearing(...points);
          let dst = distance(...points);
          if (e.originalEvent.shiftKey) {
            brg0 = Math.round(brg0);
            // dst = Math.round(dst * 10) / 10;
            points[1] = project(points[0], brg0, dst);
          }
          const brg1 = to360(brg0 + 180);
          line.setLatLngs(points);
          marker.bindTooltip(dir(brg1, 1, 1), {
            permanent: true,
            direction: "top",
          });
          marker.setLatLng(mix(...points));
          marker.setRotationAngle(brg1);
          if (e.type == "click") {
            xmark.remove();
            marker.bindTooltip(dir(brg1), {
              direction: "top",
            });
            line.setStyle(style);
            offMouse(group);
            if (then) then(points);
          }
        }
      }
      onMouse(draw, group);
    }

    function twoStep(e) {
      return true;
      return !isTouch;
    }

    function drawBearingRange(sym, mrk, then, start, style = LINE_OPTS) {
      let line = null;
      let points = [];
      let symbol = null;
      let marker = null;
      let brg = null;
      const group = L.featureGroup().addTo(layer);
      let xmark = L.marker([0, 0], { icon: icon("x") }).addTo(group);
      const invert = sym.startsWith("-");
      if (invert) sym = sym.substring(1);
      function init(p) {
        points = [p, p];
        line = L.polyline(points, LINE_OPT2).addTo(group);
        symbol = L.marker(p, { icon: icon(sym) }).addTo(group);
        marker = mrk ? L.marker(p, { icon: icon(mrk) }).addTo(group) : null;
      }
      if (start) init(start);
      function draw(e) {
        // console.log(e);
        if (points.length == 0) {
          xmark.setLatLng(e.latlng);
        }
        if (points.length == 0 && e.type == "click") {
          init(e.latlng);
        } else if (points.length) {
          points[1] = e.latlng;
          if (brg != null)
            points[1] = project(points[0], brg, distance(...points));
          let brg0 = bearing(...points);
          let dst = distance(...points);
          if (e.originalEvent.shiftKey) {
            if (brg == null) brg0 = Math.round(brg0);
            else dst = Math.round(dst * 10) / 10;
            points[1] = project(points[0], brg0, dst);
          }
          const brg1 = to360(brg0 + 180);
          line.setLatLngs(points);
          const brg2 = invert ? brg1 : brg0;
          const tt =
            brg == null
              ? dir(brg2, 1, sym == "a1" || sym == "a2" || sym == "arr")
              : dist(dst, 2);
          marker.bindTooltip(tt, { permanent: true, direction: "top" });
          symbol.setLatLng(mix(...points));
          symbol.setRotationAngle(brg2);
          marker.setLatLng(points[1]);
          marker.setRotationAngle(Math.max(brg0, brg1) + 90);
          if (e.type == "click") {
            if (twoStep(e) && brg == null) {
              brg = brg0;
              line.setStyle(LINE_OPT3);
            } else {
              clickThrough(marker);
              if (mrk == "x") marker.remove();
              else marker.bindTooltip(pos, { direction: "top" });
              xmark.remove();
              line.setStyle(style);
              symbol.bindTooltip(dir_dist(brg2, dst, 0, sym == "a1"), {
                direction: "top",
              });
              offMouse(group);
              if (then) then(points);
            }
          }
        }
      }
      onMouse(draw, group);
      return group;
    }

    function line(a, b, sym, showDist) {
      let brg = bearing(a, b);
      let dst = distance(a, b);
      const group = L.featureGroup().addTo(layer);
      const line = L.polyline([a, b], LINE_OPTS).addTo(group);
      if (sym)
        L.marker(mix(a, b), { icon: icon(sym), rotationAngle: brg })
          .addTo(group)
          .bindTooltip(showDist ? dir_dist(brg, dst) : dir(brg), {
            direction: "top",
          });
      group.on("contextmenu", group.remove);
      return group;
    }

    function drawCourseToSteer(tpoints) {
      const gpoints = [tpoints[0], tpoints[1]];
      const wpoints = [tpoints[1], tpoints[1]];
      const group = L.featureGroup().addTo(layer);
      const ggroup = L.featureGroup().addTo(group);
      const wgroup = L.featureGroup().addTo(group);
      const gline = L.polyline(gpoints, LINE_OPT2).addTo(ggroup);
      const wline = L.polyline(wpoints, LINE_OPT4).addTo(wgroup);
      const gsymbol = L.marker(mix(...gpoints), { icon: icon("a2") }).addTo(
        ggroup,
      );
      const wsymbol = L.marker(mix(...wpoints), { icon: icon("a1") }).addTo(
        wgroup,
      );
      const marker = L.marker(gpoints[1], { icon: icon("x") }).addTo(ggroup);
      // const circle = L.circle(wpoints[1], {
      //   ...LINE_OPT3,
      //   radius: 0,
      //   fillColor: "none",
      // }).addTo(wgroup);
      let brg = null;
      function draw(e) {
        let { latlng } = e;
        gpoints[1] = wpoints[1] = latlng;
        if (brg != null) {
          gpoints[1] = wpoints[1] = project(
            gpoints[0],
            brg,
            distance(...gpoints),
          );
        }
        let cog = bearing(...gpoints);
        let sog = distance(...gpoints);
        if (e.originalEvent.shiftKey) {
          if (brg == null) cog = Math.round(cog);
          else sog = Math.round(sog * 10) / 10;
          gpoints[1] = wpoints[1] = project(gpoints[0], cog, sog);
        }
        gline.setLatLngs(gpoints);
        gsymbol.setLatLng(mix(...gpoints));
        gsymbol.setRotationAngle(cog);
        wline.setLatLngs(wpoints);
        const ctw = bearing(...wpoints);
        const stw = distance(...wpoints);
        wsymbol.setLatLng(mix(...wpoints));
        wsymbol.setRotationAngle(ctw);
        marker.setLatLng(gpoints[1]);
        // marker.setRotationAngle(cog);
        const tt = brg == null ? dir(cog, 1) : dist(stw);
        marker.bindTooltip(tt, { permanent: true, direction: "top" });
        // if (brg != null) circle.setRadius(stw * 1852);
        if (e.type == "click") {
          if (twoStep(e) && brg == null) {
            brg = cog;
            gline.setStyle(LINE_OPT4);
            wline.setStyle(LINE_OPT3);
          } else {
            offMouse();
            ggroup.on("contextmenu", ggroup.remove);
            wgroup.on("contextmenu", wgroup.remove);
            gline.setStyle(LINE_OPTS);
            wline.setStyle(LINE_OPTS);
            gsymbol.bindTooltip(dir_dist(cog, sog), {
              direction: "top",
            });
            wsymbol.bindTooltip(dir_dist(ctw, stw, 0, 1), {
              direction: "top",
            });
            clickThrough(marker);
            // marker.bindTooltip(pos, { direction: "top" });
            marker.remove();
            // circle.remove();
          }
        }
      }
      onMouse(draw, group);
    }

    function drawRunningBearing() {
      drawBearing(
        (p) => {
          drawBearingRange(
            "a2",
            "x",
            (q) => {
              const brg = bearing(...q);
              const dst = distance(...q);
              line(project(p[1], brg, dst), project(p[0], brg, dst), "arr");
            },
            mix(...p),
            { ...LINE_OPTS, color: "gray" },
          );
        },
        { ...LINE_OPTS, dashArray: [5, 5] },
      );
    }

    function drawEstimatedPosition() {
      drawBearingRange("a1", "plus", (p) => {
        drawBearingRange("a3", "ep", (q) => line(p[0], q[1], "a2", true), p[1]);
      });
    }

    function button(name, action) {
      const b = L.DomUtil.create("a", "button " + name.replaceAll(" ", "_"));
      b.innerHTML = "&nbsp;";
      b.title = name;
      if (action)
        b.addEventListener("click", (e) => {
          if (cancelAction) cancelAction();
          action();
        });
      return b;
    }

    const HIDE = "hide";

    const pb = L.DomUtil.create(
      "div",
      "buttons " + HIDE + (isDevMode ? "x" : ""),
    );
    div.appendChild(pb);
    pb.appendChild(
      button("charttools", () => {
        // toggleVisibility();
        if (pb.classList.contains(HIDE)) pb.classList.remove(HIDE);
        else pb.classList.add(HIDE);
      }),
    );
    pb.appendChild(button("erase", clear));
    pb.appendChild(button("waypoint", () => drawMarker("wp")));
    pb.appendChild(button("bearing", drawBearing));
    pb.appendChild(button("range", drawCircle));
    pb.appendChild(
      button("bearing and range", () => drawBearingRange("-arr", "fix")),
    );
    pb.appendChild(button("running bearing", drawRunningBearing));
    pb.appendChild(button("fix", () => drawMarker("fix")));
    pb.appendChild(
      button("dead reckoning", () => drawBearingRange("a1", "plus")),
    );
    pb.appendChild(button("estimated position", drawEstimatedPosition));
    pb.appendChild(
      button("course to steer", () =>
        drawBearingRange("a3", "x", drawCourseToSteer),
      ),
    );

    return div;
  },
});

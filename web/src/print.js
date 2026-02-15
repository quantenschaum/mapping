import L from "leaflet";
// import domtoimage from "dom-to-image";
import "./print.less";
import { ackee } from "./ackee";

export const PrintButton = L.Control.extend({
  options: { position: "topleft" },
  onAdd: function (map) {
    const div = L.DomUtil.create(
      "div",
      "printmode leaflet-bar leaflet-control",
    );
    L.DomEvent.disableClickPropagation(div);

    async function getImage() {
      const size = map.getSize();
      const body = document.body;
      body.classList.add("imagemode");
      const htmlToImage = await import("html-to-image");
      await htmlToImage
        .toPng(map.getContainer(), {
          height: size.y,
          width: size.x,
          pixelRatio: 1,
        })
        .then(function (dataUrl) {
          const link = L.DomUtil.create("a");
          link.download = `freenauticalchart-${map.getZoom()}-${map.getCenter().lat.toFixed(3)}-${map.getCenter().lng.toFixed(3)}.png`;
          link.href = dataUrl;
          link.click();
          ackee.action("4e923284-945c-45fd-97d6-4c0d351205ec", {
            key: "print_export",
            value: 1,
          });
        })
        .catch(console.error);
      body.classList.remove("imagemode");
    }

    const classes = [];

    function button(name, title, cls = "") {
      const clss = cls.split(" ").filter((c) => c);
      clss.forEach((c) => classes.push(c));
      const b = L.DomUtil.create("a", cls ? "format " + clss.at(-1) : "button");
      b.innerHTML = name;
      b.title = title;
      const body = document.body;
      const cont = map.getContainer();
      b.addEventListener("click", () => {
        if (!title.includes("reset")) {
          ackee.action("4e923284-945c-45fd-97d6-4c0d351205ec", {
            key: "print " + title,
            value: 1,
          });
        }
        const cl = cont.classList;
        const isSelected = clss.every((c) => cl.contains(c));
        if (!cls) {
          getImage();
        } else if (!isSelected) {
          body.classList.add("print");
          const formats = pb.querySelectorAll(".format");
          formats.forEach((f) => f.classList.remove("selected"));
          b.classList.add("selected");
          classes.forEach((c) => cl.remove(c));
          clss.forEach((c) => cl.add(c));
          map.invalidateSize();
          map.options.zoomDelta = 0.5;
          map.options.zoomSnap = 0.5;
          map.options.wheelPxPerZoomLevel = 100;
        } else {
          body.classList.remove("print");
          b.classList.remove("selected");
          classes.forEach((c) => cl.remove(c));
          map.invalidateSize();
          delete map.options.zoomDelta;
          delete map.options.zoomSnap;
          delete map.options.wheelPxPerZoomLevel;
          map.setZoom(map.getZoom());
        }
      });
      return b;
    }

    const pb = L.DomUtil.create("div", "printbuttons hide");
    div.appendChild(pb);
    pb.appendChild(button("&nbsp;", "print mode/download image"));
    pb.appendChild(button("A4", "A4 landscape", "A4 landscape"));
    pb.appendChild(button("A4", "A4 portrait", "A4 portrait"));
    pb.appendChild(button("A3", "A3 landscape", "A3 landscape"));
    pb.appendChild(button("A3", "A3 portrait", "A3 portrait"));
    pb.addEventListener("mouseenter", () => pb.classList.remove("hide"));
    pb.addEventListener("mouseleave", () => pb.classList.add("hide"));

    return div;
  },
});

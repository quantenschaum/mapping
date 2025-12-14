import L from "leaflet";
import "./infobox.less";

export const InfoBox = L.Control.extend({
  options: {
    position: "bottomleft",
    text: "infotext",
    hideonclick: true,
    timeout: 0,
  },
  onAdd: function (map) {
    const div = L.DomUtil.create("div", "leaflet-bar leaflet-control infobox");
    L.DomEvent.disableClickPropagation(div);
    div.innerHTML = this.options.text;
    if (this.options.hideonclick) {
      div.addEventListener("click", (e) => div.remove());
    }
    const timeout = this.options.timeout;
    if (timeout) setTimeout(() => div.remove(), timeout * 1000);
    return div;
  },
});

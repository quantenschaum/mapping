import L from 'leaflet';
import './print.less';

export const PrintButton = L.Control.extend({
  options: {position: 'topleft'},
  onAdd: function (map) {
    var div = L.DomUtil.create('div', 'printmode leaflet-bar');
    var button = L.DomUtil.create('a');
    button.innerHTML = '&#x1F5B6;'; // 🖶
    button.title = 'toggle print layout';
    div.appendChild(button);
    const mapc = map.getContainer();
    button.addEventListener('click', () => {
      if (mapc.classList.contains('print')) {
        mapc.classList.remove('print');
        map.invalidateSize();
        delete map.options.zoomDelta;
        delete map.options.zoomSnap;
        delete map.options.wheelPxPerZoomLevel;
      } else {
        mapc.classList.add('print');
        map.invalidateSize();
        map.options.zoomDelta = 0.5;
        map.options.zoomSnap = 0.5;
        map.options.wheelPxPerZoomLevel = 100;
      }
    });
    L.DomEvent.disableClickPropagation(div);
    return div;
  },
});

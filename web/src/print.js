import L from 'leaflet';
import domtoimage from 'dom-to-image';
import './print.less';

export const PrintButton = L.Control.extend({
  options: {position: 'topleft'},
  onAdd: function (map) {
    const div = L.DomUtil.create('div', 'printmode leaflet-bar');
    L.DomEvent.disableClickPropagation(div);

    const printButton = L.DomUtil.create('a');
    printButton.innerHTML = '&#x1F5B6;'; // 🖶
    printButton.title = 'toggle print layout';
    div.appendChild(printButton);
    const mapc = map.getContainer();
    printButton.addEventListener('click', () => {
      const cl = mapc.classList;
      if (cl.contains('portrait')) {
        cl.remove('print');
        cl.remove('portrait');
        map.invalidateSize();
        delete map.options.zoomDelta;
        delete map.options.zoomSnap;
        delete map.options.wheelPxPerZoomLevel;
      } else {
        cl.add('print');
        if (cl.contains('landscape')) {
          cl.remove('landscape');
          cl.add('portrait');
        } else {
          cl.add('landscape');
        }
        map.invalidateSize();
        map.options.zoomDelta = 0.5;
        map.options.zoomSnap = 0.5;
        map.options.wheelPxPerZoomLevel = 100;
      }
    });

    const imgButton = L.DomUtil.create('a');
    imgButton.innerHTML = '&#x1F5BC;'; // 🖼
    imgButton.title = 'save image';
    div.appendChild(imgButton);
    imgButton.addEventListener('click', async () => {
      const size = map.getSize();
      console.log(size);
      mapc.classList.add('image');
      // await new Promise(r => setTimeout(r, 500));
      await domtoimage.toPng(mapc, {height: size.y, width: size.x})
        .then(function (dataUrl) {
          const link = L.DomUtil.create('a');
          link.download = `freenauticalchart-${map.getZoom()}-${map.getCenter().lat.toFixed(3)}-${map.getCenter().lng.toFixed(3)}.png`;
          link.href = dataUrl;
          link.click();
        })
        .catch(console.error);
      mapc.classList.remove('image');
    });

    return div;
  },
});

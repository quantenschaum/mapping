import L from 'leaflet';
import domtoimage from 'dom-to-image';
import './print.less';

export const PrintButton = L.Control.extend({
  options: {position: 'topleft'},
  onAdd: function (map) {
    const div = L.DomUtil.create('div', 'printmode leaflet-bar');
    L.DomEvent.disableClickPropagation(div);

    const classes = [];

    function button(name, title, cls) {
      classes.push(cls);
      const b = L.DomUtil.create('a', cls ? 'format' : '');
      b.innerHTML = name;
      b.title = title;
      const cont = map.getContainer();
      b.addEventListener('click', () => {
        const cl = cont.classList;
        if (cls) {
          cl.add('print');
          classes.forEach(c => cl.remove(c));
          cl.add(cls);
          map.invalidateSize();
          map.options.zoomDelta = 0.5;
          map.options.zoomSnap = 0.5;
          map.options.wheelPxPerZoomLevel = 100;
        } else {
          cl.remove('print');
          classes.forEach(c => cl.remove(c));
          map.invalidateSize();
          delete map.options.zoomDelta;
          delete map.options.zoomSnap;
          delete map.options.wheelPxPerZoomLevel;
          map.setZoom(map.getZoom());
        }
      });
      return b;
    }

    const pb = L.DomUtil.create('div', 'printbuttons hidebuttons');
    div.appendChild(pb);
    pb.appendChild(button('&#x1F5B6;', 'reset print layout'));
    pb.appendChild(button('A4L', 'A4 landscape', 'A4landscape'));
    pb.appendChild(button('A4P', 'A4 portrait', 'A4portrait'));
    pb.appendChild(button('A3L', 'A3 landscape', 'A3landscape'));
    pb.appendChild(button('A3P', 'A3 portrait', 'A3portrait'));
    pb.addEventListener('mouseover', () => {
      pb.classList.remove('hidebuttons');
    });
    pb.addEventListener('mouseout', () => {
      pb.classList.add('hidebuttons');
    });

    const imgButton = L.DomUtil.create('a');
    imgButton.innerHTML = '&#x1F5BC;'; // 🖼
    imgButton.title = 'save image';
    div.appendChild(imgButton);
    imgButton.addEventListener('click', async () => {
      const size = map.getSize();
      const cont = map.getContainer();
      cont.classList.add('image');
      // await new Promise(r => setTimeout(r, 500));
      await domtoimage.toPng(cont, {height: size.y, width: size.x})
        .then(function (dataUrl) {
          const link = L.DomUtil.create('a');
          link.download = `freenauticalchart-${map.getZoom()}-${map.getCenter().lat.toFixed(3)}-${map.getCenter().lng.toFixed(3)}.png`;
          link.href = dataUrl;
          link.click();
        }).catch(console.error);
      cont.classList.remove('image');
    });

    return div;
  },
});

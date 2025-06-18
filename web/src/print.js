import L from 'leaflet';
import domtoimage from 'dom-to-image';
import './print.less';

export const PrintButton = L.Control.extend({
  options: {position: 'topleft'},
  onAdd: function (map) {
    const div = L.DomUtil.create('div', 'printmode leaflet-bar');
    L.DomEvent.disableClickPropagation(div);

    const classes = [];

    function button(name, title, cls = '') {
      const clss = cls.split(' ').filter(c => c);
      clss.forEach(c => classes.push(c));
      const b = L.DomUtil.create('a', cls ? 'format ' + clss.at(-1) : 'button');
      b.innerHTML = name;
      b.title = title;
      const body = document.body;
      const cont = map.getContainer();
      b.addEventListener('click', () => {
        const cl = cont.classList;
        if (cls) {
          body.classList.add('print');
          classes.forEach(c => cl.remove(c));
          clss.forEach(c => cl.add(c));
          map.invalidateSize();
          map.options.zoomDelta = 0.5;
          map.options.zoomSnap = 0.5;
          map.options.wheelPxPerZoomLevel = 100;
        } else {
          body.classList.remove('print');
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
    pb.appendChild(button('&nbsp;', 'reset print layout'));
    pb.appendChild(button('A4', 'A4 landscape', 'A4 landscape'));
    pb.appendChild(button('A4', 'A4 portrait', 'A4 portrait'));
    pb.appendChild(button('A3', 'A3 landscape', 'A3 landscape'));
    pb.appendChild(button('A3', 'A3 portrait', 'A3 portrait'));
    pb.addEventListener('mouseover', () => {
      pb.classList.remove('hidebuttons');
    });
    pb.addEventListener('mouseout', () => {
      pb.classList.add('hidebuttons');
    });

    const imgButton = L.DomUtil.create('a', 'imagebutton');
    imgButton.innerHTML = '&nbsp;';
    imgButton.title = 'download image';
    div.appendChild(imgButton);
    imgButton.addEventListener('click', async () => {
      const size = map.getSize();
      const body = document.body;
      body.classList.add('image');
      // await new Promise(r => setTimeout(r, 500));
      await domtoimage.toPng(map.getContainer(), {height: size.y, width: size.x})
        .then(function (dataUrl) {
          const link = L.DomUtil.create('a');
          link.download = `freenauticalchart-${map.getZoom()}-${map.getCenter().lat.toFixed(3)}-${map.getCenter().lng.toFixed(3)}.png`;
          link.href = dataUrl;
          link.click();
        }).catch(console.error);
      body.classList.remove('image');
    });

    return div;
  },
});

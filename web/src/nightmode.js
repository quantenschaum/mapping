import L from 'leaflet';
import {log} from './utils';
import './nightmode.less';

export const NightSwitch = L.Control.extend({
  options: {position: 'topleft'},
  onAdd: function (map) {
    log('NightSwitch', 'brown', 'added');
    var div = L.DomUtil.create('div', 'nightswitch leaflet-bar leaflet-control');
    var button = L.DomUtil.create('a');
    button.innerHTML = '&#x1F319;'; // 🌙
    button.title = 'toggle night mode';
    div.appendChild(button);
    map = map.getContainer();
    button.addEventListener('click', () => {
      if (map.classList.contains('night')) {
        map.classList.remove('night');
      } else {
        map.classList.add('night');
      }
    });
    L.DomEvent.disableClickPropagation(div);
    return div;
  },
});

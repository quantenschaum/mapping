// default zoom, center and rotation
let zoom = 2;
let center = [0, 0];
let rotation = 0;

if (window.location.hash !== '') {
  // try to restore center, zoom-level and rotation from the URL
  const hash = window.location.hash.replace('#map=', '');
  const parts = hash.split('/');
  if (parts.length === 4) {
    zoom = parseFloat(parts[0]);
    center = [parseFloat(parts[1]), parseFloat(parts[2])];
    rotation = parseFloat(parts[3]);
  }
}

const map = new ol.Map({
  layers: [
    new ol.layer.Tile({ source: new ol.source.OSM(), }),
  ],
  target: 'map',
  view: new ol.View({
    center: center,
    zoom: zoom,
    rotation: rotation,
  }),
});

//layer = new ol.layer.VectorTile({declutter: true});
//olms.applyStyle(layer,"https://api.maptiler.com/maps/openstreetmap/style.json?key=L8FrrrJGE2n415wJo8BL");
//map.addLayer(layer);

layer = new ol.layer.VectorTile({declutter: true});
olms.applyStyle(layer,"style.json");
map.addLayer(layer);

//console.log(map);

let shouldUpdate = true;
const view = map.getView();
const updatePermalink = function () {
  if (!shouldUpdate) {
    // do not update the URL when the view was changed in the 'popstate' handler
    shouldUpdate = true;
    return;
  }

  const center = view.getCenter();
  const hash =
    '#map=' +
    view.getZoom().toFixed(2) +
    '/' +
    center[0].toFixed(2) +
    '/' +
    center[1].toFixed(2) +
    '/' +
    view.getRotation();
  const state = {
    zoom: view.getZoom(),
    center: view.getCenter(),
    rotation: view.getRotation(),
  };
  window.history.pushState(state, 'map', hash);
};

map.on('moveend', updatePermalink);

// restore the view state when navigating through the history, see
// https://developer.mozilla.org/en-US/docs/Web/API/WindowEventHandlers/onpopstate
window.addEventListener('popstate', function (event) {
  if (event.state === null) {
    return;
  }
  map.getView().setCenter(event.state.center);
  map.getView().setZoom(event.state.zoom);
  map.getView().setRotation(event.state.rotation);
  shouldUpdate = false;
});

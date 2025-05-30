var style=(new URL(document.location)).searchParams.get("style");
if(!style) style='style.json';


var map = new maplibregl.Map({
    container: 'map', // container id
//    style: 'https://demotiles.maplibre.org/style.json',
//    style: 'https://api.maptiler.com/maps/openstreetmap/style.json?key=L8FrrrJGE2n415wJo8BL',
    style: style,
    center: [9.239,54.397], // starting position [lng, lat]
    zoom: 7, // starting zoom
    hash: true,
});

map.addControl(new maplibregl.NavigationControl(),'top-left');

map.on('click', 'SkinOfTheEarth', (e) => {
  console.log(e);
  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`${e.features[0].properties}`)
    .addTo(map);
});

//map.on("styleimagemissing", e=>{
//  var id=e.id;
//  var size=64;
//  var url=(id.includes('INT1')?id:"icons/"+id)+".svg";
//  var img=new Image(size,size);
////  console.log("svg",id,url);
//  img.onload = ()=>{
//    console.log("loaded",id,url);
//    if(!map.hasImage(id)) {
//      map.addImage(id, img);
//    }
//  };
//  img.src=url;
//});


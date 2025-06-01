var style=(new URL(document.location)).searchParams.get("style");
if(!style) style='style.json';

async function mergeStyles(styleUrl1, styleUrl2) {
  const [style1, style2] = await Promise.all([
    fetch(styleUrl1).then(res => res.json()),
    fetch(styleUrl2).then(res => res.json())
  ]);

  const mergedSources = {
    ...style1.sources,
    ...style2.sources
  };

  const mergedLayers = [...style1.layers, ...style2.layers];

  const mergedStyle = {
    ...style1,
    sprite: style2.sprite,
    sources: mergedSources,
    layers: mergedLayers
  };

  return mergedStyle;
}

mergeStyles('https://api.maptiler.com/maps/openstreetmap/style.json?key=L8FrrrJGE2n415wJo8BL', style)
  .then(mergedStyle => {
    const map = new maplibregl.Map({
      container: 'map',
      style: mergedStyle,
      center: [9.239,54.397], // starting position [lng, lat]
      zoom: 7, // starting zoom
      hash: true,
    });
    map.addControl(new maplibregl.NavigationControl(),'top-left');
  });

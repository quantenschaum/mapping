import geomagnetism from "geomagnetism";

const magModel = geomagnetism.model(new Date());
console.log("magModel", magModel);

export function declination(pos) {
  if (pos.lat < 46.5 && pos.lat > 45.6 && pos.lng > -6.42 && pos.lng < -5.57)
    return -7;
  return magModel.point([pos.lat, pos.lng]).decl;
}

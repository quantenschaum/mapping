export function log(label, color, ...args) {
  console.log(
    "%c" + label,
    `background-color: ${color}; color: white; font-weight: bold; padding: 2px 4px; border-radius: 4px`,
    ...args,
  );
}

export function logger(label, color) {
  return function (...args) {
    log(label, color, ...args);
  };
}

export function debounce(func, delay = 1000) {
  let timer;
  return function (...args) {
    const context = this;
    clearTimeout(timer);
    timer = setTimeout(() => func.apply(context, args), delay);
  };
}

export function deg(a) {
  return (a * 180) / Math.PI;
}

export function rad(a) {
  return (a * Math.PI) / 180;
}

export function to360(a) {
  return (a + 360) % 360;
}

export function to180(a) {
  return to360(a + 180) - 180;
}

export function p2c(r, theta) {
  let angle = rad(theta);
  const x = r * Math.sin(angle);
  const y = r * Math.cos(angle);
  return { x, y };
}

export function c2p(x, y) {
  let angle = Math.atan2(x, y);
  const r = Math.sqrt(x * x + y * y);
  let theta = to360(deg(angle));
  return { r, theta };
}

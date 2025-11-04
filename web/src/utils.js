const debug = process.env.NODE_ENV === "development";

export function log(label, color, ...args) {
  // if (!debug) return;
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

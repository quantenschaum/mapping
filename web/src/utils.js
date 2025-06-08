const debug = process.env.NODE_ENV === 'development';

export function log(label, color, ...args) {
  if (!debug) return;
  console.log('%c' + label,
    `background-color: ${color}; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px`,
    ...args);
}

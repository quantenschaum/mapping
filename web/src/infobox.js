import "./infobox.less";

const isStandalone = !!(
  window.matchMedia("(display-mode: standalone)").matches ||
  window.navigator.standalone
);

function createElementFromHTML(htmlString) {
  const template = document.createElement("template");
  template.innerHTML = htmlString.trim();
  return template.content.firstChild;
}

const storage = isStandalone ? localStorage : sessionStorage;

function setInt(name, value) {
  storage.setItem(name, value);
}

function getInt(name) {
  try {
    return parseInt(storage.getItem(name) ?? 0);
  } catch (x) {
    return 0;
  }
}

export function showDialog(options = {}) {
  console.log(Date.now(), getInt("infoshown"));
  if (Date.now() - getInt("infoshown") < 24 * 3600 * 1000) return;
  options = {
    title: "Title",
    text: "lorem ipsum",
    button: "Close",
    callback: null,
    ...options,
  };
  const el = createElementFromHTML(`
    <dialog class="infobox modal">
      <form method="dialog">
        ${options.img ? '<img src="' + options.img + '" />' : ""}
        <h2>${options.title}</h2>
        ${options.text}
        <button id="closebutton">${options.button}</button>
      </form>
    </dialog>
    `);
  document.body.appendChild(el);
  const btn = document.getElementById("closebutton");
  btn.addEventListener("click", (e) => setInt("infoshown", Date.now()));
  if (options.callback) {
    options.callback();
  }
  el.showModal();
}

import "./infobox.less";

function createElementFromHTML(htmlString) {
  const template = document.createElement("template");
  template.innerHTML = htmlString.trim();
  return template.content.firstChild;
}

function setSessionBool(name, value) {
  sessionStorage.setItem(name, value);
}

function getSessionBool(name) {
  return sessionStorage.getItem(name) == "true";
}

export function showDialog(options = {}) {
  if (getSessionBool("infoshown")) return;
  options = {
    title: "Title",
    text: "lorem ipsum",
    button: "Close",
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
  btn.addEventListener("click", (e) => setSessionBool("infoshown", true));
  el.showModal();
}

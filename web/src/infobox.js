import "./infobox.less";

const isDevMode = process.env.NODE_ENV === "development";

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

export function showDialog(options = { title: "Title", text: "lorem ipsum" }) {
  if (getSessionBool("infoshown")) return;
  const el = createElementFromHTML(`
    <dialog class="modal">
      <form method="dialog">
        ${options.img ? '<img src="' + options.img + '" />' : ""}
        <h2>${options.title}</h2>
        ${options.text}
        <button id="closebutton">Close</button>
      </form>
    </dialog>
    `);
  document.body.appendChild(el);
  const btn = document.getElementById("closebutton");
  btn.addEventListener("click", (e) => setSessionBool("infoshown", true));
  el.showModal();
}

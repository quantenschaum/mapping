import "./infobox.less";

const isDevMode = process.env.NODE_ENV === "development";

function createElementFromHTML(htmlString) {
  const template = document.createElement("template");
  template.innerHTML = htmlString.trim();
  return template.content.firstChild;
}

function setSessionBoolCookie(name, value) {
  document.cookie =
    encodeURIComponent(name) + "=" + encodeURIComponent(value) + "; path=/";
}

function getSessionBoolCookie(name) {
  const nameEQ = encodeURIComponent(name) + "=";
  const cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    let c = cookies[i].trim();
    if (c.indexOf(nameEQ) === 0) {
      return c.substring(nameEQ.length) === "true";
    }
  }
  return null;
}

export function showDialog(options = { title: "Title", text: "lorem ipsum" }) {
  if (!isDevMode && getSessionBoolCookie("infoshown")) return;
  const el = createElementFromHTML(`
    <dialog class="modal">
      <form method="dialog">
        <h2>${options.title}</h2>
        ${options.text}
        <button id="closebutton">Close</button>
      </form>
    </dialog>
    `);
  document.body.appendChild(el);
  const btn = document.getElementById("closebutton");
  btn.addEventListener("click", (e) => setSessionBoolCookie("infoshown", true));
  el.showModal();
}

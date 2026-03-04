async function download(url) {
  console.log("download", url);
  alert(`downloading ${url}, wait for it to finish...`);

  try {
    const parts = [url.replace("?", ".0?"), url.replace("?", ".1?")];
    const buffers = await Promise.all(
      parts.map((url) =>
        fetch(url).then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText}`);
          return r.arrayBuffer();
        }),
      ),
    );
    const blob = new Blob(buffers, { type: "application/octet-stream" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = url.replace(/.*\//, "").replace(/\?.*/, "");
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (err) {
    alert(`download failed ${err}`);
  }
}

function init(name) {
  console.log("init downloader for", name);
  const links = document.querySelectorAll(`a[href^="${name}"]`);
  links.forEach((l) => {
    console.log("init on", l.href);
    l.onclick = (e) => {
      e.preventDefault();
      console.log("clicked", l.href);
      download(l.href);
    };
  });
}

window.addEventListener("load", function () {
  init("qmap-de.mbtiles");
  init("qmap-de.sqlitedb");
});

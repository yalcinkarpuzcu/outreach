"""Önizleme paketi: gerçek sayfalar + sahte API, tek dosyada (yalnızca sohbet önizlemesi için, Workiom'a GİTMEZ)."""
import json, re, sys
from pathlib import Path
SRC = Path(__file__).resolve().parent.parent / "arge-proje-merkezi"
MOCK = Path(__file__).resolve().parent
out = Path(sys.argv[1])
css = (SRC / "styles.css").read_text()
common = ["schema.js", "app.js"]
mock = [(MOCK / "mock-data.js").read_text(), (MOCK / "mock-api.js").read_text()]
NAV = """
<script>
/* önizleme: sayfa geçişlerini ebeveyne ilet */
document.addEventListener("click", e => {
  const a = e.target.closest && e.target.closest("a[href]");
  if (!a) return;
  const h = a.getAttribute("href");
  if (!/^[a-z]+\\.html/.test(h)) return;
  e.preventDefault();
  parent.postMessage({ nav: h }, "*");
}, true);
</script>"""
pages = {}
for html in ["index.html", "plan.html", "gorevlerim.html", "kutuphane.html"]:
    doc = (SRC / html).read_text()
    doc = doc.replace('<link rel="stylesheet" href="styles.css">', "<style>" + css + "</style>")
    def inline(m):
        name = m.group(1)
        js = (SRC / name).read_text()
        js = js.replace("location.search", "(window.__QS || location.search)")
        extra = "".join("<script>" + x + "</script>" for x in mock) if name == "app.js" else ""
        return "<script>" + js.replace("</script", "<\\/script") + "</script>" + extra
    doc = re.sub(r'<script src="([a-z]+\.js)"></script>', inline, doc)
    doc = doc.replace("</body>", NAV + "</body>")
    pages[html] = doc
shell = """<title>Ar-Ge Proje Merkezi</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root { --bg: #f4f6f8; --fg: #0f1b26; --banner: #7a4b00; --banner-bg: #fff3d6; --line: #dde2e8; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #121416; --fg: #f0efec; --banner: #fab219; --banner-bg: #3a2e12; --line: #2f3439; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #121416; --fg: #f0efec; --banner: #fab219; --banner-bg: #3a2e12; --line: #2f3439; color-scheme: dark }
html, body { height: 100%; }
body { background: var(--bg); color: var(--fg); display: flex; flex-direction: column; }
.pv { flex: none; padding-block: 7px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  background: var(--banner-bg); color: var(--banner); font: 600 13px/1.4 system-ui, sans-serif; border-bottom: 1px solid var(--line); }
iframe { flex: 1; width: 100%; border: 0; background: var(--bg); }
</style>
<div class="pv" role="note">Önizleme — örnek veri, Workiom'a bağlı değil. Sayfalar arası geçişte örnek veri baştan yüklenir; Excel indirme önizlemede çalışmaz.</div>
<iframe id="app" title="Ar-Ge Proje Merkezi önizleme"></iframe>
<script>
const PAGES = """ + json.dumps(pages).replace("</", "<\\/") + """;
const frame = document.getElementById("app");
function go(href) {
  const [file, qs] = href.split("?");
  const doc = PAGES[file.split("#")[0]];
  if (!doc) return;
  frame.srcdoc = doc.replace("<head>", "<head><script>window.__QS=" + JSON.stringify(qs ? "?" + qs : "") + "<\\/script>");
}
window.addEventListener("message", e => { if (e.source === frame.contentWindow && e.data && e.data.nav) go(e.data.nav); });
go("index.html");
</script>
"""
out.write_text(shell)
print(out, len(shell))

"""Önizleme: gerçek paket + sahte API tek dosyada (yalnızca sohbet önizlemesi/test için, Workiom'a GİTMEZ)."""
import re, sys
from pathlib import Path
SRC = Path(__file__).resolve().parent.parent / (sys.argv[2] if len(sys.argv) > 2 else "proje-yonetimi")
MOCK = Path(__file__).resolve().parent
out = Path(sys.argv[1])
NAME = "Proje Merkezi" if "merkezi" in str(SRC) else "Proje Yönetimi"
doc = (SRC / "index.html").read_text()
css = (SRC / "styles.css").read_text()
doc = doc.replace('<link rel="stylesheet" href="styles.css">', "<style>" + css + "</style>")
def inline(m):
    name = m.group(1)
    js = (SRC / name).read_text().replace("</script", "<\\/script")
    tag = "<script>" + js + "</script>"
    if name == "core.js":
        for x in ("mock-data2.js", "mock-api2.js"):
            tag += "<script>" + (MOCK / x).read_text().replace("</script", "<\\/script") + "</script>"
    return tag
doc = re.sub(r'<script src="([a-z]+\.js)"></script>', inline, doc)
banner = ('<div role="note" style="flex:none;padding:6px 16px;background:#fff3d6;color:#7a4b00;font:600 12.5px/1.4 system-ui,sans-serif;border-bottom:1px solid #e8d7a8">'
          'Önizleme — örnek veri, Workiom\'a bağlı değil. Otomasyonlar (kilit, onay, ardıllar, kilometre taşı, baseline, plan kurulumu) taklit edilir; dosya indirme çalışmaz.</div>')
doc = doc.replace('<div class="app">', banner + '<div class="app">').replace('<div class="shell">', banner + '<div class="shell">')
doc = doc.replace(".app { display: grid; grid-template-rows: auto auto auto 1fr auto; height: 100vh;", ".app { display: grid; grid-template-rows: auto auto auto 1fr auto; height: calc(100vh - 31px);")
head_style = re.search(r"<style>.*?</style>", doc, re.S).group(0)
body = re.search(r"<body>(.*)</body>", doc, re.S).group(1)
fix = "<style>html,body{height:100%}body{background:var(--bg)}.app,.shell{height:calc(100% - 31px)!important}</style>"
doc = "<title>" + NAME + " Önizleme</title>\n" + head_style + fix + body
out.write_text(doc)
print(out, len(doc))

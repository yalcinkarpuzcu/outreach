import sys
T={
 "A":dict(name="Kâğıt Masa",bg="#F5EFE4",ink="#221E52",soft="#E9E0CF",line="#221E52",acc="#8A3FFC",acc2="#F0287A",acc3="#F6B71E",tex="paper"),
 "B":dict(name="Gece Vardiyası",bg="#17143A",ink="#F3EEFF",soft="#26215A",line="#B9A8FF",acc="#A46BFF",acc2="#FF4F93",acc3="#FFC845",tex="glow"),
 "C":dict(name="Metro Haritası",bg="#EEEBFA",ink="#1F1B4D",soft="#DCD6F5",line="#1F1B4D",acc="#7B35F0",acc2="#E8236F",acc3="#F2A900",tex="grid"),
}
k=sys.argv[1];t=T[k]
tex={"paper":"background-image:radial-gradient(rgba(34,30,82,.07) 1px,transparent 1.2px);background-size:7px 7px;",
     "glow":"background-image:radial-gradient(900px 600px at 70% 30%,rgba(164,107,255,.28),transparent 70%),radial-gradient(700px 500px at 15% 90%,rgba(255,79,147,.16),transparent 70%);",
     "grid":"background-image:linear-gradient(rgba(31,27,77,.07) 2px,transparent 2px),linear-gradient(90deg,rgba(31,27,77,.07) 2px,transparent 2px);background-size:60px 60px;"}[t["tex"]]
nodes=[("1","≤ 15 dk","İLK ARAMA",t["acc"]),("2","+2 saat","AYNI GÜN",t["acc"]),("3","1 gün","OTOMASYON",t["acc3"]),("4","ertesi gün","FARKLI SAAT",t["acc"]),("5","ertesi gün","SON DENEME",t["acc2"])]
xs=[260,610,960,1310,1660]
dash='stroke-dasharray="2 16"' if k=="A" else ""
rope = f'<path d="M140 560 C 400 470, 500 650, 610 560 S 860 470, 960 560 S 1200 650, 1310 560 S 1560 470, 1780 560" stroke="{t["line"]}" stroke-width="5" fill="none" stroke-linecap="round" {dash}/>' if k!="C" else f'<path d="M140 560 H1780" stroke="{t["acc"]}" stroke-width="22" stroke-linecap="round"/>'
html=f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../assets/fonts.css"><style>
*{{margin:0;box-sizing:border-box}}body{{width:1920px;height:1080px;background:{t["bg"]};{tex}font-family:Rubik;color:{t["ink"]};position:relative;overflow:hidden}}
.k{{position:absolute;left:120px;top:110px;font:600 30px 'JetBrains Mono';letter-spacing:.12em;color:{t["acc"]}}}
.h{{position:absolute;left:120px;top:160px;font:600 104px/1 Fraunces;letter-spacing:-.03em}}
.h i{{font-style:italic;font-weight:400;color:{t["acc2"]}}}
.n{{position:absolute;width:150px;height:150px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:800 64px Rubik;transform:translate(-50%,-50%)}}
.lb{{position:absolute;transform:translateX(-50%);text-align:center;top:680px}}
.lb b{{display:block;font:700 40px Rubik}} .lb span{{display:block;font:500 24px 'JetBrains Mono';letter-spacing:.1em;opacity:.75;margin-top:8px}}
.end{{position:absolute;right:120px;bottom:110px;font:400 italic 40px Fraunces;opacity:.9}}
.tag{{position:absolute;left:120px;bottom:100px;font:500 22px 'JetBrains Mono';opacity:.6}}
</style></head><body>
<div class="k">TAKİP KADANSI</div><div class="h">Beş deneme, <i>sonra</i> karar.</div>
<svg width="1920" height="1080" style="position:absolute;left:0;top:0">{rope}</svg>
{"".join(f'<div class="n" style="left:{x}px;top:560px;background:{c};color:{t["bg"]};{"border:6px solid "+t["bg"]+";box-shadow:0 0 0 6px "+t["acc"] if k=="C" else ("box-shadow:0 0 60px "+c+"88" if k=="B" else "box-shadow:8px 10px 0 "+t["ink"])}">{n}</div><div class="lb" style="left:{x}px"><b>{a}</b><span>{b}</span></div>' for (n,a,b,c),x in zip(nodes,xs))}
<div class="end">5 başarısız temas → Unqualified · Non-responding</div>
<div class="tag">TEMA {k} — {t["name"].upper().replace("I","I")}</div>
</body></html>'''
open(f"theme-{k}.html","w").write(html)

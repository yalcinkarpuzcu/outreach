"""Bir projenin görevlerini doğrular: sayı, tarih, hiyerarşi, öncüllerin proje dışına sızmaması.

  API_KEY=... python dogrula.py <proje_id>
"""
import sys

from wk import *  # noqa: F401,F403
from farmatek_seed import records


def gorevler(proje_id):
    fm = {str(f["id"]): f["name"] for f in fields("Görevler")}
    out = []
    for r in records("Görevler"):
        d = {fm.get(k, k): v for k, v in r.items() if not k.startswith("view-")}
        if any(p["_id"] == proje_id for p in d.get("Proje") or []):
            out.append(d)
    return out


def main(proje_id):
    gs = gorevler(proje_id)
    ids = {g["_id"] for g in gs}
    print(f"görev sayısı: {len(gs)}")
    sizinti = ust_yok = 0
    for g in sorted(gs, key=lambda g: g.get("WBS No") or 0):
        onc = g.get("Öncüller") or []
        disari = [o for o in onc if o["_id"] not in ids]
        sizinti += len(disari)
        if g.get("Tür", {}).get("label") != "Faz" and not g.get("Üst Görev"):
            ust_yok += 1
        print(f"  {int(g.get('WBS No') or 0):>4} {g['Görev Adı'][:42]:<42} "
              f"{(g.get('Başlangıç') or '')[:10]} → {(g.get('Bitiş') or '')[:10]} "
              f"üst={(g.get('Üst Görev') or [{}])[0].get('label', '-')[:18]:<18} "
              f"öncül={[o['label'][:14] for o in onc]} açık={g.get('Açık Öncül Sayısı')} "
              f"durum={g.get('Durum', {}).get('label')}")
    print(f"proje dışı öncül bağı: {sizinti} · üst öğesi olmayan görev: {ust_yok}")


if __name__ == "__main__":
    main(sys.argv[1])

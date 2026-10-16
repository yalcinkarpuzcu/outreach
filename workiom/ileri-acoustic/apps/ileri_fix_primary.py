"""Tüm İleri Acoustic listelerinde birincil alanı zorunlu olmaktan çıkarır
(otomasyonlar ve webhook'lar kayıt açabilsin; zorunluluk formlarda)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workiom.client import WorkiomClient
c = WorkiomClient((ROOT / ".env").read_text().split("=", 1)[1].strip())
for sf in sorted((ROOT / "state").glob("*.json")):
    for ln, ld in json.loads(sf.read_text())["lists"].items():
        for f in c.get_all_fields(ld["id"]):
            if f.get("isRequired"):
                f["isRequired"] = False
                c.update_field(ld["id"], f["id"], f)
                print(f"  · {ln}.{f['name']} → zorunlu değil")

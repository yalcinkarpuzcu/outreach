import sys, time, json
sys.path.insert(0, '.')
from workiom.client import WorkiomClient
from workiom.state import AppState
c = WorkiomClient(open('.env').read().split('=', 1)[1].strip())
P, S = AppState('Ar-Ge Proje Takibi'), AppState('Numune ve Hammadde Stok')
created = []

def fid(st, l, f): return str(st.get_field_id(l, f))
def mk(st, l, vals):
    lid = st.get_list_id(l)
    rid = c.create_record(lid, {fid(st, l, k): v for k, v in vals.items()})
    created.append((lid, rid, l)); return rid
def link(r): return [{"_id": r}]
def get(st, l, rid):
    m = {str(v): k for k, v in st.get_all_fields(l).items()}
    r = c.get(f"/api/services/app/Data/Get", {"listId": st.get_list_id(l), "id": rid})
    return {m.get(k, k): v for k, v in r.items()}
def records(st, l):
    m = {str(v): k for k, v in st.get_all_fields(l).items()}
    return [{m.get(k, k): v for k, v in r.items()} for r in c.get_all_records(st.get_list_id(l))]

mal = mk(S, 'Malzeme Kartları', {'Malzeme Kodu': 'TEST-001', 'Malzeme Adı': 'Test Laktoz', 'Birim': 'g', 'Kritik Stok Seviyesi': 800})
lot = mk(S, 'Lotlar', {'Lot No': 'TEST-LOT-1', 'Giriş Miktarı': 1000, 'Birim Maliyet': 2, 'Malzeme': link(mal)})
prj = mk(P, 'Ar-Ge Projeleri', {'Proje Kodu': 'TEST-PRJ', 'Ürün Adı': 'Test Ürün', 'Durum': 'Aktif'})
den = mk(P, 'Formülasyon Denemeleri', {'Deneme Kodu': 'TEST-D1', 'Proje': link(prj)})
print('created test records; waiting for lot-entry automation...')
for i in range(24):
    time.sleep(10)
    h = [r for r in records(S, 'Stok Hareketleri') if 'TEST-LOT-1' in json.dumps(r.get('Lot'), ensure_ascii=False)]
    if h: break
print('auto giriş hareketi:', [(r.get('Ad'), (r.get('Hareket Tipi') or {}).get('label'), r.get('Giriş Miktarı')) for r in h])
for r in h: created.append((S.get_list_id('Stok Hareketleri'), r['_id'], 'Stok Hareketleri'))
l = get(S, 'Lotlar', lot); print('Lot:', l.get('Ad'), 'Durum=', (l.get('Lot Durumu') or {}).get('label'), 'Kalan=', l.get('Kalan Miktar'))
c.update_record(S.get_list_id('Lotlar'), lot, {fid(S, 'Lotlar', 'Lot Durumu'): 'Onaylı'})
bil = mk(S, 'Formül Bileşenleri', {'Miktar': 300, 'Lot': link(lot), 'Deneme': link(den), 'İlgili Proje': link(prj)})
print('formül bileşeni girildi; çıkış hareketi bekleniyor...')
for i in range(24):
    time.sleep(10)
    h2 = [r for r in records(S, 'Stok Hareketleri') if r.get('Çıkış Miktarı')]
    if h2: break
print('auto çıkış hareketi:', [(r.get('Ad'), r.get('Çıkış Miktarı'), r.get('Stok Etkisi'), r.get('Tüketim Maliyeti')) for r in h2])
for r in h2: created.append((S.get_list_id('Stok Hareketleri'), r['_id'], 'Stok Hareketleri'))
time.sleep(15)
l = get(S, 'Lotlar', lot); m = get(S, 'Malzeme Kartları', mal); p = get(P, 'Ar-Ge Projeleri', prj)
print('Lot Kalan Miktar =', l.get('Kalan Miktar'), '(beklenen 700)')
print('Malzeme Toplam Stok =', m.get('Toplam Stok'), '(beklenen 700) | Kritik Seviye Altında =', m.get('Kritik Seviye Altında'), '(beklenen 1) | Ad =', m.get('Ad'))
print('Proje Gerçekleşen Maliyet =', p.get('Gerçekleşen Maliyet'), '(beklenen 600) | Deneme Sayısı =', p.get('Deneme Sayısı'), '| Ad =', p.get('Ad'))
print('Proje Stok Tüketimi bağlantısı:', [x.get('_id') for x in (p.get('Stok Tüketimi') or [])])
json.dump(created, open('smoke_created.json', 'w'))

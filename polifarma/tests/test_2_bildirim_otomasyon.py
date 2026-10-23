import sys, time, json
sys.path.insert(0, '.')
from workiom.client import WorkiomClient
from workiom.state import AppState
c = WorkiomClient(open('.env').read().split('=', 1)[1].strip())
P, S, T = AppState('Ar-Ge Proje Takibi'), AppState('Numune ve Hammadde Stok'), AppState('Toplantı Yönetimi')
U = '162102'
created = []

def fid(st, l, f): return str(st.get_field_id(l, f))
def mk(st, l, vals):
    lid = st.get_list_id(l)
    rid = c.create_record(lid, {fid(st, l, k): v for k, v in vals.items()})
    created.append((lid, rid, l)); return rid
def upd(st, l, rid, vals): c.update_record(st.get_list_id(l), rid, {fid(st, l, k): v for k, v in vals.items()})
def link(r): return [{"_id": r}]
def records(st, l):
    m = {str(v): k for k, v in st.get_all_fields(l).items()}
    return [{m.get(k, k): v for k, v in r.items()} for r in c.get_all_records(st.get_list_id(l))]
def notifs():
    r = c.get('/api/services/app/Notification/GetUserNotifications', {'MaxResultCount': 100})
    return r['items']

base = {n['id'] for n in notifs()}
print('baseline notifications:', len(base))
print(json.dumps(notifs()[0], ensure_ascii=False)[:1500] if notifs() else 'none')

prj = mk(P, 'Ar-Ge Projeleri', {'Proje Kodu': 'TEST-PRJ2', 'Ürün Adı': 'Test', 'Proje Lideri': U, 'Ekip': [U], 'Ar-Ge Direktörü': U, 'Durum': 'Aktif'})
mk(P, 'Görevler ve Sapmalar', {'Başlık': 'TEST sapma', 'Tip': 'Sapma', 'Atanan': U, 'Öncelik': 'Yüksek', 'Durum': 'Açık', 'Proje': link(prj)})
aks = mk(T, 'Aksiyonlar', {'Aksiyon': 'TEST aksiyon', 'Sorumlu': U, 'Durum': 'Açık', 'İlgili Proje': link(prj)})
mal = mk(S, 'Malzeme Kartları', {'Malzeme Kodu': 'TEST-002', 'Malzeme Adı': 'Test MCC', 'Stok Sorumlusu': U})
lot_ok = mk(S, 'Lotlar', {'Lot No': 'TEST-LOT-OK', 'Giriş Miktarı': 500, 'Malzeme': link(mal), 'Stok Sorumlusu': U})
lot_q = mk(S, 'Lotlar', {'Lot No': 'TEST-LOT-Q', 'Giriş Miktarı': 100, 'Malzeme': link(mal), 'Stok Sorumlusu': U})
mk(S, 'Depo Görevleri', {'Başlık': 'TEST depo görevi', 'Görev Tipi': 'Sayım', 'Atanan': U, 'Durum': 'Açık'})
time.sleep(30)  # lot automations set Karantinada
upd(S, 'Lotlar', lot_ok, {'Lot Durumu': 'Onaylı'})
mk(S, 'Stok Hareketleri', {'Hareket Tipi': 'Çıkış', 'Çıkış Miktarı': 10, 'Lot': link(lot_q), 'Yapan Kişi': U})
tal = mk(S, 'Malzeme ve Numune Talepleri', {'Talep Tipi': 'Malzeme', 'Talep Eden': U, 'İstenen Miktar': 50, 'Onaylayıcı (Stok Sorumlusu)': U,
                                            'Malzeme': link(mal), 'Lot': link(lot_ok), 'İlgili Proje': link(prj), 'Durum': 'Taslak'})
kapi = mk(P, 'Faz Kapıları', {'Faz Adı': '1. Literatür ve Fizibilite', 'Sonraki Faz': '2. Ön Formülasyon', 'Durum': 'Devam Ediyor',
                              '1. Onaylayan (Direktör)': U, '2. Onaylayan (QA/Ruhsat)': U, 'Proje': link(prj)})
top = mk(T, 'Toplantılar', {'Başlık': 'TEST haftalık', 'Tip': 'Haftalık Ar-Ge', 'Katılımcılar': [U], 'Organizatör': U, 'Durum': 'Planlandı'})
time.sleep(20)
upd(S, 'Malzeme ve Numune Talepleri', tal, {'Durum': 'Onay Bekliyor'})
upd(P, 'Faz Kapıları', kapi, {'Durum': 'Direktör Onayı Bekliyor'})
upd(T, 'Toplantılar', top, {'Durum': 'Yapıldı', 'AI Özeti': 'Test özeti'})
print('all test actions done; waiting for automations...')
time.sleep(120)
new = [n for n in notifs() if n['id'] not in base]
print(f'\n{len(new)} new notifications:')
for n in new:
    d = n['notification']
    print(' -', json.dumps({k: d.get(k) for k in ('notificationName', 'data', 'listId', 'recordId')}, ensure_ascii=False)[:400])
g = [r for r in records(T, 'Gündem Maddeleri')]
print('\nGündem maddeleri:', [(r.get('Konu'), (r.get('Kaynak') or {}).get('label'), bool(r.get('İlgili Aksiyon'))) for r in g])
for r in g: created.append((T.get_list_id('Gündem Maddeleri'), r['_id'], 'Gündem Maddeleri'))
for r in records(S, 'Stok Hareketleri'): created.append((S.get_list_id('Stok Hareketleri'), r['_id'], 'Stok Hareketleri'))
print('Talep durumu:', [(r.get('Ad'), (r.get('Durum') or {}).get('label')) for r in records(S, 'Malzeme ve Numune Talepleri')])
print('Kapı durumu:', [(r.get('Ad'), (r.get('Durum') or {}).get('label')) for r in records(P, 'Faz Kapıları')])
json.dump({'created': created, 'kapi': kapi, 'tal': tal, 'prj': prj, 'lot_ok': lot_ok}, open('smoke2_created.json', 'w'))

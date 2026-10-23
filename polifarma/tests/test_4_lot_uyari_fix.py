import sys, time, json
sys.path.insert(0, '.')
from workiom.client import WorkiomClient
from workiom.state import AppState
c = WorkiomClient(open('.env').read().split('=', 1)[1].strip())
S, T = AppState('Numune ve Hammadde Stok'), AppState('Toplantı Yönetimi')
U = '162102'
def fid(s, l, f): return str(s.get_field_id(l, f))
def mk(s, l, vals): return c.create_record(s.get_list_id(l), {fid(s, l, k): v for k, v in vals.items()})
def notifs(): return c.get('/api/services/app/Notification/GetUserNotifications', {'MaxResultCount': 200})['items']
base = {n['id'] for n in notifs()}
mal = mk(S, 'Malzeme Kartları', {'Malzeme Kodu': 'TEST-003', 'Malzeme Adı': 'Test fix'})
lot = mk(S, 'Lotlar', {'Lot No': 'TEST-LOT-FIX', 'Giriş Miktarı': 100, 'Malzeme': [{"_id": mal}]})
time.sleep(30)
mk(S, 'Stok Hareketleri', {'Hareket Tipi': 'İade', 'Giriş Miktarı': 5, 'Lot': [{"_id": lot}], 'Yapan Kişi': U})
mk(S, 'Stok Hareketleri', {'Hareket Tipi': 'Çıkış', 'Çıkış Miktarı': 7, 'Lot': [{"_id": lot}], 'Yapan Kişi': U})
mk(T, 'Aksiyonlar', {'Aksiyon': 'TEST aksiyon 2', 'Sorumlu': U, 'Durum': 'Açık'})
time.sleep(90)
for n in notifs():
    if n['id'] not in base:
        print('-', n['notification']['notificationName'].split('.')[-1], '|', n['notification']['data']['message'][:140])

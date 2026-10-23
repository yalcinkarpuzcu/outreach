import sys, time, json
sys.path.insert(0, '.')
from workiom.client import WorkiomClient
from workiom.state import AppState
c = WorkiomClient(open('.env').read().split('=', 1)[1].strip())
P, S = AppState('Ar-Ge Proje Takibi'), AppState('Numune ve Hammadde Stok')
U = '162102'
st = json.load(open('smoke2_created.json')); created = st['created']
def fid(s, l, f): return str(s.get_field_id(l, f))
def get(s, l, rid):
    m = {str(v): k for k, v in s.get_all_fields(l).items()}
    r = c.get('/api/services/app/Data/Get', {'listId': s.get_list_id(l), 'id': rid})
    return {m.get(k, k): v for k, v in r.items()}
def lbl(v): return (v or {}).get('label') if isinstance(v, dict) else v
def pending(record_id):
    out = []
    for n in c.get('/api/services/app/Notification/GetUserNotifications', {'MaxResultCount': 200})['items']:
        p = n['notification']['data'].get('properties', {})
        if n['notification']['notificationName'] == 'App.AutomationApprovalRequest' and p.get('recordId') == record_id:
            out.append(p['approvalRequestId'])
    return out
def wait_for(fn, desc, tries=18):
    for _ in range(tries):
        v = fn()
        if v: return v
        time.sleep(10)
    print('   ✗ timeout:', desc); return None
done = set()
def approve_next(rid, desc):
    ids = wait_for(lambda: [i for i in pending(rid) if i not in done], desc)
    if not ids: return False
    c.post(f"/api/services/app/AutomationApprovalRequest/Approve?approvalRequestId={ids[0]}", {})
    done.add(ids[0]); print('   ✓ onaylandı:', desc); return True

kapi, tal, prj, lot_ok = st['kapi'], st['tal'], st['prj'], st['lot_ok']
print('1) Faz kapısı çift onay')
approve_next(kapi, 'Direktör onayı')
wait_for(lambda: lbl(get(P, 'Faz Kapıları', kapi).get('Durum')) == 'QA Onayı Bekliyor', 'durum QA Onayı Bekliyor')
print('   kapı durumu:', lbl(get(P, 'Faz Kapıları', kapi).get('Durum')))
approve_next(kapi, 'QA onayı')
wait_for(lambda: lbl(get(P, 'Ar-Ge Projeleri', prj).get('Mevcut Faz')) == '2. Ön Formülasyon', 'proje fazı güncellendi')
k = get(P, 'Faz Kapıları', kapi); p = get(P, 'Ar-Ge Projeleri', prj)
print('   kapı:', lbl(k.get('Durum')), '| Gerçekleşen Bitiş:', k.get('Gerçekleşen Bitiş'), '| proje Mevcut Faz:', lbl(p.get('Mevcut Faz')))

print('2) Malzeme talebi onayı')
approve_next(tal, 'Stok sorumlusu onayı')
wait_for(lambda: lbl(get(S, 'Malzeme ve Numune Talepleri', tal).get('Durum')) == 'Onaylandı', 'talep onaylandı')
time.sleep(20)
l = get(S, 'Lotlar', lot_ok)
print('   talep:', lbl(get(S, 'Malzeme ve Numune Talepleri', tal).get('Durum')), '| lot TEST-LOT-OK Kalan Miktar:', l.get('Kalan Miktar'), '(beklenen 450)')
print('   proje Stok Tüketimi kayıt sayısı:', len(get(P, 'Ar-Ge Projeleri', prj).get('Stok Tüketimi') or []))

print('3) Red yolu')
lid = P.get_list_id('Faz Kapıları')
k2 = c.create_record(lid, {fid(P, 'Faz Kapıları', 'Faz Adı'): '2. Ön Formülasyon', fid(P, 'Faz Kapıları', 'Sonraki Faz'): '3. Formülasyon Geliştirme',
                           fid(P, 'Faz Kapıları', 'Durum'): 'Devam Ediyor', fid(P, 'Faz Kapıları', '1. Onaylayan (Direktör)'): U,
                           fid(P, 'Faz Kapıları', 'Proje'): [{"_id": prj}]})
created.append((lid, k2, 'Faz Kapıları'))
time.sleep(10)
c.update_record(lid, k2, {fid(P, 'Faz Kapıları', 'Durum'): 'Direktör Onayı Bekliyor'})
ids = wait_for(lambda: pending(k2), 'red için onay isteği')
if ids:
    c.post(f"/api/services/app/AutomationApprovalRequest/Reject?approvalRequestId={ids[0]}&message=Test%20red", {})
    wait_for(lambda: lbl(get(P, 'Faz Kapıları', k2).get('Durum')) == 'Reddedildi', 'durum Reddedildi')
    print('   kapı 2:', lbl(get(P, 'Faz Kapıları', k2).get('Durum')), '| proje fazı değişmedi:', lbl(get(P, 'Ar-Ge Projeleri', prj).get('Mevcut Faz')))
json.dump({'created': created}, open('smoke3_created.json', 'w'))

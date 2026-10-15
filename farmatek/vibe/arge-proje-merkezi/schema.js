/* Ar-Ge Proje Merkezi — canlı şema keşfinden üretildi (farmatek.workiom.com, 'Ar-Ge Proje Yönetimi'). Elle düzenlemeyin. */
const SCHEMA = {
 "P": {
  "id": "75f4cb5f-8f23-4d33-b23c-bb84147d7a0d",
  "name": "Projeler",
  "f": {
   "Proje Adı": {
    "id": 6025544,
    "t": 0,
    "req": true
   },
   "Proje Kodu": {
    "id": 6025604,
    "t": 14
   },
   "Ürün / Molekül": {
    "id": 6025605,
    "t": 0
   },
   "Şablon": {
    "id": 6025613,
    "t": 5
   },
   "Proje Yöneticisi": {
    "id": 6025546,
    "t": 6
   },
   "Başlangıç Tarihi": {
    "id": 6025606,
    "t": 2
   },
   "Hedef Bitiş": {
    "id": 6025547,
    "t": 2
   },
   "Durum": {
    "id": 6025548,
    "t": 16,
    "opts": [
     "Taslak",
     "Planlanıyor",
     "Plan Onaylandı (Baseline)",
     "Devam Ediyor",
     "Beklemede",
     "Tamamlandı",
     "İptal"
    ],
    "req": true
   },
   "Plan Durumu": {
    "id": 6025607,
    "t": 4,
    "opts": [
     "Bekliyor",
     "Görevler Oluşturuldu",
     "Hazır"
    ]
   },
   "Baseline No": {
    "id": 6025608,
    "t": 1
   },
   "Baseline Tarihi": {
    "id": 6025609,
    "t": 2
   },
   "Proje Açıklaması": {
    "id": 6025545,
    "t": 0
   }
  }
 },
 "G": {
  "id": "1e9939f4-8af9-42a7-a50d-bc5bd81e0d0f",
  "name": "Görevler",
  "f": {
   "Görev Adı": {
    "id": 6025557,
    "t": 0,
    "req": true
   },
   "WBS No": {
    "id": 6025614,
    "t": 1
   },
   "Tür": {
    "id": 6025615,
    "t": 4,
    "opts": [
     "Faz",
     "Alt Faz",
     "Görev",
     "Alt Görev",
     "Kilometre Taşı"
    ]
   },
   "Proje": {
    "id": 6025632,
    "t": 5
   },
   "Sorumlu Departman": {
    "id": 6025633,
    "t": 5
   },
   "Sorumlu": {
    "id": 6025559,
    "t": 6
   },
   "Onaylayıcı": {
    "id": 6025620,
    "t": 6
   },
   "Başlangıç": {
    "id": 6025616,
    "t": 2
   },
   "Bitiş": {
    "id": 6025560,
    "t": 2
   },
   "Süre (gün)": {
    "id": 6025656,
    "t": 1
   },
   "Durum": {
    "id": 6025561,
    "t": 16,
    "opts": [
     "Başlamadı",
     "Başlayabilir",
     "Devam Ediyor",
     "Onay Bekliyor",
     "Revizyon Gerekli",
     "Beklemede",
     "Tamamlandı",
     "İptal"
    ],
    "req": true
   },
   "% Tamamlanma": {
    "id": 6025617,
    "t": 1
   },
   "Kilometre Taşı": {
    "id": 6025618,
    "t": 3
   },
   "Onay Gerekli": {
    "id": 6025619,
    "t": 3
   },
   "Onay Durumu": {
    "id": 6025621,
    "t": 4,
    "opts": [
     "Gerekmiyor",
     "Bekliyor",
     "Onaylandı",
     "Reddedildi"
    ]
   },
   "Son Onay Notu": {
    "id": 6025622,
    "t": 0
   },
   "Gerçekleşen Başlangıç": {
    "id": 6025623,
    "t": 2
   },
   "Gerçekleşen Bitiş": {
    "id": 6025624,
    "t": 2
   },
   "Baseline Başlangıç": {
    "id": 6025625,
    "t": 2
   },
   "Baseline Bitiş": {
    "id": 6025626,
    "t": 2
   },
   "Sapma (gün)": {
    "id": 6025657,
    "t": 1
   },
   "Gecikmede": {
    "id": 6025627,
    "t": 3
   },
   "Kapalı": {
    "id": 6025629,
    "t": 1
   },
   "Açık Öncül Sayısı": {
    "id": 6025663,
    "t": 1
   },
   "Öncüller": {
    "id": 6025653,
    "t": 21
   },
   "Üst Görev": {
    "id": 6025562,
    "t": 5
   },
   "Notlar": {
    "id": 6025630,
    "t": 0
   },
   "Dokümanlar": {
    "id": 6025631,
    "t": 9
   },
   "Açıklama": {
    "id": 6025558,
    "t": 0
   },
   "Proje Yöneticisi": {
    "id": 6025658,
    "t": 6
   }
  }
 },
 "K": {
  "id": "cb5ea28c-930d-4e48-9703-c402f159b265",
  "name": "Görev Kütüphanesi",
  "f": {
   "Görev Adı": {
    "id": 6025531,
    "t": 0,
    "req": true
   },
   "WBS No": {
    "id": 6025593,
    "t": 1
   },
   "Tür": {
    "id": 6025594,
    "t": 4,
    "opts": [
     "Faz",
     "Alt Faz",
     "Görev",
     "Alt Görev",
     "Kilometre Taşı"
    ]
   },
   "Şablonlar": {
    "id": 6025602,
    "t": 5
   },
   "Sorumlu Departman": {
    "id": 6025603,
    "t": 5
   },
   "Başlangıç": {
    "id": 6025595,
    "t": 2
   },
   "Bitiş": {
    "id": 6025534,
    "t": 2
   },
   "Süre (gün)": {
    "id": 6025654,
    "t": 1
   },
   "Başlangıç Ofseti (gün)": {
    "id": 6025655,
    "t": 1
   },
   "Öncüller": {
    "id": 6025652,
    "t": 21
   },
   "Üst Öğe": {
    "id": 6025536,
    "t": 5
   },
   "Kilometre Taşı": {
    "id": 6025597,
    "t": 3
   },
   "Onay Gerekli": {
    "id": 6025598,
    "t": 3
   },
   "Varsayım": {
    "id": 6025601,
    "t": 3
   },
   "Kabul Kriteri": {
    "id": 6025600,
    "t": 0
   }
  }
 },
 "S": {
  "id": "10e4991b-5317-4915-87e5-f788efa80753",
  "name": "Proje Şablonları",
  "f": {
   "Şablon": {
    "id": 6025524,
    "t": 0,
    "req": true
   },
   "Açıklama": {
    "id": 6025591,
    "t": 0
   },
   "Aktif": {
    "id": 6025592,
    "t": 3
   },
   "Toplam Süre (gün)": {
    "id": 6025671,
    "t": 1
   }
  }
 }
};

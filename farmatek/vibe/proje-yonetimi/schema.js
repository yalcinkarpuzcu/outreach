/* Proje Yönetimi — canlı şema keşfinden üretildi (farmatek.workiom.com). Elle düzenlemeyin; sema_uret2.py ile yenileyin. */
const SCHEMA = {
 "APP": {
  "id": "31c9d231-36d4-451d-b138-5010bdc357d8",
  "name": "Proje Yönetimi"
 },
 "P": {
  "id": "db69522d-db16-42c9-bfb5-c160cb319dcd",
  "name": "Projeler",
  "f": {
   "Proje Adı": {
    "id": 6025748,
    "t": 0,
    "req": true
   },
   "Proje Kodu": {
    "id": 6025830,
    "t": 14
   },
   "Ürün / Molekül": {
    "id": 6025831,
    "t": 0
   },
   "Başlangıç Tarihi": {
    "id": 6025832,
    "t": 2
   },
   "Plan Durumu": {
    "id": 6025833,
    "t": 4,
    "opts": [
     "Bekliyor",
     "Fazlar Oluşturuldu",
     "Görevler Oluşturuldu",
     "Öncüller Bağlandı",
     "Hazır"
    ]
   },
   "Baseline No": {
    "id": 6025834,
    "t": 1
   },
   "Baseline Tarihi": {
    "id": 6025835,
    "t": 2
   },
   "Proje Ekibi": {
    "id": 6025836,
    "t": 18
   },
   "Dokümanlar": {
    "id": 6025837,
    "t": 9
   },
   "Şablon": {
    "id": 6025838,
    "t": 5
   },
   "Şablon Süresi": {
    "id": 6025901,
    "t": 1,
    "ro": true
   },
   "Proje Açıklaması": {
    "id": 6025749,
    "t": 0
   },
   "Proje Yöneticisi": {
    "id": 6025750,
    "t": 6
   },
   "Hedef Bitiş": {
    "id": 6025751,
    "t": 2
   },
   "Durum": {
    "id": 6025752,
    "t": 16,
    "req": true,
    "opts": [
     "Taslak",
     "Planlanıyor",
     "Plan Onaylandı (Baseline)",
     "Devam Ediyor",
     "Beklemede",
     "Tamamlandı",
     "İptal"
    ],
    "def": "Taslak"
   },
   "Parent Task": {
    "id": 6025753,
    "t": 5
   },
   "Subtasks": {
    "id": 6025754,
    "t": 5
   }
  }
 },
 "F": {
  "id": "52840fbc-1576-4a1a-8e97-62fd2a99457f",
  "name": "Fazlar",
  "f": {
   "Faz": {
    "id": 6025761,
    "t": 0,
    "req": true
   },
   "Sıra": {
    "id": 6025839,
    "t": 1
   },
   "Başlangıç": {
    "id": 6025840,
    "t": 2
   },
   "Bitiş": {
    "id": 6025841,
    "t": 2
   },
   "Baseline Başlangıç": {
    "id": 6025842,
    "t": 2
   },
   "Baseline Bitiş": {
    "id": 6025843,
    "t": 2
   },
   "Açıklama": {
    "id": 6025844,
    "t": 0
   },
   "Proje": {
    "id": 6025845,
    "t": 5
   },
   "Faz Şablonu": {
    "id": 6025846,
    "t": 5
   },
   "Süre (gün)": {
    "id": 6025897,
    "t": 1,
    "ro": true
   }
  }
 },
 "G": {
  "id": "c2611685-3a96-4035-a3b9-6e514d12ed19",
  "name": "Görevler",
  "f": {
   "Görev Adı": {
    "id": 6025768,
    "t": 0,
    "req": true
   },
   "WBS No": {
    "id": 6025847,
    "t": 1
   },
   "Başlangıç": {
    "id": 6025848,
    "t": 2
   },
   "% Tamamlanma": {
    "id": 6025849,
    "t": 1
   },
   "Onay Gerekli": {
    "id": 6025850,
    "t": 3
   },
   "Onaylayıcı": {
    "id": 6025851,
    "t": 6
   },
   "Onay Durumu": {
    "id": 6025852,
    "t": 4,
    "opts": [
     "Gerekmiyor",
     "Bekliyor",
     "Onaylandı",
     "Reddedildi"
    ]
   },
   "Gerçekleşen Başlangıç": {
    "id": 6025853,
    "t": 2
   },
   "Gerçekleşen Bitiş": {
    "id": 6025854,
    "t": 2
   },
   "Baseline Başlangıç": {
    "id": 6025855,
    "t": 2
   },
   "Baseline Bitiş": {
    "id": 6025856,
    "t": 2
   },
   "Gecikmede": {
    "id": 6025857,
    "t": 3
   },
   "Kapalı": {
    "id": 6025858,
    "t": 1
   },
   "Notlar": {
    "id": 6025859,
    "t": 0
   },
   "Dokümanlar": {
    "id": 6025860,
    "t": 9
   },
   "Proje": {
    "id": 6025861,
    "t": 5
   },
   "Faz": {
    "id": 6025862,
    "t": 5
   },
   "Sorumlu Departman": {
    "id": 6025863,
    "t": 5
   },
   "Şablon Öğesi": {
    "id": 6025864,
    "t": 5
   },
   "Öncül Kayıtları": {
    "id": 6025865,
    "t": 5
   },
   "Öncüller": {
    "id": 6025892,
    "t": 21
   },
   "Süre (gün)": {
    "id": 6025895,
    "t": 1,
    "ro": true
   },
   "Sapma (gün)": {
    "id": 6025896,
    "t": 1,
    "ro": true
   },
   "Proje Yöneticisi": {
    "id": 6025899,
    "t": 6,
    "ro": true
   },
   "Öncül Sayısı": {
    "id": 6025902,
    "t": 1,
    "ro": true
   },
   "Kapanan Öncül": {
    "id": 6025903,
    "t": 1,
    "ro": true
   },
   "Açık Öncül Sayısı": {
    "id": 6025904,
    "t": 1,
    "ro": true
   },
   "Açıklama": {
    "id": 6025769,
    "t": 0
   },
   "Sorumlu": {
    "id": 6025770,
    "t": 6
   },
   "Bitiş": {
    "id": 6025771,
    "t": 2
   },
   "Durum": {
    "id": 6025772,
    "t": 16,
    "req": true,
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
    "def": "Başlamadı"
   },
   "Parent Task": {
    "id": 6025773,
    "t": 5
   },
   "Subtasks": {
    "id": 6025774,
    "t": 5
   }
  }
 },
 "K": {
  "id": "469706bc-53ae-47f3-b746-5a8c817ba7f1",
  "name": "Kilometre Taşları",
  "f": {
   "Kilometre Taşı": {
    "id": 6025781,
    "t": 0,
    "req": true
   },
   "Hedef Tarih": {
    "id": 6025866,
    "t": 2
   },
   "Gerçekleşen Tarih": {
    "id": 6025867,
    "t": 2
   },
   "Baseline Tarih": {
    "id": 6025868,
    "t": 2
   },
   "KT Durumu": {
    "id": 6025869,
    "t": 4,
    "opts": [
     "Bekleniyor",
     "Ulaşıldı",
     "Gecikti"
    ]
   },
   "Kritik": {
    "id": 6025870,
    "t": 3
   },
   "Açıklama": {
    "id": 6025871,
    "t": 0
   },
   "Proje": {
    "id": 6025872,
    "t": 5
   },
   "Faz": {
    "id": 6025873,
    "t": 5
   },
   "KT Şablonu": {
    "id": 6025874,
    "t": 5
   },
   "Bağlı Görevler": {
    "id": 6025875,
    "t": 5
   },
   "Sapma (gün)": {
    "id": 6025898,
    "t": 1,
    "ro": true
   },
   "Proje Yöneticisi": {
    "id": 6025900,
    "t": 6,
    "ro": true
   },
   "Bağlı Görev Sayısı": {
    "id": 6025905,
    "t": 1,
    "ro": true
   },
   "Kapanan Bağlı Görev": {
    "id": 6025906,
    "t": 1,
    "ro": true
   },
   "Açık Bağlı Görev": {
    "id": 6025907,
    "t": 1,
    "ro": true
   }
  }
 },
 "O": {
  "id": "b5d75c26-1fde-419c-a088-afe75a509076",
  "name": "Onay Geçmişi",
  "f": {
   "Başlık": {
    "id": 6025788,
    "t": 0,
    "req": true
   },
   "Kayıt No": {
    "id": 6025876,
    "t": 14
   },
   "Karar": {
    "id": 6025877,
    "t": 4,
    "opts": [
     "Onaylandı",
     "Reddedildi"
    ]
   },
   "Onaylayan": {
    "id": 6025878,
    "t": 6
   },
   "Tarih": {
    "id": 6025879,
    "t": 2
   },
   "Not": {
    "id": 6025880,
    "t": 0
   },
   "Görev": {
    "id": 6025881,
    "t": 5
   },
   "Proje": {
    "id": 6025882,
    "t": 5
   }
  }
 },
 "B": {
  "id": "dee3fde4-6bba-4c0e-9d71-d5570b795cea",
  "name": "Baseline Arşivi",
  "f": {
   "Başlık": {
    "id": 6025795,
    "t": 0,
    "req": true
   },
   "Kayıt No": {
    "id": 6025883,
    "t": 14
   },
   "Baseline No": {
    "id": 6025884,
    "t": 1
   },
   "Baseline Tarihi": {
    "id": 6025885,
    "t": 2
   },
   "Planlanan Başlangıç": {
    "id": 6025886,
    "t": 2
   },
   "Planlanan Bitiş": {
    "id": 6025887,
    "t": 2
   },
   "Proje": {
    "id": 6025888,
    "t": 5
   },
   "Görev": {
    "id": 6025889,
    "t": 5
   }
  }
 },
 "D": {
  "id": "c28642f3-3f79-430b-8750-43bcb3fef816",
  "name": "Departmanlar",
  "f": {
   "Departman": {
    "id": 6025707,
    "t": 0,
    "req": true
   },
   "Kod": {
    "id": 6025802,
    "t": 0
   },
   "Departman Yöneticisi": {
    "id": 6025803,
    "t": 6
   },
   "Onaylayıcı": {
    "id": 6025804,
    "t": 6
   },
   "Ekip Üyeleri": {
    "id": 6025805,
    "t": 18
   },
   "Açıklama": {
    "id": 6025806,
    "t": 0
   }
  }
 },
 "S": {
  "id": "f10d73f0-6889-4710-b4cd-1e58307464f6",
  "name": "Proje Şablonları",
  "f": {
   "Şablon": {
    "id": 6025714,
    "t": 0,
    "req": true
   },
   "Açıklama": {
    "id": 6025807,
    "t": 0
   },
   "Aktif": {
    "id": 6025808,
    "t": 3
   },
   "Toplam Süre (gün)": {
    "id": 6025809,
    "t": 1
   }
  }
 },
 "GK": {
  "id": "f280153b-a63b-4e50-bfe0-fc92190f1f73",
  "name": "Görev Kütüphanesi",
  "f": {
   "Görev Adı": {
    "id": 6025735,
    "t": 0,
    "req": true
   },
   "WBS No": {
    "id": 6025820,
    "t": 1
   },
   "Başlangıç": {
    "id": 6025821,
    "t": 2
   },
   "Referans Tarih": {
    "id": 6025822,
    "t": 2
   },
   "Onay Gerekli": {
    "id": 6025823,
    "t": 3
   },
   "Kabul Kriteri": {
    "id": 6025824,
    "t": 0
   },
   "Varsayım": {
    "id": 6025825,
    "t": 3
   },
   "Faz": {
    "id": 6025826,
    "t": 5
   },
   "Kilometre Taşları": {
    "id": 6025827,
    "t": 5
   },
   "Şablonlar": {
    "id": 6025828,
    "t": 5
   },
   "Sorumlu Departman": {
    "id": 6025829,
    "t": 5
   },
   "Departman Onaylayıcı": {
    "id": 6025890,
    "t": 6,
    "ro": true
   },
   "Öncüller": {
    "id": 6025891,
    "t": 21
   },
   "Süre (gün)": {
    "id": 6025893,
    "t": 1,
    "ro": true
   },
   "Başlangıç Ofseti (gün)": {
    "id": 6025894,
    "t": 1,
    "ro": true
   },
   "Açıklama": {
    "id": 6025736,
    "t": 0
   },
   "Varsayılan Sorumlu": {
    "id": 6025737,
    "t": 6
   },
   "Bitiş": {
    "id": 6025738,
    "t": 2
   },
   "Durum": {
    "id": 6025739,
    "t": 16,
    "req": true,
    "opts": [
     "Yayında",
     "Taslak",
     "Arşiv"
    ],
    "def": "Yayında"
   },
   "Parent Task": {
    "id": 6025740,
    "t": 5
   },
   "Subtasks": {
    "id": 6025741,
    "t": 5
   }
  }
 },
 "FK": {
  "id": "03c29a99-ecff-4574-9df6-a5eca95cf6cd",
  "name": "Faz Kütüphanesi",
  "f": {
   "Faz": {
    "id": 6025721,
    "t": 0,
    "req": true
   },
   "Sıra": {
    "id": 6025810,
    "t": 1
   },
   "Başlangıç Ofseti (gün)": {
    "id": 6025811,
    "t": 1
   },
   "Süre (gün)": {
    "id": 6025812,
    "t": 1
   },
   "Açıklama": {
    "id": 6025813,
    "t": 0
   },
   "Şablonlar": {
    "id": 6025814,
    "t": 5
   }
  }
 },
 "KK": {
  "id": "6810b7c5-9ab5-4eb3-8eba-f8b57a94d1e2",
  "name": "Kilometre Taşı Kütüphanesi",
  "f": {
   "Kilometre Taşı": {
    "id": 6025728,
    "t": 0,
    "req": true
   },
   "Gün Ofseti": {
    "id": 6025815,
    "t": 1
   },
   "Kritik": {
    "id": 6025816,
    "t": 3
   },
   "Açıklama": {
    "id": 6025817,
    "t": 0
   },
   "Faz": {
    "id": 6025818,
    "t": 5
   },
   "Şablonlar": {
    "id": 6025819,
    "t": 5
   }
  }
 }
};

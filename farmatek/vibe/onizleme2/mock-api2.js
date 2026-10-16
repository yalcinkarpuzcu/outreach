/* ÖNİZLEME / TEST İSKELESİ — gerçek pakete GİRMEZ.
   core.js'ten sonra yüklenir: oturum ve API tabanını taklit eder, fetch'i yakalar, SCHEMA alan id'leriyle
   sentetik kayıtlar üretir ve Workiom otomasyonlarını (plan kurulumu, öncül kilidi, onay, ardılları açma,
   kilometre taşına ulaşma, baseline, bildirimler) hafifçe taklit eder. */
"use strict";
(function () {
  workiomHeaders = () => ({ "Content-Type": "application/json", "Authorization": "Bearer preview" });   // eslint-disable-line no-global-assign
  apiBase = () => Promise.resolve("https://onizleme.invalid");                                         // eslint-disable-line no-global-assign
  const USERS = [
    { id: 900001, name: "Demo", surname: "Kullanıcı", emailAddress: "demo@ornek.com", isActive: true },
    { id: 900002, name: "Analitik", surname: "Uzmanı", emailAddress: "analitik@ornek.com", isActive: true },
    { id: 900003, name: "Formülasyon", surname: "Uzmanı", emailAddress: "formul@ornek.com", isActive: true },
    { id: 900004, name: "Ruhsat", surname: "Sorumlusu", emailAddress: "ruhsat@ornek.com", isActive: true }
  ];
  const U = id => { const u = USERS.find(x => x.id === id); return { id: String(u.id), fullname: u.name + " " + u.surname, name: u.name, surname: u.surname, emailAddress: u.emailAddress }; };
  const uByEmail = e => { const u = USERS.find(x => x.emailAddress === e); return u ? U(u.id) : null; };
  const ME = U(900001);
  const F = (l, n) => String(SCHEMA[l].f[n].id);
  const opt = label => ({ id: "o-" + label, label });
  let seq = 0;
  const oid = () => "m" + String(++seq).padStart(23, "0");
  const iso = day => new Date(day * 864e5 - 3 * 3600e3).toISOString().replace(".000", "");
  const dayOf = s => { if (!s) return null; const d = new Date(s); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5); };
  const tday = () => { const d = new Date(); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5); };
  const KEYS = ["P", "F", "G", "K", "O", "B", "D", "S", "GK", "FK", "KK"];
  const store = Object.fromEntries(KEYS.map(k => [k, []]));
  const keyOf = id => KEYS.find(k => SCHEMA[k].id === id);
  const lnk = (rec, l, nameField) => ({ _id: rec._id, label: rec[F(l, nameField)] });
  const NOTES = [], HIST = [], COMMENTS = {}, APPROVALS = {};
  const notify = (userId, msg, l, rec) => NOTES.unshift({ id: "n" + (++seq), state: 0, notification: { appId: SCHEMA.APP.id, listId: SCHEMA[l].id, recordId: rec._id, creationTime: new Date().toISOString(),
    data: { properties: { notificationMessage: msg, listName: SCHEMA[l].name, appId: SCHEMA.APP.id, recordTitle: "" } } }, userId });
  const hist = (l, rec, changes, prev, auto) => HIST.unshift({ date: new Date().toISOString(), username: auto ? "Otomasyon" : "Demo Kullanıcı", automationId: auto ? 1 : null, listName: SCHEMA[l].name,
    itemName: rec[Object.entries(SCHEMA[l].f).find(([, f]) => f.pri || (f.t === 0 && f.req))?.[1].id] || "", record: changes, previousRecord: prev || {}, action: prev ? 1 : 0, isVisible: true, recordId: rec._id });

  /* ── referans veriler ─────────────────────────────────────────── */
  const DEPTS = {};
  ["Proje Yönetimi", "Formülasyon Geliştirme", "Analitik Metot Geliştirme", "Ruhsat", "Kalite Güvence"].forEach((d, i) => {
    const r = { _id: oid(), [F("D", "Departman")]: d, [F("D", "Kod")]: ["PM", "FOR", "ANA", "RUH", "KG"][i],
      [F("D", "Departman Yöneticisi")]: U([900001, 900003, 900002, 900004, 900001][i]), [F("D", "Onaylayıcı")]: U(900001), [F("D", "Ekip Üyeleri")]: [ME, U(900002)] };
    store.D.push(r); DEPTS[d] = r;
  });
  const REF = Math.round(Date.UTC(2026, 0, 1) / 864e5);
  const TPL = {};
  Object.entries(MOCK2.sablonlar).forEach(([s, nos]) => {
    const r = { _id: oid(), [F("S", "Şablon")]: s, [F("S", "Aktif")]: true, [F("S", "Toplam Süre (gün)")]: Math.max(...MOCK2.gorevler.filter(g => nos.includes(g.no)).map(g => g.e)),
      [F("S", "Açıklama")]: s === "Yeni Ürün" ? "Yeni jenerik ürün geliştirme: API seçimi → formülasyon → validasyon → BE → ruhsat." : "Ruhsatlı ürün için alternatif API kaynağı." };
    store.S.push(r); TPL[s] = r;
  });
  const tplsFor = nos => Object.entries(MOCK2.sablonlar).filter(([, ns]) => nos.some(n => ns.includes(n))).map(([s]) => lnk(TPL[s], "S", "Şablon"));
  const FK = {}, KK = {}, GK = {};
  MOCK2.fazlar.forEach(f => {
    const nos = MOCK2.gorevler.filter(g => g.faz === f.kod).map(g => g.no);
    const r = { _id: oid(), [F("FK", "Faz")]: f.ad, [F("FK", "Sıra")]: f.sira, [F("FK", "Başlangıç Ofseti (gün)")]: f.s, [F("FK", "Süre (gün)")]: f.e - f.s, [F("FK", "Şablonlar")]: tplsFor(nos) };
    store.FK.push(r); FK[f.kod] = r;
  });
  MOCK2.kt.forEach(k => {
    const r = { _id: oid(), [F("KK", "Kilometre Taşı")]: k.ad, [F("KK", "Gün Ofseti")]: k.gun, [F("KK", "Kritik")]: k.kritik, [F("KK", "Faz")]: [lnk(FK[k.faz], "FK", "Faz")], [F("KK", "Şablonlar")]: tplsFor(k.bagli) };
    store.KK.push(r); KK[k.kod] = r;
  });
  MOCK2.gorevler.forEach(g => {
    const r = { _id: oid(), [F("GK", "Görev Adı")]: g.ad, [F("GK", "WBS No")]: g.no, [F("GK", "Başlangıç")]: iso(REF + g.s), [F("GK", "Bitiş")]: iso(REF + g.e), [F("GK", "Referans Tarih")]: iso(REF),
      [F("GK", "Onay Gerekli")]: g.onay, [F("GK", "Varsayım")]: g.vars, [F("GK", "Faz")]: [lnk(FK[g.faz], "FK", "Faz")], [F("GK", "Sorumlu Departman")]: [lnk(DEPTS[g.dep], "D", "Departman")],
      [F("GK", "Şablonlar")]: Object.entries(MOCK2.sablonlar).filter(([, ns]) => ns.includes(g.no)).map(([s]) => lnk(TPL[s], "S", "Şablon")),
      [F("GK", "Kilometre Taşları")]: MOCK2.kt.filter(k => k.bagli.includes(g.no)).map(k => lnk(KK[k.kod], "KK", "Kilometre Taşı")),
      [F("GK", "Durum")]: opt("Yayında") };
    store.GK.push(r); GK[g.no] = r;
  });
  MOCK2.gorevler.forEach(g => { GK[g.no][F("GK", "Öncüller")] = g.onc.map(p => ({ _id: GK[p]._id, label: GK[p][F("GK", "Görev Adı")], dependencyType: 1 })); });

  /* ── proje kurulumu (A1 → A2c taklidi) ────────────────────────── */
  const OWN = { "Proje Yönetimi": 900001, "Formülasyon Geliştirme": 900001, "Analitik Metot Geliştirme": 900002, "Ruhsat": 900004, "Kalite Güvence": 900001 };
  function buildPlan(p) {
    const tplId = (p[F("P", "Şablon")] || [])[0]?._id;
    const tplName = Object.keys(TPL).find(s => TPL[s]._id === tplId) || "Yeni Ürün";
    const nos = MOCK2.sablonlar[tplName];
    const start = dayOf(p[F("P", "Başlangıç Tarihi")]);
    const pl = lnk(p, "P", "Proje Adı");
    const fz = {}, gs = {};
    MOCK2.fazlar.forEach(f => {
      if (!MOCK2.gorevler.some(g => g.faz === f.kod && nos.includes(g.no))) return;
      const r = { _id: oid(), [F("F", "Faz")]: f.ad, [F("F", "Sıra")]: f.sira, [F("F", "Başlangıç")]: iso(start + f.s), [F("F", "Bitiş")]: iso(start + f.e), [F("F", "Proje")]: [pl], [F("F", "Faz Şablonu")]: [lnk(FK[f.kod], "FK", "Faz")] };
      store.F.push(r); fz[f.kod] = r;
    });
    MOCK2.gorevler.filter(g => nos.includes(g.no)).forEach(g => {
      const r = { _id: oid(), [F("G", "Görev Adı")]: g.ad, [F("G", "WBS No")]: g.no, [F("G", "Proje")]: [pl], [F("G", "Faz")]: [lnk(fz[g.faz], "F", "Faz")],
        [F("G", "Başlangıç")]: iso(start + g.s), [F("G", "Bitiş")]: iso(start + g.e), [F("G", "Durum")]: opt("Başlamadı"), [F("G", "Kapalı")]: 0, [F("G", "% Tamamlanma")]: 0,
        [F("G", "Onay Gerekli")]: g.onay, [F("G", "Sorumlu")]: U(OWN[g.dep]), [F("G", "Onaylayıcı")]: ME, [F("G", "Sorumlu Departman")]: [lnk(DEPTS[g.dep], "D", "Departman")],
        [F("G", "Şablon Öğesi")]: [lnk(GK[g.no], "GK", "Görev Adı")], [F("G", "Proje Yöneticisi")]: p[F("P", "Proje Yöneticisi")] };
      store.G.push(r); gs[g.no] = r;
    });
    MOCK2.gorevler.filter(g => nos.includes(g.no)).forEach(g => {
      const ps = g.onc.filter(n => gs[n]);
      gs[g.no][F("G", "Öncüller")] = ps.map(n => ({ _id: gs[n]._id, label: gs[n][F("G", "Görev Adı")], dependencyType: 1 }));
      gs[g.no][F("G", "Öncül Kayıtları")] = ps.map(n => lnk(gs[n], "G", "Görev Adı"));
    });
    MOCK2.kt.forEach(k => {
      const linked = k.bagli.filter(n => gs[n]);
      if (!linked.length) return;
      store.K.push({ _id: oid(), [F("K", "Kilometre Taşı")]: k.ad, [F("K", "Proje")]: [pl], [F("K", "Faz")]: fz[k.faz] ? [lnk(fz[k.faz], "F", "Faz")] : [],
        [F("K", "Hedef Tarih")]: iso(start + k.gun), [F("K", "KT Durumu")]: opt("Bekleniyor"), [F("K", "Kritik")]: k.kritik, [F("K", "KT Şablonu")]: [lnk(KK[k.kod], "KK", "Kilometre Taşı")],
        [F("K", "Bağlı Görevler")]: linked.map(n => lnk(gs[n], "G", "Görev Adı")), [F("K", "Proje Yöneticisi")]: p[F("P", "Proje Yöneticisi")] });
    });
    unlock(Object.values(gs));
    return gs;
  }
  function makeProject(name, tpl, startDay, extra) {
    const p = { _id: oid(), [F("P", "Proje Adı")]: name, [F("P", "Proje Kodu")]: store.P.length + 1, [F("P", "Şablon")]: [lnk(TPL[tpl], "S", "Şablon")],
      [F("P", "Proje Yöneticisi")]: ME, [F("P", "Başlangıç Tarihi")]: iso(startDay), [F("P", "Hedef Bitiş")]: iso(startDay + 1006),
      [F("P", "Durum")]: opt(extra.durum || "Devam Ediyor"), [F("P", "Plan Durumu")]: opt("Hazır"), [F("P", "Ürün / Molekül")]: extra.urun || "" };
    store.P.push(p);
    return [p, buildPlan(p)];
  }
  const closeTask = (r, day) => { r[F("G", "Durum")] = opt("Tamamlandı"); r[F("G", "Kapalı")] = 1; r[F("G", "% Tamamlanma")] = 100;
    r[F("G", "Gerçekleşen Başlangıç")] = r[F("G", "Başlangıç")]; r[F("G", "Gerçekleşen Bitiş")] = iso(day ?? dayOf(r[F("G", "Bitiş")])); };
  const t0 = tday();
  // demo 1: 140 gün önce başlamış, baseline alınmış, bazı görevler bitmiş/gecikmiş
  const [p1, g1] = makeProject("Calcium Carbonate 500 mg Film Tablet", "Yeni Ürün", t0 - 140, { urun: "Kalsiyum karbonat" });
  Object.values(g1).forEach(r => { r[F("G", "Baseline Başlangıç")] = r[F("G", "Başlangıç")]; r[F("G", "Baseline Bitiş")] = r[F("G", "Bitiş")]; });
  store.F.filter(f => f[F("F", "Proje")][0]._id === p1._id).forEach(f => { f[F("F", "Baseline Başlangıç")] = f[F("F", "Başlangıç")]; f[F("F", "Baseline Bitiş")] = f[F("F", "Bitiş")]; });
  store.K.filter(k => k[F("K", "Proje")][0]._id === p1._id).forEach(k => { k[F("K", "Baseline Tarih")] = k[F("K", "Hedef Tarih")]; });
  p1[F("P", "Baseline No")] = 1; p1[F("P", "Baseline Tarihi")] = iso(t0 - 138);
  [2, 3, 5, 6, 7, 8, 4, 11].forEach(n => g1[n] && closeTask(g1[n]));
  [9, 10, 12, 13, 14].forEach(n => { const r = g1[n]; r[F("G", "Durum")] = opt("Devam Ediyor"); r[F("G", "% Tamamlanma")] = n === 9 ? 70 : 40; r[F("G", "Gerçekleşen Başlangıç")] = r[F("G", "Başlangıç")]; });
  // 9 numarayı geciktir (bitişi geçti)
  g1[9][F("G", "Bitiş")] = iso(t0 - 6); g1[9][F("G", "Notlar")] = "Tedarikçiden COA bekleniyor.";
  g1[12][F("G", "Durum")] = opt("Onay Bekliyor"); g1[12][F("G", "Onay Gerekli")] = true; g1[12][F("G", "Onay Durumu")] = opt("Bekliyor"); g1[12][F("G", "% Tamamlanma")] = 100;
  APPROVALS[g1[12]._id] = { requestId: 777001, status: 0, usersIds: [900001] };
  // demo 2: yeni başlamış alternatif kaynak
  const [p2, g2] = makeProject("Metformin 1000 mg — Alternatif API", "Alternatif Kaynak", t0 - 12, { urun: "Metformin HCl", durum: "Planlanıyor" });
  closeTask(g2[2], t0 - 11);
  unlock(Object.values(g1)); unlock(Object.values(g2)); reachMilestones();
  void p2;
  store.O.push({ _id: oid(), [F("O", "Başlık")]: "Onaylandı: API Kaynağı Belirlenmesi", [F("O", "Karar")]: opt("Onaylandı"), [F("O", "Onaylayan")]: ME, [F("O", "Tarih")]: iso(t0 - 100),
    [F("O", "Görev")]: [lnk(g1[3], "G", "Görev Adı")], [F("O", "Proje")]: [lnk(p1, "P", "Proje Adı")], [F("O", "Kayıt No")]: 1 });
  notify(900001, "▶️ Seçilen API'nin Temini başlayabilir: tüm öncülleri tamamlandı.", "G", g1[9]);
  notify(900001, "⏰ Geciken görev: Seçilen API'nin Temini · Calcium Carbonate 500 mg Film Tablet", "G", g1[9]);
  notify(900001, "🏁 Kilometre taşına ulaşıldı: Proje Başlatıldı · Calcium Carbonate 500 mg Film Tablet", "K", store.K[0]);
  NOTES[2].state = 1;

  /* ── hesaplanan alanlar ───────────────────────────────────────── */
  function computed(l, r) {
    const out = { ...r };
    if (l === "G") {
      const pre = (r[F("G", "Öncül Kayıtları")] || []).map(x => store.G.find(g => g._id === x._id)).filter(Boolean);
      out[F("G", "Öncül Sayısı")] = pre.length;
      out[F("G", "Kapanan Öncül")] = pre.filter(g => g[F("G", "Kapalı")] === 1).length;
      out[F("G", "Açık Öncül Sayısı")] = out[F("G", "Öncül Sayısı")] - out[F("G", "Kapanan Öncül")];
      const be = dayOf(r[F("G", "Baseline Bitiş")]);
      out[F("G", "Sapma (gün)")] = be == null ? 0 : dayOf(r[F("G", "Bitiş")]) - be;
      out[F("G", "Süre (gün)")] = dayOf(r[F("G", "Bitiş")]) - dayOf(r[F("G", "Başlangıç")]);
    }
    if (l === "K") {
      const ls = (r[F("K", "Bağlı Görevler")] || []).map(x => store.G.find(g => g._id === x._id)).filter(Boolean);
      out[F("K", "Bağlı Görev Sayısı")] = ls.length;
      out[F("K", "Kapanan Bağlı Görev")] = ls.filter(g => g[F("G", "Kapalı")] === 1).length;
      out[F("K", "Açık Bağlı Görev")] = ls.length - out[F("K", "Kapanan Bağlı Görev")];
      const b = dayOf(r[F("K", "Baseline Tarih")]);
      out[F("K", "Sapma (gün)")] = b == null ? 0 : dayOf(r[F("K", "Hedef Tarih")]) - b;
    }
    if (l === "GK") {
      out[F("GK", "Süre (gün)")] = dayOf(r[F("GK", "Bitiş")]) - dayOf(r[F("GK", "Başlangıç")]);
      out[F("GK", "Başlangıç Ofseti (gün)")] = dayOf(r[F("GK", "Başlangıç")]) - REF;
    }
    return out;
  }
  function openPreds(g) { return (g[F("G", "Öncül Kayıtları")] || []).map(x => store.G.find(t => t._id === x._id)).filter(t => t && t[F("G", "Kapalı")] !== 1).length; }
  function unlock(list) {
    for (const g of list) if (g[F("G", "Durum")]?.label === "Başlamadı" && (g[F("G", "Öncül Kayıtları")] || []).length && openPreds(g) === 0) {
      g[F("G", "Durum")] = opt("Başlayabilir");
    }
  }
  function reachMilestones() {
    const reached = [];
    for (const k of store.K) {
      const ls = (k[F("K", "Bağlı Görevler")] || []).map(x => store.G.find(g => g._id === x._id)).filter(Boolean);
      const done = ls.length && ls.every(g => g[F("G", "Kapalı")] === 1);
      const st = k[F("K", "KT Durumu")]?.label;
      if (done && st !== "Ulaşıldı") { k[F("K", "KT Durumu")] = opt("Ulaşıldı"); k[F("K", "Gerçekleşen Tarih")] = iso(tday()); reached.push(k); continue; }
      if (!done && st === "Ulaşıldı") k[F("K", "KT Durumu")] = opt("Bekleniyor");
    }
    for (const k of store.K) if (k[F("K", "KT Durumu")]?.label === "Bekleniyor" && dayOf(k[F("K", "Hedef Tarih")]) < tday()) k[F("K", "KT Durumu")] = opt("Gecikti");
    return reached;
  }

  /* ── yazma: değer biçimi dönüşümü + otomasyon taklidi ─────────── */
  function toStored(l, fidStr, val) {
    const f = Object.values(SCHEMA[l].f).find(x => String(x.id) === fidStr);
    if (!f || val == null) return val;
    if (f.t === 4 || f.t === 16) return opt(val);
    if (f.t === 6) return uByEmail(val);
    if (f.t === 18) return (val || []).map(uByEmail).filter(Boolean);
    if (f.t === 5) return (val || []).map(id => { const k = KEYS.find(kk => store[kk].some(r => r._id === id)); const r = k && store[k].find(x => x._id === id); const pri = k && Object.values(SCHEMA[k].f).find(x => x.pri || (x.t === 0 && x.req)); return { _id: id, label: r && pri ? r[pri.id] : id }; });
    if (f.t === 21) return val.map(d => { const g = store.G.find(x => x._id === d._id) || store.GK.find(x => x._id === d._id); return { _id: d._id, dependencyType: d.dependencyType, label: g ? (g[F("G", "Görev Adı")] || g[F("GK", "Görev Adı")]) : "" }; });
    if (f.t === 2) return val && val.length === 10 ? iso(dayOf(val + "T12:00:00")) : val;
    return val;
  }
  function afterUpdate(l, r, payload, prev) {
    const dur = F("G", "Durum");
    if (l === "G" && dur in payload) {
      const st = r[dur].label, name = r[F("G", "Görev Adı")];
      setTimeout(() => {
        if (["Devam Ediyor", "Onay Bekliyor", "Tamamlandı"].includes(st) && openPreds(r) > 0) {
          r[dur] = opt("Başlamadı");
          notify(900001, "⛔ " + name + ": öncül görevler tamamlanmadan başlatılamaz/tamamlanamaz. Açık öncül sayısı: " + openPreds(r), "G", r);
          hist("G", r, { Durum: "Başlamadı" }, { Durum: st }, true); return;
        }
        if (st === "Devam Ediyor") { if (!r[F("G", "Gerçekleşen Başlangıç")]) r[F("G", "Gerçekleşen Başlangıç")] = iso(tday()); r[F("G", "Kapalı")] = 0; }
        if (st === "Onay Bekliyor") {
          if (r[F("G", "Onay Gerekli")]) { r[F("G", "Onay Durumu")] = opt("Bekliyor"); APPROVALS[r._id] = { requestId: 777000 + (++seq), status: 0, usersIds: [900001] }; notify(900001, "✍ Onay talebi: " + name, "G", r); }
          else r[dur] = opt("Tamamlandı");
        }
        if (r[dur].label === "Tamamlandı") {
          if (r[F("G", "Onay Gerekli")] && r[F("G", "Onay Durumu")]?.label !== "Onaylandı") { r[dur] = opt("Onay Bekliyor"); afterUpdate(l, r, { [dur]: 1 }, prev); return; }
          closeTask(r, tday());
          const succ = store.G.filter(g => (g[F("G", "Öncül Kayıtları")] || []).some(x => x._id === r._id));
          for (const s of succ) if (s[dur].label === "Başlamadı" && openPreds(s) === 0) {
            s[dur] = opt("Başlayabilir"); notify(900001, "▶️ " + s[F("G", "Görev Adı")] + " başlayabilir: tüm öncülleri tamamlandı.", "G", s);
            if (!s[F("G", "Sorumlu")]) { s[F("G", "Sorumlu")] = ME; notify(900001, "👤 " + s[F("G", "Görev Adı")] + " sırası geldi ve size atandı.", "G", s); }   // A6c taklidi
          }
          for (const k of reachMilestones()) notify(900001, "🏁 Kilometre taşına ulaşıldı: " + k[F("K", "Kilometre Taşı")], "K", k);
        }
        if (["Revizyon Gerekli", "Beklemede", "Başlamadı", "Başlayabilir"].includes(r[dur].label)) { r[F("G", "Kapalı")] = 0; reachMilestones(); }
      }, 900);
    }
    if (l === "P" && F("P", "Durum") in payload && r[F("P", "Durum")].label === "Plan Onaylandı (Baseline)") {
      setTimeout(() => {
        const pid = r._id, no = (Number(r[F("P", "Baseline No")]) || 0) + 1;
        store.G.filter(g => g[F("G", "Proje")]?.[0]?._id === pid).forEach(g => { g[F("G", "Baseline Başlangıç")] = g[F("G", "Başlangıç")]; g[F("G", "Baseline Bitiş")] = g[F("G", "Bitiş")]; });
        store.F.filter(g => g[F("F", "Proje")]?.[0]?._id === pid).forEach(g => { g[F("F", "Baseline Başlangıç")] = g[F("F", "Başlangıç")]; g[F("F", "Baseline Bitiş")] = g[F("F", "Bitiş")]; });
        store.K.filter(g => g[F("K", "Proje")]?.[0]?._id === pid).forEach(g => { g[F("K", "Baseline Tarih")] = g[F("K", "Hedef Tarih")]; });
        r[F("P", "Baseline No")] = no; r[F("P", "Baseline Tarihi")] = iso(tday()); r[F("P", "Durum")] = opt("Devam Ediyor");
        notify(900001, "📌 Baseline alındı: " + r[F("P", "Proje Adı")], "P", r);
      }, 1500);
    }
  }
  function afterCreate(l, r) {
    if (l === "P" && r[F("P", "Şablon")]?.length && r[F("P", "Başlangıç Tarihi")]) {
      r[F("P", "Durum")] = opt("Planlanıyor"); r[F("P", "Plan Durumu")] = opt("Bekliyor"); r[F("P", "Proje Kodu")] = store.P.length;
      const steps = ["Fazlar Oluşturuldu", "Görevler Oluşturuldu", "Öncüller Bağlandı", "Hazır"];
      steps.forEach((s, i) => setTimeout(() => {
        if (s === "Hazır") { buildPlan(r); notify(900001, "Proje planı hazır: " + r[F("P", "Proje Adı")] + ". Fazlar, görevler, öncüller ve kilometre taşları oluşturuldu.", "P", r); }
        r[F("P", "Plan Durumu")] = opt(s);
      }, 1800 * (i + 1)));
    }
    if (l === "G") { r[F("G", "Kapalı")] = r[F("G", "Kapalı")] ?? 0; unlock([r]); }
  }

  /* ── fetch yakalayıcı ─────────────────────────────────────────── */
  const ok = result => new Response(JSON.stringify({ success: true, result, error: null, unAuthorizedRequest: false }), { status: 200, headers: { "Content-Type": "application/json" } });
  const fail = msg => new Response(JSON.stringify({ success: false, error: { message: msg } }), { status: 200 });
  const realFetch = window.fetch.bind(window);
  window.fetch = async (url, init) => {
    const u = new URL(String(url), "https://onizleme.invalid");
    if (u.hostname !== "onizleme.invalid") return realFetch(url, init);
    await new Promise(r => setTimeout(r, 60 + Math.random() * 90));
    const p = u.pathname.replace("/api/services/app", ""), q = u.searchParams;
    const body = init && init.body && typeof init.body === "string" ? JSON.parse(init.body) : {};
    if (p === "/Session/GetCurrentLoginInformations") return ok({ user: { id: 900001, name: "Demo", surname: "Kullanıcı", emailAddress: ME.emailAddress, userName: "demo" } });
    if (p === "/User/GetAll") return ok({ items: USERS });
    if (p === "/Data/All") {
      const k = keyOf(body.listId); if (!k) return fail("Liste bulunamadı");
      let items = store[k].map(r => computed(k, r));
      if (k === "G" && body.includeApprovalRequest) items = items.map(r => APPROVALS[r._id] && r[F("G", "Durum")]?.label === "Onay Bekliyor" ? { ...r, approvalRequest: APPROVALS[r._id] } : r);
      return ok({ items: items.slice(body.skipCount || 0, (body.skipCount || 0) + (body.maxResultCount || 100)), totalCount: items.length });
    }
    if (p === "/Data/Get") { const k = keyOf(q.get("listId")); const r = store[k]?.find(x => x._id === q.get("id")); return r ? ok(computed(k, r)) : fail("Kayıt bulunamadı"); }
    if (p === "/Data/UpdatePartial") {
      const k = keyOf(q.get("listId")); const r = store[k]?.find(x => x._id === q.get("id")); if (!r) return fail("Kayıt bulunamadı");
      const prev = {}, ch = {};
      for (const [fidStr, val] of Object.entries(body)) {
        const name = Object.entries(SCHEMA[k].f).find(([, f]) => String(f.id) === fidStr)?.[0] || fidStr;
        prev[name] = r[fidStr]; r[fidStr] = toStored(k, fidStr, val); ch[name] = r[fidStr];
      }
      hist(k, r, ch, prev, false);
      afterUpdate(k, r, body, prev);
      return ok(computed(k, r));
    }
    if (p === "/Data/Create") {
      const k = keyOf(q.get("listId"));
      const r = { _id: oid() };
      for (const [fidStr, val] of Object.entries(body)) r[fidStr] = toStored(k, fidStr, val);
      store[k].push(r); hist(k, r, {}, null, false); afterCreate(k, r);
      return ok({ id: r._id });
    }
    if (p === "/Data/Delete") { const k = keyOf(q.get("listId")); store[k] = store[k].filter(x => x._id !== q.get("id")); return ok(null); }
    if (p === "/Notification/GetUserNotifications") { const s = Number(q.get("skipCount") || 0), m = Number(q.get("maxResultCount") || 100); return ok({ items: NOTES.slice(s, s + m), totalCount: NOTES.length, unreadCount: NOTES.filter(n => n.state === 0).length }); }
    if (p === "/Notification/SetNotificationAsRead") { const n = NOTES.find(x => x.id === body.id); if (n) n.state = 1; return ok(null); }
    if (p === "/History/GetAll") return ok({ items: HIST.filter(h => h.recordId === q.get("recordId")) });
    if (p === "/History/GetAllPaged") return ok({ items: HIST.slice(body.skipCount || 0, (body.skipCount || 0) + (body.maxResultCount || 100)) });
    if (p === "/AdvancedComment/GetAll") return ok({ items: COMMENTS[q.get("recordId")] || [] });
    if (p === "/AdvancedComment/Comment") { (COMMENTS[body.recordId] ||= []).push({ comment: body.comment, userFullName: "Demo Kullanıcı", creationTime: new Date().toISOString() }); return ok(null); }
    if (p.startsWith("/AutomationApprovalRequest/")) {
      const rid = Number(q.get("approvalRequestId"));
      const gid = Object.keys(APPROVALS).find(k => APPROVALS[k].requestId === rid);
      const g = store.G.find(x => x._id === gid); if (!g) return fail("Onay talebi bulunamadı");
      APPROVALS[gid].status = p.endsWith("Approve") ? 1 : 2;
      const approve = p.endsWith("Approve");
      g[F("G", "Onay Durumu")] = opt(approve ? "Onaylandı" : "Reddedildi");
      store.O.push({ _id: oid(), [F("O", "Başlık")]: (approve ? "Onaylandı: " : "Reddedildi: ") + g[F("G", "Görev Adı")], [F("O", "Karar")]: opt(approve ? "Onaylandı" : "Reddedildi"),
        [F("O", "Onaylayan")]: ME, [F("O", "Tarih")]: iso(tday()), [F("O", "Görev")]: [lnk(g, "G", "Görev Adı")], [F("O", "Proje")]: g[F("G", "Proje")], [F("O", "Not")]: q.get("message") || "", [F("O", "Kayıt No")]: store.O.length + 1 });
      g[F("G", "Durum")] = opt(approve ? "Tamamlandı" : "Revizyon Gerekli");
      if (!approve) notify(900001, "↩️ " + g[F("G", "Görev Adı")] + " reddedildi, revizyon gerekiyor.", "G", g);
      afterUpdate("G", g, { [F("G", "Durum")]: 1 }, {});
      return ok(null);
    }
    if (p === "/File/Upload") return ok([{ fileName: "rapor.pdf", fileType: "application/pdf", fileToken: "tok" + (++seq), hasThumbnail: false, fileUrl: "", thumbnailUrl: "" }]);
    if (p.startsWith("/File/GeneratePublicDownloadUrl")) return fail("Önizlemede dosya indirilemez.");
    return fail("Önizlemede desteklenmiyor: " + p);
  };
})();

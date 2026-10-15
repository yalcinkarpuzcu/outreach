/* ÖNİZLEME / TEST İSKELESİ — gerçek pakete GİRMEZ.
   fetch'i yakalar, SCHEMA alan id'leriyle sentetik kayıtlar üretir ve Workiom otomasyonlarını
   (öncül kilidi, onay, ardılları açma, baseline, proje oluşturma) hafifçe taklit eder. */
"use strict";
(function () {
  const ME = { id: 900001, name: "Demo", surname: "Kullanıcı", emailAddress: "demo@ornek.com" };
  const ANA = { id: "900002", fullname: "Analitik Uzmanı", emailAddress: "a@ornek.com" };
  const meU = { id: String(ME.id), fullname: "Demo Kullanıcı", emailAddress: ME.emailAddress };
  const F = (l, n) => String(SCHEMA[l].f[n].id);
  const opt = (l, n, label) => ({ id: "o-" + label, label, isClosed: label === "Tamamlandı" || label === "İptal" });
  let seq = 0;   // sayfalar arası tutarlı kimlik (her sayfa aynı veriyi üretir)
  const oid = () => "m" + String(++seq).padStart(23, "0");
  const iso = day => new Date((day) * 864e5 - 3 * 3600e3).toISOString().replace(".000", "");   // TR gece yarısı (UTC-3s)
  const tday = () => { const d = new Date(); return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5); };
  const store = { P: [], G: [], K: [], S: [] };
  const ids = l => SCHEMA[l].id;
  const listKey = id => Object.keys(store).find(k => SCHEMA[k].id === id);

  /* şablonlar + kütüphane */
  const sab = {};
  MOCK_TEMPLATE.sablonlar.forEach((s, i) => {
    const r = { _id: oid() }; r[F("S", "Şablon")] = s; r[F("S", "Aktif")] = true; r[F("S", "Toplam Süre (gün)")] = 1006;
    store.S.push(r); sab[s] = r;
  });
  const REF = Math.round(Date.UTC(2026, 0, 1) / 864e5);
  const kFaz = {}, kNo = {};
  MOCK_TEMPLATE.fazlar.forEach(f => {
    const r = { _id: oid() };
    Object.assign(r, { [F("K", "Görev Adı")]: f.ad, [F("K", "WBS No")]: f.sira * 100, [F("K", "Tür")]: opt("K", "Tür", "Faz"),
      [F("K", "Başlangıç")]: iso(REF + f.s), [F("K", "Bitiş")]: iso(REF + f.e), [F("K", "Şablonlar")]: Object.values(sab).map(s => ({ _id: s._id, label: s[F("S", "Şablon")] })) });
    store.K.push(r); kFaz[f.kod] = r;
  });
  MOCK_TEMPLATE.gorevler.forEach(g => {
    const r = { _id: oid() };
    Object.assign(r, { [F("K", "Görev Adı")]: g.ad, [F("K", "WBS No")]: g.no, [F("K", "Tür")]: opt("K", "Tür", g.kt ? "Kilometre Taşı" : "Görev"),
      [F("K", "Başlangıç")]: iso(REF + g.s), [F("K", "Bitiş")]: iso(REF + g.e), [F("K", "Kilometre Taşı")]: g.kt, [F("K", "Onay Gerekli")]: g.onay, [F("K", "Varsayım")]: g.vars,
      [F("K", "Sorumlu Departman")]: [{ _id: "d", label: g.dep }], [F("K", "Üst Öğe")]: [{ _id: kFaz[g.faz]._id, label: kFaz[g.faz][F("K", "Görev Adı")] }],
      [F("K", "Şablonlar")]: g.sab.map(s => ({ _id: sab[s]._id, label: s })) });
    store.K.push(r); kNo[g.no] = r;
  });
  MOCK_TEMPLATE.gorevler.forEach(g => { kNo[g.no][F("K", "Öncüller")] = g.onc.map(p => ({ _id: kNo[p]._id, label: kNo[p][F("K", "Görev Adı")], dependencyType: 1 })); });

  /* proje + görev üretimi (A1/A2 taklidi) */
  function makeProject(name, sabName, startDay, opts) {
    const p = { _id: oid() };
    const code = store.P.length + 1;
    Object.assign(p, { [F("P", "Proje Adı")]: name, [F("P", "Proje Kodu")]: code, [F("P", "Şablon")]: [{ _id: sab[sabName]._id, label: sabName }],
      [F("P", "Proje Yöneticisi")]: meU, [F("P", "Başlangıç Tarihi")]: iso(startDay), [F("P", "Hedef Bitiş")]: iso(startDay + 1006),
      [F("P", "Durum")]: opt("P", "Durum", opts.durum || "Devam Ediyor"), [F("P", "Plan Durumu")]: opt("P", "Plan Durumu", "Hazır"),
      [F("P", "Ürün / Molekül")]: opts.urun || "" });
    store.P.push(p);
    const fazRec = {}, noRec = {};
    MOCK_TEMPLATE.fazlar.forEach(f => {
      const r = { _id: oid() };
      Object.assign(r, { [F("G", "Görev Adı")]: f.ad, [F("G", "WBS No")]: f.sira * 100, [F("G", "Tür")]: opt("G", "Tür", "Faz"), [F("G", "Durum")]: opt("G", "Durum", "Başlamadı"),
        [F("G", "Başlangıç")]: iso(startDay + f.s), [F("G", "Bitiş")]: iso(startDay + f.e), [F("G", "Proje")]: [{ _id: p._id, label: name }], [F("G", "Kapalı")]: 0 });
      store.G.push(r); fazRec[f.kod] = r;
    });
    MOCK_TEMPLATE.gorevler.filter(g => g.sab.includes(sabName)).forEach(g => {
      const r = { _id: oid() };
      const owner = g.dep.startsWith("Analitik") ? ANA : meU;
      Object.assign(r, { [F("G", "Görev Adı")]: g.ad, [F("G", "WBS No")]: g.no, [F("G", "Tür")]: opt("G", "Tür", g.kt ? "Kilometre Taşı" : "Görev"),
        [F("G", "Durum")]: opt("G", "Durum", "Başlamadı"), [F("G", "Başlangıç")]: iso(startDay + g.s), [F("G", "Bitiş")]: iso(startDay + g.e),
        [F("G", "Proje")]: [{ _id: p._id, label: name }], [F("G", "Sorumlu")]: owner, [F("G", "Onaylayıcı")]: meU,
        [F("G", "Sorumlu Departman")]: [{ _id: "d", label: g.dep }], [F("G", "Kilometre Taşı")]: g.kt, [F("G", "Onay Gerekli")]: g.onay,
        [F("G", "% Tamamlanma")]: 0, [F("G", "Kapalı")]: 0, [F("G", "Üst Görev")]: [{ _id: fazRec[g.faz]._id, label: fazRec[g.faz][F("G", "Görev Adı")] }],
        _no: g.no, _onc: g.onc });
      store.G.push(r); noRec[g.no] = r;
    });
    Object.values(noRec).forEach(r => { r[F("G", "Öncüller")] = r._onc.filter(n => noRec[n]).map(n => ({ _id: noRec[n]._id, label: noRec[n][F("G", "Görev Adı")], dependencyType: 1 })); });
    recompute();
    return { p, noRec };
  }

  const st = r => r[F("G", "Durum")]?.label;
  const setSt = (r, label) => { r[F("G", "Durum")] = opt("G", "Durum", label); };
  function recompute() {
    const byId = new Map(store.G.map(r => [r._id, r]));
    for (const r of store.G) {
      const preds = (r[F("G", "Öncüller")] || []).map(d => byId.get(d._id)).filter(Boolean);
      r[F("G", "Açık Öncül Sayısı")] = preds.filter(p => !["Tamamlandı", "İptal"].includes(st(p))).length;
      r[F("G", "Kapalı")] = ["Tamamlandı", "İptal"].includes(st(r)) ? 1 : 0;
      const be = r[F("G", "Baseline Bitiş")];
      r[F("G", "Sapma (gün)")] = be ? Math.round((new Date(r[F("G", "Bitiş")]) - new Date(be)) / 864e5) : 0;
      const end = new Date(r[F("G", "Bitiş")]);
      r[F("G", "Gecikmede")] = !r[F("G", "Kapalı")] && end < new Date(Date.now() - 864e5);
    }
  }
  function openSuccessors(closedId) {
    recompute();
    for (const r of store.G) if ((r[F("G", "Öncüller")] || []).some(d => d._id === closedId) && st(r) === "Başlamadı" && r[F("G", "Açık Öncül Sayısı")] === 0) setSt(r, "Başlayabilir");
  }
  function complete(r) {
    setSt(r, "Tamamlandı"); r[F("G", "% Tamamlanma")] = 100; r[F("G", "Gerçekleşen Bitiş")] = iso(tday());
    delete r.approvalRequest; openSuccessors(r._id);
  }
  function automationOnStatus(r) {
    recompute();
    const s = st(r);
    if (["Devam Ediyor", "Onay Bekliyor", "Tamamlandı"].includes(s) && r[F("G", "Açık Öncül Sayısı")] > 0) { setSt(r, "Başlamadı"); return; }
    if (s === "Devam Ediyor" && !r[F("G", "Gerçekleşen Başlangıç")]) r[F("G", "Gerçekleşen Başlangıç")] = iso(tday());
    if (s === "Onay Bekliyor") {
      if (r[F("G", "Onay Gerekli")]) { r[F("G", "Onay Durumu")] = opt("G", "Onay Durumu", "Bekliyor"); r.approvalRequest = { requestId: "ar-" + r._id, status: 0, usersIds: [ME.id] }; }
      else complete(r);
    }
    if (s === "Tamamlandı") {
      if (r[F("G", "Onay Gerekli")] && r[F("G", "Onay Durumu")]?.label !== "Onaylandı") { setSt(r, "Onay Bekliyor"); automationOnStatus(r); }
      else complete(r);
    }
    recompute();
  }

  /* demo durumu: bir proje ilerlemiş, biri yeni */
  const t0 = tday();
  const a = makeProject("Calcium Carbonate 500 mg Film Tablet", "Yeni Ürün", t0 - 190, { urun: "Kalsiyum karbonat" });
  const doneUpTo = [1, 2, 3, 4, 5, 6, 7, 8, 11, 9, 10, 12, 16];
  doneUpTo.forEach(n => { const r = a.noRec[n]; if (r) { setSt(r, "Tamamlandı"); r[F("G", "% Tamamlanma")] = 100; } });
  [["13", "Devam Ediyor", 70], ["14", "Devam Ediyor", 55], ["15", "Devam Ediyor", 40], ["17", "Başlayabilir", 0], ["18", "Onay Bekliyor", 100]].forEach(([n, s, pc]) => {
    const r = a.noRec[n]; setSt(r, s); r[F("G", "% Tamamlanma")] = pc;
    if (s === "Onay Bekliyor") { r[F("G", "Onay Durumu")] = opt("G", "Onay Durumu", "Bekliyor"); r.approvalRequest = { requestId: "ar-" + r._id, status: 0, usersIds: [ME.id] }; r[F("G", "Notlar")] = "Formülasyon denemeleri F1–F6 tamamlandı, F5 seçildi."; r[F("G", "Dokümanlar")] = [{ _id: "f1", FileToken: "f1", FileName: "Formulasyon_Raporu_F5.pdf", ContentType: "application/pdf", Size: 182000 }]; }
  });
  for (const r of store.G.filter(x => x[F("G", "Proje")][0]._id === a.p._id)) {   // baseline: 25 gün önceki plan
    r[F("G", "Baseline Başlangıç")] = r[F("G", "Başlangıç")];
    r[F("G", "Baseline Bitiş")] = iso(Math.round(new Date(r[F("G", "Bitiş")]) / 864e5) - (r._no >= 9 ? 12 : 0) + (r._no ? 0 : 0));
  }
  a.p[F("P", "Baseline No")] = 1; a.p[F("P", "Baseline Tarihi")] = iso(t0 - 185);
  makeProject("Demo – Alternatif API Kaynağı", "Alternatif Kaynak", t0 + 20, { durum: "Planlanıyor", urun: "Metformin HCl" });
  recompute();

  /* fetch yakalayıcı */
  const json = (result, status) => new Response(JSON.stringify({ success: status ? false : true, result, error: status ? { message: "Hata" } : null, unAuthorizedRequest: false }), { status: status || 200, headers: { "Content-Type": "application/json" } });
  const realFetch = window.fetch.bind(window);
  window.fetch = async (url, init) => {
    url = String(url);
    await new Promise(r => setTimeout(r, 120));
    if (url.includes("IsTenantAvailable")) return json({ state: 1, serverRootAddress: "https://onizleme.invalid" });
    if (!url.startsWith("https://onizleme.invalid")) return realFetch(url, init);
    const u = new URL(url), path = u.pathname, q = u.searchParams, body = init?.body && typeof init.body === "string" ? JSON.parse(init.body) : null;
    if (path.endsWith("/Session/GetCurrentLoginInformations")) return json({ user: ME });
    if (path.endsWith("/Data/All")) {
      recompute();
      const items = store[listKey(body.listId)].map(r => { const c = { ...r }; if (!body.includeApprovalRequest) delete c.approvalRequest; return c; });
      return json({ items, totalCount: items.length });
    }
    if (path.endsWith("/Data/Get")) { recompute(); return json(store[listKey(q.get("listId"))].find(r => r._id === q.get("id"))); }
    if (path.endsWith("/Data/UpdatePartial")) {
      const k = listKey(q.get("listId")), r = store[k].find(x => x._id === q.get("id"));
      for (const [fidk, val] of Object.entries(body)) {
        const fname = Object.entries(SCHEMA[k].f).find(([, e]) => String(e.id) === fidk)?.[0];
        const t = SCHEMA[k].f[fname]?.t;
        r[fidk] = (t === 16 || t === 4) && typeof val === "string" ? opt(k, fname, val) : (t === 2 && val ? iso(Math.round(Date.UTC(...val.split("-").map((x, i) => i === 1 ? x - 1 : +x)) / 864e5)) : val);
      }
      if (k === "G" && body[F("G", "Durum")]) setTimeout(() => automationOnStatus(r), 600);
      if (k === "P" && body[F("P", "Durum")] === "Plan Onaylandı (Baseline)") setTimeout(() => {
        for (const g of store.G.filter(x => x[F("G", "Proje")][0]._id === r._id)) { g[F("G", "Baseline Başlangıç")] = g[F("G", "Başlangıç")]; g[F("G", "Baseline Bitiş")] = g[F("G", "Bitiş")]; }
        r[F("P", "Baseline No")] = (r[F("P", "Baseline No")] || 0) + 1; r[F("P", "Baseline Tarihi")] = iso(tday()); r[F("P", "Durum")] = opt("P", "Durum", "Devam Ediyor"); recompute();
      }, 1500);
      recompute();
      return json(null);
    }
    if (path.endsWith("/Data/Create")) {
      const k = listKey(q.get("listId"));
      if (k === "P") {
        const sb = store.S.find(s => s._id === body[F("P", "Şablon")][0]);
        const sd = Math.round(new Date(body[F("P", "Başlangıç Tarihi")] + "T12:00:00Z") / 864e5);
        const { p } = makeProject(body[F("P", "Proje Adı")], sb[F("S", "Şablon")], sd, { durum: "Planlanıyor", urun: body[F("P", "Ürün / Molekül")] });
        const hidden = store.G.filter(g => g[F("G", "Proje")][0]._id === p._id);
        store.G = store.G.filter(g => !hidden.includes(g));
        p[F("P", "Plan Durumu")] = opt("P", "Plan Durumu", "Bekliyor");
        setTimeout(() => { store.G.push(...hidden); p[F("P", "Plan Durumu")] = opt("P", "Plan Durumu", "Görevler Oluşturuldu"); }, 3500);
        setTimeout(() => { p[F("P", "Plan Durumu")] = opt("P", "Plan Durumu", "Hazır"); }, 7500);
        return json({ id: p._id });
      }
      const r = { _id: oid(), ...body }; store[k].push(r); return json({ id: r._id });
    }
    if (path.includes("/AutomationApprovalRequest/")) {
      const rid = q.get("approvalRequestId"), r = store.G.find(x => x.approvalRequest?.requestId === rid);
      if (r) {
        if (path.endsWith("/Approve")) { r[F("G", "Onay Durumu")] = opt("G", "Onay Durumu", "Onaylandı"); setTimeout(() => complete(r), 500); }
        else { r[F("G", "Onay Durumu")] = opt("G", "Onay Durumu", "Reddedildi"); setSt(r, "Revizyon Gerekli"); delete r.approvalRequest; }
      }
      return json(null);
    }
    if (path.includes("/File/")) return json(path.includes("Upload") ? [{ fileName: "yeni.pdf", fileType: "application/pdf", fileToken: oid(), hasThumbnail: false, fileUrl: "", thumbnailUrl: "" }] : { url: "about:blank" });
    return json(null, 404);
  };
  // önizlemede oturum çerezi yok → çerez okuyucuyu taklit et
  window.getCookie = name => (name === "Abp.AuthToken" ? "onizleme" : name === "Abp.TenantId" ? "1" : null);
})();

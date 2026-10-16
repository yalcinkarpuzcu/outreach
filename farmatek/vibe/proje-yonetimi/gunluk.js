/* Değişiklik günlüğü — uygulama genelinde Workiom kayıt geçmişi (kim, neyi, ne zaman değiştirdi) */
"use strict";

VIEWS.gunluk = { title: "Değişiklik Günlüğü", async mount(ctx) {
  const PAGE = 100;
  const S = { items: [], skip: 0, done: false, list: "", q: "", userOnly: false, planOnly: false, alive: true };
  const KRITIK = /Başlangıç|Bitiş|Hedef Tarih|Sorumlu|Durum|Onaylayıcı|Öncüller|Bağlı Görevler|Proje Yöneticisi|Gün Ofseti/;
  const box = el("div", { class: "page" });
  clear(ctx.main).append(box);
  const more = el("button", { class: "btn", type: "button", text: "Daha eski kayıtları yükle" });

  async function fetchPage() {
    more.disabled = true;
    try {
      const r = await api("POST", "/api/services/app/History/GetAllPaged?appId=" + encodeURIComponent(L.APP.id) + "&commentAsPlainText=true", { maxResultCount: PAGE, skipCount: S.skip });
      if (!S.alive) return;
      const items = Array.isArray(r) ? r : (r.items || []);
      S.items.push(...items.filter(h => h.isVisible !== false));
      S.skip += PAGE; S.done = items.length < PAGE;
      draw();
    } catch (e) { if (!S.items.length) stateError(box, e, reload); else if (!(e instanceof SessionGone)) toast(e.message, "err"); }
    finally { more.disabled = false; }
  }
  function reload() { S.items = []; S.skip = 0; S.done = false; stateLoading(box, "Günlük yükleniyor…"); fetchPage(); }
  more.addEventListener("click", fetchPage);

  function drawRibbon() {
    const lists = [...new Set(S.items.map(h => h.listName).filter(Boolean))].sort((a, b) => a.localeCompare(b, "tr"));
    const ls = el("select", { class: "rsel", "aria-label": "Liste" }, el("option", { value: "", text: "Tüm listeler" }), ...lists.map(n => el("option", { value: n, text: n, selected: n === S.list || null })));
    ls.addEventListener("change", () => { S.list = ls.value; draw(); });
    const q = el("input", { class: "rsel search", type: "search", placeholder: "Kayıt ya da kişi ara…", value: S.q, "aria-label": "Ara" });
    q.addEventListener("input", () => { S.q = q.value.trim().toLocaleLowerCase("tr"); drawList(); });
    clear(ctx.ribbon).append(
      rgroup("Filtre", el("div", { class: "rcol" }, el("div", { class: "rrow" }, ls, q),
        el("div", { class: "rrow" }, rcheck("Yalnızca kişilerin değişiklikleri", S.userOnly, on => { S.userOnly = on; drawList(); }),
          rcheck("Yalnızca plan/durum değişiklikleri", S.planOnly, on => { S.planOnly = on; drawList(); })))),
      rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: reload }), rbtn({ icon: "excel", text: "Excel'e aktar", onclick: exportCSV })));
  }
  const filtered = () => S.items.filter(h => (!S.list || h.listName === S.list) && (!S.userOnly || h.automationId == null)
    && (!S.planOnly || h.approvalRequestItem || Object.keys(h.record || {}).some(k => KRITIK.test(k)))
    && (!S.q || [h.itemName, h.username, h.listName].join(" ").toLocaleLowerCase("tr").includes(S.q)));
  function drawList() {
    const list = filtered();
    setStatus(list.length + " kayıt gösteriliyor", S.items.length + " yüklendi", S.done ? "tümü yüklendi" : "daha eskileri var");
    if (!list.length) { stateEmpty(box, "Eşleşen kayıt yok", "Filtreleri değiştirin" + (S.done ? "." : " ya da daha eski kayıtları yükleyin."), S.done ? null : more, "log"); return; }
    const groups = new Map();
    for (const h of list) {
      const day = new Date(h.date).toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
      if (!groups.has(day)) groups.set(day, []);
      groups.get(day).push(h);
    }
    const wrap = el("div", { class: "card log" });
    for (const [day, hs] of groups) wrap.append(el("h3", { class: "n-day", text: day }), el("ul", { class: "hist" }, ...hs.map(h => histEntry(h, true))));
    clear(box).append(wrap, S.done ? null : el("div", { class: "center" }, more));
  }
  function draw() { drawRibbon(); drawList(); }
  function exportCSV() {
    const rows = [["Tarih", "Kişi", "Otomasyon", "Liste", "Kayıt", "Alan", "Önceki", "Yeni"]];
    for (const h of filtered()) {
      const rec = h.record || {}, prev = h.previousRecord || {};
      const keys = Object.keys(rec).filter(k => !/^Last |^Creation|^Creator/.test(k));
      if (!keys.length) rows.push([fmtStamp(h.date), h.username || "", h.automationId != null ? "Evet" : "", h.listName || "", h.itemName || "", "", "", ISLEM[h.action] || ""]);
      for (const k of keys) rows.push([fmtStamp(h.date), h.username || "", h.automationId != null ? "Evet" : "", h.listName || "", h.itemName || "", k, k in prev ? histValue(prev[k]) : "", histValue(rec[k])]);
    }
    downloadCSV("degisiklik_gunlugu.csv", rows);
  }
  drawRibbon();
  reload();
  return { unmount() { S.alive = false; } };
} };

/* Portföy — KPI'lar, proje tablosu, portföy Gantt'ı (proje çubukları + ◆ kilometre taşları), yeni proje sihirbazı */
"use strict";

VIEWS.portfoy = { title: "Portföy", async mount(ctx) {
  const S = { projs: [], tasks: [], mss: [], tpls: [], mode: "tablo", show: "aktif", alive: true };
  const kpiBox = el("div", { class: "kpis" });
  const body = el("div", { class: "pf-body" });
  clear(ctx.main).append(el("div", { class: "page" }, kpiBox, body));
  let gantt = null;

  function drawRibbon() {
    clear(ctx.ribbon).append(
      rgroup("Proje", rbtn({ icon: "plus", text: "Yeni proje", big: true, cls: "hot", onclick: newProject })),
      rgroup("Görünüm", el("div", { class: "rcol" },
        rseg([["tablo", "Tablo"], ["gantt", "Portföy Gantt"]], S.mode, m => { S.mode = m; draw(); }, "Görünüm"),
        rseg([["aktif", "Aktif"], ["hepsi", "Tümü"]], S.show, m => { S.show = m; draw(); }, "Kapsam"))),
      rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: load }), rbtn({ icon: "excel", text: "Excel'e aktar", onclick: exportCSV })));
  }

  async function load() {
    stateLoading(body, "Portföy yükleniyor…");
    try {
      const [p, g, k, s] = await Promise.all([fetchAll("P"), fetchAll("G"), fetchAll("K"), fetchAll("S").catch(() => [])]);
      if (!S.alive) return;
      S.tasks = g.map(taskModel); S.mss = k.map(msModel); S.tpls = s;
      S.projs = p.map(r => projStats(r));
      drawKPIs(); draw();
    } catch (e) { stateError(body, e, load); }
  }
  function projStats(r) {
    const id = r._id, ts = S.tasks.filter(t => t.project === id), ks = S.mss.filter(k => k.project === id);
    const w = t => Math.max(1, (t.end ?? 0) - (t.start ?? 0));
    const tot = ts.reduce((a, t) => a + w(t), 0);
    const ends = ts.map(t => t.end).filter(x => x != null), starts = ts.map(t => t.start).filter(x => x != null);
    const bEnds = ts.map(t => t.baseEnd).filter(x => x != null);
    const next = ks.filter(k => !k.closed && k.start != null).sort((a, b) => a.start - b.start)[0];
    const end = ends.length ? Math.max(...ends) : toDay(v(r, "P", "Hedef Bitiş"));
    const bEnd = bEnds.length ? Math.max(...bEnds) : null;
    return {
      id, rec: r, name: v(r, "P", "Proje Adı") || "(adsız)", code: v(r, "P", "Proje Kodu"), status: lbl(v(r, "P", "Durum")),
      planState: lbl(v(r, "P", "Plan Durumu")), tpl: linkLabel(v(r, "P", "Şablon")), pm: v(r, "P", "Proje Yöneticisi"),
      start: starts.length ? Math.min(...starts) : toDay(v(r, "P", "Başlangıç Tarihi")), end, bEnd,
      variance: end != null && bEnd != null ? end - bEnd : null,
      pct: tot ? Math.round(ts.reduce((a, t) => a + w(t) * (t.pct || 0), 0) / tot) : 0,
      n: ts.length, closed: ts.filter(t => t.closed).length, late: ts.filter(t => t.late).length,
      appr: ts.filter(t => t.status === "Onay Bekliyor").length, next, mss: ks,
      baseNo: Number(v(r, "P", "Baseline No")) || 0
    };
  }
  const visible = () => S.projs.filter(p => S.show === "hepsi" || !KAPALI.has(p.status)).sort((a, b) => (a.start ?? 0) - (b.start ?? 0));

  function drawKPIs() {
    const act = S.projs.filter(p => !KAPALI.has(p.status));
    const open = S.tasks.filter(t => !t.closed && act.some(p => p.id === t.project));
    const td = todayDay();
    const kSoon = S.mss.filter(k => !k.closed && k.start != null && k.start <= td + 30 && act.some(p => p.id === k.project));
    const kpi = (label, val, sub, cls, onclick) => el(onclick ? "button" : "div", { class: "kpi" + (cls ? " " + cls : ""), type: onclick ? "button" : null, onclick },
      el("div", { class: "k-l", text: label }), el("div", { class: "k-v", text: String(val) }), el("div", { class: "k-s", text: sub || "" }));
    clear(kpiBox).append(
      kpi("Aktif proje", act.length, S.projs.length + " projenin"),
      kpi("Açık görev", open.length, open.filter(t => t.status === "Devam Ediyor").length + " devam ediyor"),
      kpi("Geciken görev", open.filter(t => t.late).length, open.filter(t => t.late && t.critical).length + " kritik", open.some(t => t.late) ? "bad" : "good"),
      kpi("Onay bekleyen", open.filter(t => t.status === "Onay Bekliyor").length, "zorunlu onay adımı", "", () => go("onaylar")),
      kpi("30 gün içinde KT", kSoon.length, kSoon.filter(k => k.start < td).length + " gecikmiş", kSoon.some(k => k.start < td) ? "warn" : ""),
      kpi("Bildirim", NOTIF.unread, "okunmamış", NOTIF.unread ? "warn" : "", () => go("bildirimler")));
  }

  function draw() {
    drawRibbon();
    if (gantt) { gantt.destroy(); gantt = null; }
    const list = visible();
    setStatus(list.length + " proje gösteriliyor", S.projs.length + " toplam");
    if (!list.length) {
      stateEmpty(body, "Henüz proje yok", "Şablondan ilk projenizi açın; fazlar, görevler, öncüller ve kilometre taşları yaklaşık 1 dakikada kurulur.",
        el("button", { class: "btn primary", type: "button", onclick: newProject }, icon("plus", 16), " Yeni proje"), "portfolio");
      return;
    }
    if (S.mode === "gantt") return drawGantt(list);
    const tbl = el("table", { class: "tbl" });
    tbl.append(el("thead", null, el("tr", null, ...["Proje", "Durum", "Şablon", "Proje yöneticisi", "İlerleme", "Başlangıç", "Plan bitiş", "Sapma", "Sonraki kilometre taşı", "Uyarılar", ""].map(h => el("th", { text: h })))));
    const tb = el("tbody");
    for (const p of list) {
      const varTxt = p.variance == null ? "—" : (p.variance > 0 ? "+" : "") + p.variance + " g";
      tb.append(el("tr", { class: "click", tabindex: "0", onclick: () => go("plan", p.id), onkeydown: e => { if (e.key === "Enter") go("plan", p.id); } },
        el("td", null, el("div", { class: "p-name" }, el("b", { text: p.name }), el("small", { text: "P" + (p.code ?? "") + (p.planState && p.planState !== "Hazır" ? " · plan: " + p.planState : "") }))),
        el("td", null, chip(p.status)),
        el("td", { text: p.tpl || "—" }),
        el("td", null, el("span", { class: "who" }, avatar(p.pm, "xs"), el("span", { text: userName(p.pm) || "—" }))),
        el("td", null, el("div", { class: "prog" }, el("div", { class: "prog-bar" }, el("span", { style: "width:" + p.pct + "%" })), el("small", { text: "%" + p.pct + " · " + p.closed + "/" + p.n }))),
        el("td", { text: fmtDay(p.start) }),
        el("td", { text: fmtDay(p.end) }),
        el("td", { class: p.variance > 0 ? "bad" : p.variance < 0 ? "good" : "", text: varTxt }),
        el("td", null, p.next ? el("span", { class: "ms-next" + (p.next.start < todayDay() ? " late" : "") }, "◆ " + p.next.name, el("small", { text: " " + fmtShort(p.next.start) })) : el("span", { class: "muted", text: p.mss.length ? "hepsine ulaşıldı" : "—" })),
        el("td", null, p.late ? el("span", { class: "tag late", text: p.late + " geciken" }) : null, p.appr ? el("span", { class: "tag", text: p.appr + " onay" }) : null),
        el("td", null, el("button", { class: "icon-btn", type: "button", "aria-label": "Proje bilgileri", title: "Proje bilgileri", onclick: e => { e.stopPropagation(); editProject(p); } }, icon("edit", 16)))));
    }
    tbl.append(tb);
    clear(body).append(el("div", { class: "card tbl-wrap" }, tbl));
  }

  function drawGantt(list) {
    const host = el("div", { class: "plan-grid pf-gantt" });
    clear(body).append(el("div", { class: "card flush" }, host));
    const rows = list.map(p => ({
      kind: "P", id: p.id, name: p.name, summary: true, start: p.start, end: p.end, pct: p.pct, deps: [], status: p.status, pm: p.pm,
      baseStart: null, baseEnd: p.bEnd, children: p.mss.filter(k => k.start != null).sort((a, b) => a.start - b.start).map(k => ({ ...k, children: [] }))
    }));
    let n = 0; rows.forEach(r => { r.num = ++n; r.children.forEach(c => c.num = ++n); });
    gantt = createPlan(host, {
      zoom: "ceyrek", leftWidth: 560, showBaseline: false,
      columns: [
        { key: "name", title: "Proje / kilometre taşı", w: 220, flex: true },
        { key: "st", title: "Durum", w: 120, render: t => chip(t.status) },
        { key: "pm", title: "PM", w: 40, render: t => t.kind === "P" ? avatar(t.pm, "xs") : "" },
        { key: "s", title: "Başlangıç", w: 86, render: t => fmtShort(t.start) },
        { key: "e", title: "Bitiş", w: 86, render: t => fmtShort(t.end) },
        { key: "p", title: "%", w: 44, cls: "r", render: t => t.kind === "P" ? t.pct + "%" : "" }
      ],
      labelFor: t => t.kind === "P" ? "%" + t.pct : t.name,
      onOpen: t => go("plan", t.kind === "P" ? t.id : t.project, t.kind === "K" ? { sec: t.id } : null),
      onSelect: t => t && setStatus("Seçili: " + t.name, "Çift tık: planı aç")
    });
    gantt.setRows(rows);
    gantt.collapseAll(true);
    gantt.scrollToToday();
  }

  function editProject(p) {
    const m = openModal({ title: "Proje bilgileri — " + p.name, wide: true });
    projectForm(p.rec, m.body, () => { m.close(); load(); loadProjects(); });
    m.foot.append(el("button", { class: "btn", type: "button", text: "Kapat", onclick: () => m.close() }),
      el("button", { class: "btn primary", type: "button", text: "Planı aç", onclick: () => { m.close(); go("plan", p.id); } }));
  }

  function exportCSV() {
    const rows = [["Proje", "Kod", "Durum", "Şablon", "Proje Yöneticisi", "Başlangıç", "Plan Bitiş", "Baseline Bitiş", "Sapma (gün)", "% Tamamlanma", "Görev", "Kapanan", "Geciken", "Onay Bekleyen", "Sonraki Kilometre Taşı", "KT Tarihi", "Baseline No"]];
    for (const p of visible()) rows.push([p.name, "P" + (p.code ?? ""), p.status, p.tpl, userName(p.pm), p.start != null ? dayToISO(p.start) : "", p.end != null ? dayToISO(p.end) : "",
      p.bEnd != null ? dayToISO(p.bEnd) : "", p.variance ?? "", p.pct, p.n, p.closed, p.late, p.appr, p.next?.name || "", p.next ? dayToISO(p.next.start) : "", p.baseNo || ""]);
    downloadCSV("portfoy_" + dayToISO(todayDay()) + ".csv", rows);
  }

  /* ── yeni proje sihirbazı ───────────────────────────────────────── */
  function newProject() {
    const m = openModal({ title: "Yeni proje", form: true, wide: true });
    const err = el("div", { class: "error-box", role: "alert" });
    const tpls = S.tpls.filter(t => v(t, "S", "Aktif") !== false);
    const fName = el("input", { class: "input", placeholder: "ör. Calcium Carbonate 500 mg Film Tablet" });
    const fTpl = el("select", { class: "input" }, el("option", { value: "", text: "— şablon seçin —" }),
      ...tpls.map(t => el("option", { value: t._id, text: v(t, "S", "Şablon") + (v(t, "S", "Toplam Süre (gün)") ? " · " + v(t, "S", "Toplam Süre (gün)") + " gün" : "") })));
    const tplInfo = el("p", { class: "hint" });
    fTpl.addEventListener("change", () => { const t = tpls.find(x => x._id === fTpl.value); tplInfo.textContent = t ? (v(t, "S", "Açıklama") || "") : ""; });
    const fStart = el("input", { class: "input", type: "date", value: dayToISO(todayDay()) });
    const fPM = userSelect(ME, "— proje yöneticisi —");
    const fProd = el("input", { class: "input", placeholder: "ör. Kalsiyum karbonat" });
    const fTeam = multiUserSelect([]);
    const fDesc = el("textarea", { class: "input", rows: "2" });
    const ok = el("button", { class: "btn primary", type: "submit", text: "Projeyi oluştur" });
    m.body.append(reqNote(), err,
      field("Proje adı", fName, { required: true, wide: true }),
      el("div", { class: "grid2" }, field("Şablon", fTpl, { required: true }), field("Başlangıç tarihi", fStart, { required: true })), tplInfo,
      el("div", { class: "grid2" }, field("Proje yöneticisi", fPM, { hint: "Plan hazır, gecikme ve kilometre taşı bildirimleri bu kişiye gider" }), field("Ürün / Molekül", fProd)),
      field("Proje ekibi", fTeam, { hint: "Ctrl/⌘ ile birden çok kişi seçin" }), field("Açıklama", fDesc, { wide: true }));
    m.foot.append(el("button", { class: "btn", type: "button", text: "Vazgeç", onclick: () => m.close() }), ok);
    fName.focus();
    m.box.addEventListener("submit", async ev => {
      ev.preventDefault();
      const ids = { name: fid("P", "Proje Adı"), tpl: fid("P", "Şablon"), start: fid("P", "Başlangıç Tarihi") };
      const vals = { [ids.name]: fName.value, [ids.tpl]: fTpl.value ? [fTpl.value] : [], [ids.start]: fStart.value };
      if (!checkRequired([{ id: ids.name, name: "Proje adı", control: fName }, { id: ids.tpl, name: "Şablon", control: fTpl }, { id: ids.start, name: "Başlangıç tarihi", control: fStart }], vals, err)) return;
      const p = { [ids.name]: fName.value.trim(), [ids.tpl]: [fTpl.value], [ids.start]: fStart.value };
      if (fPM.value) p[fid("P", "Proje Yöneticisi")] = fPM.value;
      if (fProd.value.trim()) p[fid("P", "Ürün / Molekül")] = fProd.value.trim();
      const team = [...fTeam.selectedOptions].map(o => o.value);
      if (team.length) p[fid("P", "Proje Ekibi")] = team;
      if (fDesc.value.trim()) p[fid("P", "Proje Açıklaması")] = fDesc.value.trim();
      ok.disabled = true; ok.textContent = "Oluşturuluyor…";
      try {
        const r = await createRecord("P", p);
        const pid = r?.id || r?._id;
        m.close();
        loadProjects();
        watchBuild(pid, fName.value.trim());
      } catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; ok.disabled = false; ok.textContent = "Projeyi oluştur"; }
    });
  }

  function watchBuild(pid, name) {
    const m = openModal({ title: "Plan kuruluyor — " + name });
    const steps = [["Fazlar Oluşturuldu", "Fazlar şablondan oluşturuluyor"], ["Görevler Oluşturuldu", "Görevler oluşturulup fazlara bağlanıyor"],
      ["Öncüller Bağlandı", "Öncül bağları kuruluyor"], ["Hazır", "Kilometre taşları oluşturulup görevlere bağlanıyor"]];
    const order = ["Bekliyor", ...steps.map(s => s[0])];
    const ol = el("ol", { class: "steps big" });
    const counts = el("p", { class: "muted" });
    const open = el("button", { class: "btn primary", type: "button", text: "Planı aç", disabled: true, onclick: () => { m.close(); go("plan", pid); } });
    m.body.append(el("p", { class: "lead", text: "Workiom otomasyonları şablondan planı kuruyor (yaklaşık 1 dakika). Bu pencereyi kapatabilirsiniz; plan hazır olunca bildirim gelir." }), ol, counts);
    m.foot.append(el("button", { class: "btn", type: "button", text: "Arka planda devam etsin", onclick: () => m.close() }), open);
    const t0 = Date.now();
    let stop = false;
    const prevClose = m.close; m.close = () => { stop = true; prevClose(); };
    const tick = async () => {
      if (stop) return;
      try {
        const rec = await getRecord("P", pid);
        const st = lbl(v(rec, "P", "Plan Durumu")) || "Bekliyor";
        const i = order.indexOf(st);
        clear(ol).append(...steps.map(([, txt], k) => el("li", { class: k + 1 <= i ? "done" : k + 1 === i + 1 ? "now" : "" }, el("span", { class: "dot" }), txt)));
        const sec = Math.round((Date.now() - t0) / 1000);
        counts.textContent = "Geçen süre: " + sec + " sn · Durum: " + st;
        if (st === "Hazır") {
          await new Promise(r => setTimeout(r, 2500));
          const [g, k] = await Promise.all([fetchAll("G"), fetchAll("K")]);
          const nt = g.filter(r => linkIds(v(r, "G", "Proje")).includes(pid)).length, nk = k.filter(r => linkIds(v(r, "K", "Proje")).includes(pid)).length;
          counts.textContent = "Plan hazır (" + sec + " sn): " + nt + " görev, " + nk + " kilometre taşı.";
          open.disabled = false; open.focus();
          load();
          return;
        }
        if (Date.now() - t0 > 240000) { counts.textContent = "Plan beklenenden uzun sürüyor. Planı açıp birazdan yenileyebilirsiniz."; open.disabled = false; return; }
      } catch (e) { if (e instanceof SessionGone) return; counts.textContent = "Durum okunamadı: " + e.message; }
      setTimeout(tick, 3000);
    };
    tick();
  }

  const off = NOTIF.on(() => S.projs.length && drawKPIs());
  drawRibbon();
  await load();
  return { unmount() { S.alive = false; off(); if (gantt) gantt.destroy(); } };
} };

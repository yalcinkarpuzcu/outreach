/* Görevlerim (Kanban / liste, sürükle-bırak durum, görev kartı) ve Onaylar (onayla / reddet, onay geçmişi) */
"use strict";

const KANBAN = [
  { key: "todo", title: "Yapılacak", sts: ["Başlamadı", "Başlayabilir"], drop: null },
  { key: "doing", title: "Devam ediyor", sts: ["Devam Ediyor", "Revizyon Gerekli", "Beklemede"], drop: "Devam Ediyor" },
  { key: "review", title: "Onayda", sts: ["Onay Bekliyor"], drop: "Onay Bekliyor" },
  { key: "done", title: "Tamamlandı", sts: ["Tamamlandı", "İptal"], drop: "Tamamlandı" }
];
function isLocked(t) { return !t.closed && ["Başlamadı", "Başlayabilir"].includes(t.status) && (TASK_INDEX.size ? openPredecessors(t, TASK_INDEX).length > 0 : t.openPreds > 0); }
function dueText(t) {
  if (t.end == null) return "";
  const d = t.end - todayDay();
  if (t.closed) return "Bitti " + (t.actualEnd != null ? fmtShort(t.actualEnd) : "");
  if (d < 0) return (-d) + " gün gecikti";
  if (d === 0) return "Bugün bitiyor";
  if (d <= 7) return d + " gün kaldı";
  return "Bitiş " + fmtShort(t.end);
}

/* Görev durumunu değiştir — kilit/onay kurallarını ön uyarıyla anlatır, otomasyonlar sunucuda çalışır */
let TASK_INDEX = new Map();     // açık öncül adları için (görevlerim/onaylar yüklenince doldurulur)
async function changeTaskStatus(t, st) {
  if (st === "Onay Bekliyor" && !t.approvalNeeded) st = "Tamamlandı";
  const open = TASK_INDEX.size ? openPredecessors(t, TASK_INDEX) : [];
  if (AKTIF_DURUMLAR.includes(st) && (open.length || (!TASK_INDEX.size && isLocked(t)))) {
    blockDialog(t, open.length ? open : t.deps.filter(d => d.hard !== false).map(d => ({ name: d.label })), st);
    return false;
  }
  await updateRecord("G", t.id, { [fid("G", "Durum")]: st });
  toast(st === "Tamamlandı" && t.approvalNeeded ? "Onay gerekli — görev onaylayıcıya gönderildi." :
    st === "Onay Bekliyor" ? "Onaya gönderildi: " + (userName(t.approver) || "onaylayıcı") : "Durum: " + st, "ok", 4000);
  return true;
}

function taskModal(t, onChanged) {
  const m = openModal({ title: t.name, wide: true });
  const tabs = el("div", { class: "dr-tabs", role: "tablist" });
  const body = el("div");
  m.body.append(el("div", { class: "dr-top" }, chip(t.status), isLocked(t) ? el("span", { class: "tag late", text: "🔒 " + t.openPreds + " açık öncül" }) : null,
    t.late ? el("span", { class: "tag late", text: "Gecikmede" }) : null, t.approvalNeeded ? el("span", { class: "tag", text: "✍ Onay gerekli" }) : null,
    el("span", { class: "muted", text: t.projectName + " · " + (t.phaseName || "") })), tabs, body);
  const panes = {
    "Görev": () => {
      body.append(el("dl", { class: "kv" },
        el("dt", { text: "Plan" }), el("dd", { text: fmtDay(t.start) + " → " + fmtDay(t.end) + " (" + (t.end - t.start) + " gün)" }),
        el("dt", { text: "Sorumlu" }), el("dd", { text: userName(t.owner) || "—" }),
        el("dt", { text: "Onaylayıcı" }), el("dd", { text: t.approvalNeeded ? (userName(t.approver) || "—") + (t.approvalState ? " · " + t.approvalState : "") : "Onay gerekmiyor" }),
        el("dt", { text: "Gerçekleşen" }), el("dd", { text: (t.actualStart != null ? fmtDay(t.actualStart) : "—") + " → " + (t.actualEnd != null ? fmtDay(t.actualEnd) : "—") }),
        t.desc ? el("dt", { text: "Kabul kriteri" }) : null, t.desc ? el("dd", { text: t.desc }) : null));
      const acts = el("div", { class: "quick" });
      const qb = (txt, st, cls) => acts.append(el("button", { class: "btn " + (cls || ""), type: "button", text: txt, disabled: (isLocked(t) && st !== "Beklemede") || null,
        onclick: async () => { try { if (await changeTaskStatus(t, st)) { m.close(); onChanged(); } } catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); } } }));
      if (!t.closed) {
        if (t.status !== "Devam Ediyor") qb("▶ Başlat", "Devam Ediyor", "");
        if (t.status !== "Onay Bekliyor") qb(t.approvalNeeded ? "✍ Onaya gönder" : "✓ Tamamla", t.approvalNeeded ? "Onay Bekliyor" : "Tamamlandı", "primary");
        if (t.status !== "Beklemede") qb("⏸ Beklemede", "Beklemede", "");
      }
      body.append(el("div", { class: "section-t", text: "Durum" }), acts);
      if (isLocked(t)) body.append(el("p", { class: "hint", text: "Bu görevin öncülleri bitmedi; başlatma ve tamamlama kilitli. Öncüller tamamlanınca size \"başlayabilir\" bildirimi gelir." }));
      const pct = el("input", { type: "range", min: "0", max: "100", step: "5", value: String(Math.round(t.pct || 0)), "aria-label": "% tamamlanma" });
      const pv = el("b", { text: "%" + Math.round(t.pct || 0) });
      pct.addEventListener("input", () => { pv.textContent = "%" + pct.value; });
      pct.addEventListener("change", async () => {
        try { await updateRecord("G", t.id, { [fid("G", "% Tamamlanma")]: Number(pct.value) }); t.pct = Number(pct.value); toast("İlerleme kaydedildi", "ok"); onChanged(true); }
        catch (e) { if (!(e instanceof SessionGone)) toast(e.message, "err"); }
      });
      body.append(el("div", { class: "section-t", text: "İlerleme" }), el("div", { class: "range-row" }, pct, pv));
      const ta = el("textarea", { class: "input", rows: "4" }); ta.value = t.notes || "";
      const err = el("div", { class: "error-box", role: "alert" });
      const sv = el("button", { class: "btn primary sm", type: "button", text: "Notu kaydet" });
      sv.addEventListener("click", async () => {
        sv.disabled = true;
        try { await updateRecord("G", t.id, { [fid("G", "Notlar")]: ta.value.trim() || null }); t.notes = ta.value.trim(); toast("Not kaydedildi", "ok"); onChanged(true); }
        catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
        finally { sv.disabled = false; }
      });
      body.append(field("Notlar", ta), el("div", { class: "dr-actions" }, err, sv), el("div", { class: "section-t", text: "Dokümanlar (protokol, rapor…)" }),
        fileEditor(t.files, async next => { await updateRecord("G", t.id, { [fid("G", "Dokümanlar")]: next }); t.files = next; toast("Doküman yüklendi", "ok"); show("Görev"); onChanged(true); }));
    },
    "Yorumlar": () => renderComments(body, "G", t.id),
    "Geçmiş": () => renderHistory(body, "G", t.id)
  };
  const show = name => {
    tabs.querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", b.textContent === name ? "true" : "false"));
    clear(body); panes[name]();
  };
  Object.keys(panes).forEach(n => tabs.append(el("button", { type: "button", role: "tab", text: n, onclick: () => show(n) })));
  show("Görev");
  m.foot.append(el("button", { class: "btn", type: "button", text: "Planda göster", onclick: () => { m.close(); go("plan", t.project, { sec: t.id }); } }),
    el("button", { class: "btn primary", type: "button", text: "Kapat", onclick: () => m.close() }));
}

VIEWS.gorevlerim = { title: "Görevlerim", async mount(ctx) {
  const S = { all: [], tab: "mine", mode: "kanban", closed: false, proj: "", depts: [], myDepts: new Set(), alive: true };
  const box = el("div", { class: "page" });
  clear(ctx.main).append(box);

  const scope = () => {
    let list = S.all;
    if (S.tab === "mine") list = list.filter(t => sameUser(t.owner, ME));
    else if (S.tab === "dept") list = list.filter(t => t.deptId && S.myDepts.has(t.deptId));
    if (S.proj) list = list.filter(t => t.project === S.proj);
    if (!S.closed) list = list.filter(t => !t.closed || (t.actualEnd != null && t.actualEnd >= todayDay() - 14));
    return list;
  };
  function drawRibbon() {
    const projs = [...new Map(S.all.map(t => [t.project, t.projectName])).entries()].filter(([id]) => id);
    const ps = el("select", { class: "rsel", "aria-label": "Proje" }, el("option", { value: "", text: "Tüm projeler" }), ...projs.map(([id, n]) => el("option", { value: id, text: n, selected: id === S.proj || null })));
    ps.addEventListener("change", () => { S.proj = ps.value; draw(); });
    const nMine = S.all.filter(t => sameUser(t.owner, ME) && !t.closed).length;
    clear(ctx.ribbon).append(
      rgroup("Kapsam", el("div", { class: "rcol" }, rseg([["mine", "Bana atananlar (" + nMine + ")"], ["dept", "Departmanım"], ["all", "Tüm görevler"]], S.tab, x => { S.tab = x; draw(); }, "Kapsam"), ps)),
      rgroup("Görünüm", el("div", { class: "rcol" }, rseg([["kanban", "Pano"], ["liste", "Liste"]], S.mode, x => { S.mode = x; draw(); }, "Görünüm"),
        rcheck("Eski kapananları da göster", S.closed, on => { S.closed = on; draw(); }))),
      rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: () => load() })));
  }
  async function load(silent) {
    if (!silent) stateLoading(box, "Görevler yükleniyor…");
    try {
      const [g, d] = await Promise.all([fetchAll("G", { includeApprovalRequest: true }), S.depts.length ? S.depts : fetchAll("D").catch(() => [])]);
      if (!S.alive) return;
      S.depts = d;
      S.myDepts = new Set(d.filter(x => [v(x, "D", "Departman Yöneticisi"), v(x, "D", "Onaylayıcı"), ...(v(x, "D", "Ekip Üyeleri") || [])].some(u => sameUser(u, ME))).map(x => x._id));
      S.all = g.map(taskModel);
      TASK_INDEX = new Map(S.all.map(t => [t.id, t]));
      draw();
    } catch (e) { stateError(box, e, () => load()); }
  }
  function card(t) {
    const c = el("article", { class: "kcard" + (t.late ? " late" : "") + (isLocked(t) ? " locked" : ""), tabindex: "0", draggable: t.closed ? null : "true", "data-id": t.id },
      el("div", { class: "kc-top" }, chip(t.status), isLocked(t) ? el("span", { class: "tag", title: t.openPreds + " açık öncül", text: "🔒 " + t.openPreds }) : null,
        t.approvalNeeded ? el("span", { class: "tag", title: "Onay gerekli", text: "✍" }) : null, t.files.length ? el("span", { class: "tag", text: "📄 " + t.files.length }) : null),
      el("h4", { text: t.name }),
      el("div", { class: "kc-meta", text: t.projectName + (t.phaseName ? " · " + t.phaseName : "") }),
      el("div", { class: "prog-bar sm" }, el("span", { style: "width:" + Math.round(t.pct || 0) + "%" })),
      el("div", { class: "kc-foot" }, avatar(t.owner, "xs"), el("span", { class: "due" + (t.late ? " bad" : ""), text: dueText(t) })));
    c.addEventListener("click", () => taskModal(t, silent => load(silent)));
    c.addEventListener("keydown", e => { if (e.key === "Enter") taskModal(t, silent => load(silent)); });
    c.addEventListener("dragstart", e => { e.dataTransfer.setData("text/plain", t.id); e.dataTransfer.effectAllowed = "move"; c.classList.add("dragging"); });
    c.addEventListener("dragend", () => c.classList.remove("dragging"));
    return c;
  }
  function draw() {
    drawRibbon();
    const list = scope();
    setStatus(list.length + " görev", list.filter(t => t.late).length + " geciken", list.filter(isLocked).length + " kilitli (öncül bekliyor)");
    if (!list.length) {
      stateEmpty(box, S.tab === "mine" ? "Size atanmış açık görev yok" : "Görev yok", S.tab === "mine" ? "Bir görev size atandığında ya da öncülleri bitip başlayabilir olduğunda burada ve bildirimlerde görünür." : "Kapsamı ya da filtreyi değiştirin.", null, "task");
      return;
    }
    if (S.mode === "liste") {
      const tbl = el("table", { class: "tbl" });
      tbl.append(el("thead", null, el("tr", null, ...["Görev", "Proje", "Durum", "Sorumlu", "Başlangıç", "Bitiş", "%", ""].map(h => el("th", { text: h })))));
      const tb = el("tbody");
      for (const t of [...list].sort((a, b) => (a.end ?? 0) - (b.end ?? 0))) tb.append(el("tr", { class: "click", tabindex: "0", onclick: () => taskModal(t, s => load(s)) },
        el("td", null, el("b", { text: t.name }), isLocked(t) ? el("span", { class: "tag", text: " 🔒" }) : null),
        el("td", { text: t.projectName }), el("td", null, chip(t.status)), el("td", { text: userName(t.owner) || "—" }),
        el("td", { text: fmtShort(t.start) }), el("td", { class: t.late ? "bad" : "", text: fmtShort(t.end) }), el("td", { text: "%" + Math.round(t.pct || 0) }),
        el("td", { class: "muted", text: dueText(t) })));
      tbl.append(tb);
      clear(box).append(el("div", { class: "card tbl-wrap" }, tbl));
      return;
    }
    const board = el("div", { class: "kanban" });
    for (const col of KANBAN) {
      const items = list.filter(t => col.sts.includes(t.status)).sort((a, b) => (a.end ?? 0) - (b.end ?? 0));
      const zone = el("div", { class: "kcol-body" }, ...items.map(card));
      const colEl = el("section", { class: "kcol c-" + col.key, "aria-label": col.title },
        el("header", null, el("span", { text: col.title }), el("span", { class: "cnt", text: String(items.length) })), zone);
      if (col.drop) {
        colEl.addEventListener("dragover", e => { e.preventDefault(); colEl.classList.add("over"); });
        colEl.addEventListener("dragleave", () => colEl.classList.remove("over"));
        colEl.addEventListener("drop", async e => {
          e.preventDefault(); colEl.classList.remove("over");
          const t = S.all.find(x => x.id === e.dataTransfer.getData("text/plain"));
          if (!t || col.sts.includes(t.status)) return;
          try { if (await changeTaskStatus(t, col.drop)) { setTimeout(() => S.alive && load(true), 2500); load(true); } }
          catch (er) { if (!(er instanceof SessionGone)) toast(er.message, "err"); }
        });
      }
      board.append(colEl);
    }
    clear(box).append(board, el("p", { class: "hint", text: "Kartı sütunlar arasında sürükleyerek durumunu değiştirin. Onay gereken görev \"Tamamlandı\"ya bırakılınca onaylayıcıya gider; öncülü açık görev kilitlidir." }));
  }
  drawRibbon();
  await load();
  return { unmount() { S.alive = false; } };
} };

VIEWS.onaylar = { title: "Onaylar", async mount(ctx) {
  const S = { tasks: [], hist: [], tab: "bana", alive: true };
  const box = el("div", { class: "page" });
  clear(ctx.main).append(box);
  const mine = () => S.tasks.filter(t => { const ar = t.approvalRequest; return ar && ar.status === 0 && (ar.usersIds || []).map(String).includes(String(ME.id)); });
  const allPending = () => S.tasks.filter(t => t.status === "Onay Bekliyor");
  function drawRibbon() {
    clear(ctx.ribbon).append(
      rgroup("Görünüm", rseg([["bana", "Onayımı bekleyenler (" + mine().length + ")"], ["tum", "Tüm bekleyen onaylar (" + allPending().length + ")"], ["gecmis", "Onay geçmişi"]], S.tab, x => { S.tab = x; draw(); }, "Görünüm")),
      rgroup("Veri", rbtn({ icon: "refresh", text: "Yenile", onclick: load }), rbtn({ icon: "excel", text: "Geçmişi Excel'e aktar", onclick: exportHist })));
  }
  async function load() {
    stateLoading(box, "Onaylar yükleniyor…");
    try {
      const [g, o] = await Promise.all([fetchAll("G", { includeApprovalRequest: true }), fetchAll("O").catch(() => [])]);
      if (!S.alive) return;
      S.tasks = g.map(taskModel);
      S.hist = o.map(r => ({ id: r._id, title: v(r, "O", "Başlık"), karar: lbl(v(r, "O", "Karar")), who: v(r, "O", "Onaylayan"), date: toDay(v(r, "O", "Tarih")),
        note: v(r, "O", "Not") || "", task: linkLabel(v(r, "O", "Görev")), taskId: linkIds(v(r, "O", "Görev"))[0], proj: linkLabel(v(r, "O", "Proje")), no: v(r, "O", "Kayıt No") }))
        .sort((a, b) => (b.no || 0) - (a.no || 0));
      draw();
    } catch (e) { stateError(box, e, load); }
  }
  function approvalCard(t, canDecide) {
    const errB = el("div", { class: "error-box", role: "alert" });
    const msg = el("textarea", { class: "input", rows: "2", placeholder: "Red gerekçesi (reddederken zorunlu)", "aria-label": "Red gerekçesi" });
    const ok = el("button", { class: "btn good", type: "button" }, icon("check", 16), " Onayla");
    const no = el("button", { class: "btn danger", type: "button" }, icon("undo", 16), " Reddet");
    const rid = t.approvalRequest?.requestId;
    const decide = async approve => {
      if (!approve && !msg.value.trim()) { errB.textContent = "Reddetmek için gerekçe yazın."; msg.setAttribute("aria-invalid", "true"); msg.focus(); return; }
      ok.disabled = no.disabled = true; clear(errB);
      try {
        const q = "approvalRequestId=" + encodeURIComponent(rid) + (approve ? "" : "&message=" + encodeURIComponent(msg.value.trim()));
        await api("POST", "/api/services/app/AutomationApprovalRequest/" + (approve ? "Approve" : "Reject") + "?" + q);
        toast(approve ? "Onaylandı — görev tamamlandı, ardıllar açılıyor." : "Reddedildi — görev revizyon için sorumluya döndü.", "ok", 4500);
        setTimeout(() => S.alive && load(), 1800);
      } catch (e) { if (!(e instanceof SessionGone)) { errB.textContent = e.message; ok.disabled = no.disabled = false; } }
    };
    ok.addEventListener("click", () => decide(true));
    no.addEventListener("click", () => decide(false));
    return el("article", { class: "card appr" },
      el("div", { class: "appr-h" }, el("h3", { text: t.name }), chip(t.status)),
      el("div", { class: "kc-meta" }, el("span", { text: t.projectName + " · " + (t.phaseName || "") }), " · ", el("span", { text: "Sorumlu: " + (userName(t.owner) || "—") }),
        " · ", el("span", { text: "Onaylayıcı: " + (userName(t.approver) || "—") }), " · ", el("span", { text: "Plan bitiş: " + fmtDay(t.end) })),
      t.desc ? el("p", { class: "crit-box" }, el("b", { text: "Kabul kriteri: " }), t.desc) : null,
      t.notes ? el("p", { class: "note", text: t.notes }) : null,
      t.files.length ? el("div", { class: "files" }, ...t.files.map(f => el("div", { class: "file" }, icon("excel", 16), el("span", { class: "fn", text: f.FileName || "dosya" }),
        el("button", { class: "btn sm", type: "button", text: "İndir", onclick: () => downloadFile(f).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); }) })))) : el("p", { class: "muted", text: "Doküman eklenmemiş." }),
      canDecide && rid ? el("div", null, errB, msg, el("div", { class: "quick" }, ok, no)) : el("p", { class: "hint", text: canDecide ? "Onay talebi henüz oluşmadı; birkaç saniye sonra yenileyin." : "Karar yetkisi: " + (userName(t.approver) || "onaylayıcı") }),
      el("div", { class: "quick" }, el("button", { class: "btn sm", type: "button", text: "Görevi aç", onclick: () => taskModal(t, () => load()) }),
        el("button", { class: "btn sm", type: "button", text: "Planda göster", onclick: () => go("plan", t.project, { sec: t.id }) })));
  }
  function draw() {
    drawRibbon();
    if (S.tab === "gecmis") {
      setStatus(S.hist.length + " onay kararı");
      if (!S.hist.length) { stateEmpty(box, "Henüz onay kararı yok", "Onaylanan ve reddedilen her görev burada iz kaydı olarak kalır.", null, "approve"); return; }
      const tbl = el("table", { class: "tbl" });
      tbl.append(el("thead", null, el("tr", null, ...["#", "Tarih", "Karar", "Görev", "Proje", "Onaylayan", "Not"].map(h => el("th", { text: h })))));
      const tb = el("tbody");
      S.hist.forEach(h => tb.append(el("tr", null, el("td", { text: String(h.no ?? "") }), el("td", { text: fmtDay(h.date) }), el("td", null, chip(h.karar)),
        el("td", { text: h.task || h.title }), el("td", { text: h.proj }), el("td", { text: userName(h.who) || "—" }), el("td", { text: h.note }))));
      tbl.append(tb);
      clear(box).append(el("div", { class: "card tbl-wrap" }, tbl));
      return;
    }
    const list = S.tab === "bana" ? mine() : allPending();
    setStatus(list.length + " onay bekliyor");
    if (!list.length) { stateEmpty(box, S.tab === "bana" ? "Onayınızı bekleyen görev yok" : "Bekleyen onay yok", "Bir görev onaya gönderildiğinde burada ve bildirimlerde görünür.", null, "approve"); return; }
    const mineIds = new Set(mine().map(t => t.id));
    clear(box).append(el("div", { class: "appr-list" }, ...list.map(t => approvalCard(t, mineIds.has(t.id)))));
  }
  function exportHist() {
    downloadCSV("onay_gecmisi.csv", [["#", "Tarih", "Karar", "Görev", "Proje", "Onaylayan", "Not"],
      ...S.hist.map(h => [h.no ?? "", h.date != null ? dayToISO(h.date) : "", h.karar, h.task || h.title, h.proj, userName(h.who), h.note])]);
  }
  drawRibbon();
  await load();
  return { unmount() { S.alive = false; } };
} };

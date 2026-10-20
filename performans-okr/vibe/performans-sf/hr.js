"use strict";
/* İK yöneticisi personası: döngü takibi, OKR çeyreği, kalibrasyon, şirket skoru, parametreler. */

function topDept(personId) {          // CEO'nun altındaki ilk seviye birim = departman
  const p = X.people.get(personId);
  let u = p && X.units.get(p.unitId);
  if (!u) return "—";
  while (u.parentId && X.units.get(u.parentId)?.parentId) u = X.units.get(u.parentId);
  return u.parentId ? u.name : "Yönetim (" + u.name + ")";
}
const RESP = { "Hedef Belirleme": "Çalışan", "Yönetici Onayında": "Yönetici", "Aktif": "Çalışan (gerçekleşen)",
  "Değerlendirme": "Yönetici (yetkinlik)", "Kalibrasyon": "İK" };
function yearSelect(key, def) {
  const years = X.periods.filter(p => p.type === "Yıl" && [...X.karne.values()].some(k => k.period === p.name)).map(p => p.name);
  const y = state.ctx[key] && years.includes(state.ctx[key]) ? state.ctx[key] : (def && years.includes(def) ? def : years.at(-1));
  const s = select(years, { value: y }, null);
  s.addEventListener("change", () => { state.ctx[key] = s.value; render(); });
  return [y, s];
}

// ─── Döngüler ──────────────────────────────────────────────────────────────
function periodDrawer(p) {
  const order = ["Planlama", "Aktif", "Kapanış", "Kapalı"];
  const next = order[order.indexOf(p.status) + 1];
  const effect = {
    "Aktif": p.type === "Yıl" ? "Tüm aktif çalışanlara Hedef Belirleme durumunda karne açılır ve çalışanlara bildirim gider." : "Çeyrek OKR'ları bu döneme yazılabilir.",
    "Kapanış": p.type === "Yıl" ? "Aktif karneler Değerlendirme'ye geçer; yetkinlik formları açılır, çalışan ve yöneticilere bildirim gider." : "Aktif OKR'lar Kapanış'a geçer, KR takibi biter, sahiplere kapanış bildirimi gider.",
    "Kapalı": "Dönem arşivlenir."
  }[next];
  const body = el("div", {},
    el("dl", { class: "kv" }, el("dt", { text: "Tür" }), el("dd", { text: p.type }), el("dt", { text: "Tarihler" }), el("dd", { text: `${fdate(p.start)} – ${fdate(p.end)}` }),
      el("dt", { text: "Hedef giriş son tarihi" }), el("dd", { text: fdate(p.due) }), el("dt", { text: "Durum" }), el("dd", {}, chip(p.status, p.status === "Aktif" ? "good" : ""))),
    next ? el("div", { class: "callout warn section" }, el("div", {}, el("b", { text: `“${next}” yapıldığında: ` }), effect)) : el("p", { class: "muted section", text: "Dönem kapalı." }));
  drawer.open("Dönem · " + p.name, body, next ? [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }),
    el("button", { class: "btn primary", text: `${next} yap`, onclick: e => busy(e.currentTarget, async () => {
      await updateRec("donem", p.id, { [F.donem.durum]: next });
      drawer.close(); await refreshLater(["donem", "karne", "obj", "kr"], `${p.name} → ${next}. Otomasyonlar çalışıyor.`);
    }) })] : []);
}

function hrCycle(me) {
  const [year, ysel] = yearSelect("cycleYear", X.year?.name);
  const ks = [...X.karne.values()].filter(k => k.period === year && k.status !== "İptal");
  const total = ks.length || 1;
  const counts = Object.fromEntries(KARNE_DURUM.map(s => [s, ks.filter(k => k.status === s).length]));
  const cur = KARNE_DURUM.findIndex(s => counts[s] > 0);
  const phases = el("div", { class: "phases" }, KARNE_DURUM.map((s, i) => {
    const passed = ks.filter(k => KARNE_DURUM.indexOf(k.status) > i).length;
    return el("div", { class: "phase" + (i === cur ? " current" : "") },
      el("div", { class: "t", text: s }), el("div", { class: "n", text: String(counts[s]) }),
      el("div", { class: "sub", text: `%${Math.round(passed / total * 100)} geçti` }), bar(passed / total, i === cur ? "brand" : "done"));
  }));
  const depts = [...new Set(ks.map(k => topDept(k.personId)))].sort((a, b) => a.localeCompare(b, "tr"));
  const heat = el("div", { class: "tbl-wrap" }, el("table", { class: "heat" },
    el("thead", {}, el("tr", {}, el("th", { text: "Departman" }), KARNE_DURUM.map(s => el("th", { class: "num", text: s })))),
    el("tbody", {}, depts.map(d => el("tr", {}, el("td", { style: { fontWeight: 600 }, text: d }), KARNE_DURUM.map(s => {
      const n = ks.filter(k => k.status === s && topDept(k.personId) === d).length;
      const late = ["Hedef Belirleme", "Yönetici Onayında"].includes(s) && n;
      return el("td", { class: "h", style: { background: n ? (late ? `rgba(231,101,0,${0.12 + n * 0.12})` : `rgba(17,66,133,${0.08 + n * 0.08})`) : null }, text: n || "" });
    }))))));
  const fDept = state.ctx.waitDept || "";
  const waiting = ks.filter(k => k.status !== "Tamamlandı" && k.status !== "Aktif" && (!fDept || topDept(k.personId) === fDept))
    .sort((a, b) => KARNE_DURUM.indexOf(a.status) - KARNE_DURUM.indexOf(b.status));
  const dsel = select(depts, { value: fDept }, "Tüm departmanlar");
  dsel.addEventListener("change", () => { state.ctx.waitDept = dsel.value; render(); });
  const periods = X.periods.filter(p => !p.name.startsWith(String(Number(year) - 2)));
  return el("div", {},
    head("Performans Döngüleri", "Dönemlerin durumu, karnelerin aşamaları ve kimde beklediği.", ysel),
    el("div", { class: "grid g4" }, periods.map(p => el("button", { class: "card", style: { textAlign: "left", cursor: "pointer" }, onclick: () => periodDrawer(p) },
      el("div", { class: "row" }, el("b", { text: p.name }), el("span", { class: "spacer" }), chip(p.status, p.status === "Aktif" ? "good" : p.status === "Kapanış" ? "warn" : p.status === "Kapalı" ? "done" : "")),
      el("div", { class: "sub", text: `${p.type} · ${fdate(p.start)} – ${fdate(p.end)}` })))),
    el("div", { class: "section" }, el("h2", { text: `${year} karne döngüsü · ${ks.length} karne` }), phases),
    el("div", { class: "section" }, el("h2", { text: "Departman × aşama" }), heat),
    el("div", { class: "section" },
      el("div", { class: "row wrap", style: { marginBottom: "10px" } }, el("h2", { text: `Kimde bekliyor · ${waiting.length}` }), el("span", { class: "spacer" }), dsel,
        waiting.length ? el("button", { class: "btn", text: "Listedekilere hatırlat", onclick: e => busy(e.currentTarget, async () => {
          for (const k of waiting.slice(0, 25)) await addComment("karne", k.id, `Hatırlatma (İK): karne “${k.status}” aşamasında bekliyor. Sorumlu: ${RESP[k.status] || "—"}.`);
          toast(`${Math.min(25, waiting.length)} karneye hatırlatma eklendi.`, "good");
        }) }) : null),
      waiting.length ? el("div", { class: "tbl-wrap" }, el("table", {},
        el("thead", {}, el("tr", {}, ["Çalışan", "Departman", "Aşama", "Bekleyen", "Kişi", "Onay süresi"].map(t => el("th", { text: t })))),
        el("tbody", {}, waiting.map(k => {
          const p = X.people.get(k.personId), m = managerOf(k.personId);
          const who = RESP[k.status]?.startsWith("Yönetici") ? m : RESP[k.status]?.startsWith("Çalışan") ? p : me;
          return el("tr", {}, el("td", {}, personTag(p, false, true)), el("td", { text: topDept(k.personId) }),
            el("td", {}, chip(k.status, karneTone(k.status))), el("td", { text: RESP[k.status] || "—" }), el("td", { text: who?.name || "—" }),
            el("td", { class: "sub", text: k.approval?.expiryDateUtc ? "son: " + fdate(k.approval.expiryDateUtc) : "" }));
        })))) : empty("Bekleyen karne yok.", "✓")));
}

// ─── OKR çeyreği ───────────────────────────────────────────────────────────
function hrOkr() {
  const q = X.quarter?.name;
  const objs = [...X.obj.values()].filter(o => o.period === q && o.status !== "İptal");
  const active = objs.filter(o => o.status === "Aktif");
  const krs = X.kr.filter(kr => active.some(o => o.id === kr.objId));
  const fresh = krs.filter(kr => !needsCheckin(kr));
  const tones = { good: 0, warn: 0, bad: 0, none: 0 };
  for (const o of active) tones[objTone(o)]++;
  const byDept = {};
  for (const kr of krs) {
    const o = X.obj.get(kr.objId);
    const d = o.ownerId ? topDept(o.ownerId) : (o.dept || "Şirket");
    (byDept[d] ||= { n: 0, ok: 0, prog: [] }).n++;
    if (!needsCheckin(kr)) byDept[d].ok++;
    byDept[d].prog.push(kr.progress || 0);
  }
  const late = krs.filter(needsCheckin);
  return el("div", {},
    head(`Hedef Yönetimi · ${q || ""}`, "Hizalama, gidişat ve check-in disiplini."),
    el("div", { class: "grid g4" },
      stat("Objective", String(objs.length), `${active.length} aktif · ${objs.filter(o => o.status === "Onayda").length} onayda · ${objs.filter(o => o.status === "Taslak").length} taslak`, true),
      stat("Check-in uyumu", krs.length ? pct(fresh.length / krs.length) : "–", `${fresh.length}/${krs.length} KR son 7 günde güncel`),
      stat("Ortalama ilerleme", active.length ? pct(active.reduce((s, o) => s + (o.progress || 0), 0) / active.length) : "–", "Aktif objective'ler"),
      stat("Ortalama güven", active.length ? fmt(active.reduce((s, o) => s + (o.conf || 0), 0) / active.length, 1) : "–", "1–10")),
    el("div", { class: "grid g2 section" },
      el("div", { class: "card" }, el("h2", { text: "Gidişat dağılımı" }),
        ["good", "warn", "bad", "none"].map(t => el("div", { style: { marginBottom: "10px" } },
          el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "13px" } }, chip(TONE_LABEL[t], t), el("b", { text: `${tones[t]} / ${active.length}` })),
          bar(active.length ? tones[t] / active.length : 0, t)))),
      el("div", { class: "card" }, el("h2", { text: "Departmana göre check-in uyumu" }),
        Object.entries(byDept).sort((a, b) => a[0].localeCompare(b[0], "tr")).map(([d, v]) => el("div", { style: { marginBottom: "10px" } },
          el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "13px" } }, el("span", { text: d }),
            el("span", { class: "sub", text: `${v.ok}/${v.n} güncel · ilerleme ${pct(v.prog.reduce((a, b) => a + b, 0) / v.prog.length)}` })),
          bar(v.ok / v.n, v.ok / v.n >= 0.8 ? "good" : v.ok / v.n >= 0.5 ? "warn" : "bad"))))),
    el("div", { class: "section" }, el("h2", { text: `Check-in gecikenler · ${late.length}`, style: { marginBottom: "10px" } }),
      late.length ? el("div", { class: "tbl-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, ["Key Result", "Objective", "Sahip", "Son check-in", ""].map(t => el("th", { text: t })))),
        el("tbody", {}, late.map(kr => { const o = X.obj.get(kr.objId); const last = lastCheckin(kr)?.date || kr.lastCi;
          return el("tr", {}, el("td", { style: { fontWeight: 600 }, text: kr.name }), el("td", { class: "sub", text: o.name }),
            el("td", { text: o.ownerId ? personName(o.ownerId) : (o.dept || "Şirket") }), el("td", { style: { color: "var(--bad)" }, text: last ? `${fdate(last)} (${daysSince(last)} gün)` : "hiç" }),
            el("td", {}, el("button", { class: "btn sm", text: "Hatırlat", onclick: e => nudge(kr, e.currentTarget) })));
        })))) : empty("Geciken check-in yok.", "✓")));
}

// ─── Kalibrasyon ───────────────────────────────────────────────────────────
const SIM = new Map();                 // kaydedilmeyen önizleme hareketleri (karne id → grup)
function hrCalib() {
  const [year, ysel] = yearSelect("calYear", X.year?.name);
  const ks = [...X.karne.values()].filter(k => k.period === year && k.status !== "İptal");
  const fDept = state.ctx.calDept || "";
  const depts = [...new Set(ks.map(k => topDept(k.personId)))].sort((a, b) => a.localeCompare(b, "tr"));
  const dsel = select(depts, { value: fDept }, "Tüm departmanlar");
  dsel.addEventListener("change", () => { state.ctx.calDept = dsel.value; render(); });
  const list = ks.filter(k => !fDept || topDept(k.personId) === fDept);
  const editableK = k => ["Değerlendirme", "Kalibrasyon"].includes(k.status);
  const anyEditable = list.some(editableK);
  const post = k => SIM.get(k.id) || k.calib || k.final || k.group;
  const target = state.ctx.calTarget || [10, 20, 40, 20, 10];

  const dist = el("div", { class: "dist" }, GRUPLAR.map((gr, i) => {
    const pre = list.filter(k => k.group === gr).length, now = list.filter(k => post(k) === gr).length, n = list.length || 1;
    const t = input({ type: "number", min: 0, max: 100, value: target[i], style: { width: "52px", padding: "2px 4px", textAlign: "center" }, "aria-label": "Hedef % " + gr,
      onchange: e => { const tt = [...target]; tt[i] = num(e.target.value) || 0; state.ctx.calTarget = tt; render(); } });
    return el("div", { class: "col" },
      el("div", { class: "bars" },
        el("i", { class: "t-none", title: `Hesaplanan ${pre}`, style: { height: (pre / n * 85 + 2) + "px" } }),
        el("i", { class: "t-brand", title: `Kalibre ${now}`, style: { height: (now / n * 85 + 2) + "px" } }),
        el("i", { class: "t-warn", title: `Hedef %${target[i]}`, style: { height: (target[i] / 100 * 85 + 2) + "px", opacity: .55 } })),
      el("div", { style: { fontWeight: 700 }, text: GRUP_KISA[i] }),
      el("div", { class: "sub", text: `${pre} → ${now} kişi · %${Math.round(now / n * 100)}` }),
      el("div", { class: "row", style: { justifyContent: "center", gap: "4px" } }, el("span", { class: "sub", text: "hedef %" }), t));
  }));

  const board = el("div", { class: "calib" }, GRUPLAR.map((gr, i) => {
    const people = list.filter(k => post(k) === gr).sort((a, b) => (b.total || 0) - (a.total || 0));
    const drop = el("div", { class: "drop", "data-group": gr });
    drop.addEventListener("dragover", e => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", e => {
      e.preventDefault(); drop.classList.remove("over");
      const k = X.karne.get(e.dataTransfer.getData("text/plain"));
      if (k) moveTo(k, gr);
    });
    for (const k of people) {
      const p = X.people.get(k.personId);
      const moved = post(k) !== k.group;
      const c = el("div", { class: "pcard" + (moved ? " moved" : ""), draggable: "true", tabindex: "0", role: "button", "aria-label": `${p?.name}, ${GRUP_KISA[i]}` },
        el("div", { class: "row" }, avatar(p?.name || "?", true), el("b", { style: { fontSize: "13px" }, text: p?.name || "—" })),
        el("div", { class: "s" }, el("span", { text: topDept(k.personId) }), el("b", { text: fmt(k.total, 1) })),
        moved ? el("div", { class: "sub", text: "önce: " + (GRUP_KISA[GRUPLAR.indexOf(k.group)] || "–") }) : null);
      c.addEventListener("dragstart", e => e.dataTransfer.setData("text/plain", k.id));
      c.addEventListener("click", () => calibDrawer(k));
      c.addEventListener("keydown", e => { if (e.key === "Enter") calibDrawer(k); });
      drop.append(c);
    }
    return el("section", { class: "bucket" }, el("header", {}, el("div", { class: "t", text: gr }), el("div", { class: "c", text: `${people.length} kişi` })), drop);
  }));

  function moveTo(k, gr) {
    if (post(k) === gr) return;
    if (!editableK(k)) {
      if (k.status === "Tamamlandı") { toast("Tamamlanmış karne kalibre edilemez.", "bad"); return; }
      SIM.set(k.id, gr); render(); return;
    }
    busy(null, async () => { await updateRec("karne", k.id, { [F.karne.kalibre]: gr }); SIM.delete(k.id); await refreshLater(["karne"], `${personName(k.personId)} → ${gr}`); });
  }

  const banner = anyEditable ? null : el("div", { class: "callout warn", style: { marginBottom: "14px" } },
    list.every(k => k.status === "Tamamlandı") ? "Bu yılın karneleri tamamlandı; dağılım salt okunur." :
      "Karneler henüz Değerlendirme/Kalibrasyon aşamasında değil. Kartları sürükleyerek senaryo deneyebilirsin; bu hareketler kaydedilmez.",
    SIM.size ? el("button", { class: "btn sm", style: { marginLeft: "auto" }, text: "Senaryoyu sıfırla", onclick: () => { SIM.clear(); render(); } }) : null);
  return el("div", {},
    head("Kalibrasyon", "Hesaplanan performans gruplarını departmanlar arasında dengele. Gri: hesaplanan · lacivert: kalibre · turuncu: hedef dağılım.", ysel, dsel),
    banner, el("div", { class: "card", style: { marginBottom: "14px" } }, dist), board);
}
function calibDrawer(k) {
  const p = X.people.get(k.personId);
  const editable = ["Değerlendirme", "Kalibrasyon"].includes(k.status);
  const grp = select(GRUPLAR, { value: k.calib || "" }, "— Kalibrasyon yok (hesaplanan geçerli) —");
  const note = textarea({ value: k.calibNote || "", placeholder: "Gerekçe: hangi kanıtla grup değişti?" });
  if (!editable) { grp.disabled = true; note.disabled = true; }
  const body = el("div", {}, personTag(p, `${topDept(k.personId)} · ${k.form}`), karneStepper(k.status),
    el("dl", { class: "kv section" },
      el("dt", { text: "KPI skoru" }), el("dd", { text: fmt(k.kpiScore, 2) }),
      el("dt", { text: "Yetkinlik skoru" }), el("dd", { text: fmt(k.yetScore, 1) }),
      el("dt", { text: "Toplam puan" }), el("dd", { text: fmt(k.total, 2) }),
      el("dt", { text: "Hesaplanan grup" }), el("dd", {}, chip(k.group || "–", groupTone(k.group))),
      el("dt", { text: "Final grup" }), el("dd", {}, k.final ? chip(k.final, groupTone(k.final)) : "–"),
      el("dt", { text: "OKR (bilgi)" }), el("dd", { text: k.okrCount ? `${k.okrCount} OKR · ort. ${fmt(k.okrAvg, 2)}` : "–" })),
    el("div", { class: "section" }, field("Kalibre grup", grp), field("Kalibrasyon notu", note)),
    editable ? null : el("p", { class: "muted", text: "Bu karne kalibrasyon aşamasında değil; alanlar salt okunur." }));
  const acts = [el("button", { class: "btn", text: "Kapat", onclick: drawer.close })];
  if (editable) {
    acts.push(el("button", { class: "btn", text: "Kaydet", onclick: e => busy(e.currentTarget, async () => {
      await updateRec("karne", k.id, { [F.karne.kalibre]: grp.value || null, [F.karne.kalNot]: note.value.trim() || null });
      drawer.close(); await refreshLater(["karne"], "Kalibrasyon kaydedildi.");
    }) }));
    if (k.status === "Değerlendirme") acts.push(el("button", { class: "btn primary", text: "Kalibrasyona al", onclick: e => busy(e.currentTarget, async () => {
      await updateRec("karne", k.id, { [F.karne.durum]: "Kalibrasyon" }); drawer.close(); await refreshLater(["karne"], "Karne kalibrasyonda.");
    }) }));
    if (k.status === "Kalibrasyon") acts.push(el("button", { class: "btn primary", text: "Tamamla", onclick: e => busy(e.currentTarget, async () => {
      await updateRec("karne", k.id, { [F.karne.kalibre]: grp.value || null, [F.karne.kalNot]: note.value.trim() || null });
      await updateRec("karne", k.id, { [F.karne.durum]: "Tamamlandı" }); drawer.close();
      await refreshLater(["karne"], "Karne tamamlandı, final grup yazılıyor.");
    }) }));
  }
  drawer.open("Kalibrasyon · " + (p?.name || ""), body, acts);
}

// ─── Şirket skoru ──────────────────────────────────────────────────────────
function hrScore() {
  const [year, ysel] = yearSelect("scoreYear", X.periods.filter(p => p.type === "Yıl" && p.status === "Kapalı").at(-1)?.name);
  const ks = [...X.karne.values()].filter(k => k.period === year && k.status !== "İptal");
  const done = ks.filter(k => k.status === "Tamamlandı");
  const avg = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
  const tot = ks.map(k => k.total).filter(v => v != null);
  const byDept = {};
  for (const k of ks) (byDept[topDept(k.personId)] ||= []).push(k);
  const maxAvg = Math.max(1, ...Object.values(byDept).map(a => avg(a.map(k => k.total ?? k.kpiScore ?? 0)) || 0));
  const grpOf = k => k.final || k.calib || k.group;
  return el("div", {},
    head(`Şirket Performans Skoru · ${year}`, done.length === ks.length ? "Tüm karneler tamamlandı." : `${done.length}/${ks.length} karne tamamlandı; tamamlanmayanlarda puan anlık.`, ysel),
    el("div", { class: "grid g4" },
      stat("Ortalama toplam puan", fmt(avg(tot), 1), `${tot.length} karne`, true),
      stat("Ortalama KPI skoru", fmt(avg(ks.map(k => k.kpiScore).filter(v => v != null)), 1), "%90 ağırlık"),
      stat("Ortalama yetkinlik", fmt(avg(ks.map(k => k.yetScore).filter(v => v != null)), 1), "%10 ağırlık"),
      stat("Tamamlanan", `${done.length}/${ks.length}`, "Final grup yazılmış")),
    el("div", { class: "grid g2 section" },
      el("div", { class: "card" }, el("h2", { text: "Departmana göre ortalama puan" }),
        Object.entries(byDept).sort((a, b) => a[0].localeCompare(b[0], "tr")).map(([d, a]) => {
          const v = avg(a.map(k => k.total ?? k.kpiScore ?? 0));
          return el("div", { style: { marginBottom: "10px" } }, el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "13px" } },
            el("span", { text: `${d} · ${a.length} kişi` }), el("b", { text: fmt(v, 1) })), bar(v / maxAvg, v >= 90 ? "good" : v >= 60 ? "warn" : "bad"));
        })),
      el("div", { class: "card" }, el("h2", { text: "Performans grubu dağılımı" }),
        GRUPLAR.map((gr, i) => { const n = ks.filter(k => grpOf(k) === gr).length;
          return el("div", { style: { marginBottom: "10px" } }, el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "13px" } },
            chip(gr, groupTone(gr)), el("b", { text: `${n} · %${Math.round(n / (ks.length || 1) * 100)}` })), bar(n / (ks.length || 1), groupTone(gr) === "brand" ? "brand" : groupTone(gr)));
        }))),
    el("div", { class: "section" }, el("h2", { text: "Karneler", style: { marginBottom: "10px" } }),
      el("div", { class: "tbl-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, ["Çalışan", "Departman", "Form türü", "KPI", "Yetkinlik", "Toplam", "Grup", "Durum"].map((t, i) => el("th", { class: i >= 3 && i <= 5 ? "num" : "", text: t })))),
        el("tbody", {}, ks.sort((a, b) => (b.total || 0) - (a.total || 0)).map(k => el("tr", { style: { cursor: "pointer" }, onclick: () => calibDrawer(k) },
          el("td", {}, personTag(X.people.get(k.personId), false, true)), el("td", { text: topDept(k.personId) }), el("td", { text: k.form || "–" }),
          el("td", { class: "num", text: fmt(k.kpiScore, 1) }), el("td", { class: "num", text: fmt(k.yetScore, 1) }), el("td", { class: "num", style: { fontWeight: 700 }, text: fmt(k.total, 1) }),
          el("td", {}, grpOf(k) ? chip(grpOf(k), groupTone(grpOf(k))) : "–"), el("td", {}, chip(k.status, karneTone(k.status))))))))));
}

// ─── Parametreler ──────────────────────────────────────────────────────────
function hrSettings() {
  const forms = el("div", { class: "grid g3" }, X.forms.map(f => {
    const ins = ["op", "pr", "ku", "ye"].map(k => input({ type: "number", min: 0, max: 100, value: f[k] ?? 0 }));
    const sum = el("b", {});
    const upd = () => { const s = ins.reduce((a, i) => a + (num(i.value) || 0), 0); sum.textContent = `Toplam %${s}`; sum.style.color = s === 100 ? "var(--good)" : "var(--bad)"; return s; };
    ins.forEach(i => i.addEventListener("input", upd)); upd();
    return el("div", { class: "card" }, el("h3", { text: f.name }),
      el("div", { class: "two" }, field("Operasyonel %", ins[0]), field("Proje %", ins[1])),
      el("div", { class: "two" }, field("Kurumsal %", ins[2]), field("Yetkinlik %", ins[3])),
      el("div", { class: "row" }, sum, el("span", { class: "spacer" }), el("button", { class: "btn sm primary", text: "Kaydet", onclick: e => {
        if (upd() !== 100) { toast("Oranların toplamı 100 olmalı.", "bad"); return; }
        busy(e.currentTarget, async () => {
          await updateRec("form", f.id, { [F.form.op]: num(ins[0].value), [F.form.pr]: num(ins[1].value), [F.form.ku]: num(ins[2].value), [F.form.ye]: num(ins[3].value) });
          await refreshLater(["form"], `${f.name} oranları kaydedildi. Yeni açılan karnelerde geçerli.`);
        });
      } })));
  }));
  const yet = el("div", { class: "tbl-wrap" }, el("table", {}, el("thead", {}, el("tr", {}, ["Yetkinlik", "Davranış göstergeleri", "Form türleri", "Aktif"].map(t => el("th", { text: t })))),
    el("tbody", {}, X.yet.map(y => el("tr", {}, el("td", { style: { fontWeight: 600 }, text: y.name }), el("td", { class: "sub", text: y.def || "" }),
      el("td", {}, el("div", { class: "row wrap" }, y.forms.map(f => chip(f, "", true)))),
      el("td", {}, el("button", { class: "btn sm" + (y.active ? " good" : ""), "aria-pressed": y.active ? "true" : "false", text: y.active ? "Aktif" : "Pasif",
        onclick: e => busy(e.currentTarget, async () => { await updateRec("yet", y.id, { [F.yet.aktif]: y.active ? 0 : 1 }); await refreshLater(["yet"], `${y.name}: ${y.active ? "pasif" : "aktif"}`); }) })))))));
  const rules = el("div", { class: "grid g2" },
    el("div", { class: "card" }, el("h3", { text: "Hedef puanı kuralı" }), el("dl", { class: "kv" },
      el("dt", { text: "Gerçekleşme < %80" }), el("dd", { text: "0 puan" }), el("dt", { text: "%80 – %100" }), el("dd", { text: "60 → 100 (her puan 2)" }),
      el("dt", { text: "%100 – %120" }), el("dd", { text: "100 → 120 (her puan 1)" }), el("dt", { text: "≥ %120" }), el("dd", { text: "120 (üst sınır)" }))),
    el("div", { class: "card" }, el("h3", { text: "Performans grubu eşikleri" }), el("dl", { class: "kv" },
      ["< 60", "60 – 89,99", "90 – 100,99", "101 – 110,99", "≥ 111"].flatMap((t, i) => [el("dt", { text: t }), el("dd", {}, chip(GRUPLAR[i], groupTone(GRUPLAR[i])))]))));
  return el("div", {}, head("Yönetici Merkezi", "Form türü oranları, yetkinlik seti ve puanlama kuralları. Eşik ve kurallar Workiom formül/otomasyonlarında tanımlı."),
    el("h2", { text: "Form türleri", style: { marginBottom: "10px" } }), forms,
    el("div", { class: "section" }, el("h2", { text: "Yetkinlikler", style: { marginBottom: "10px" } }), yet),
    el("div", { class: "section" }, rules));
}

function hrTodos(me) {
  const out = [];
  const year = X.year?.name;
  const ks = [...X.karne.values()].filter(k => k.period === year && k.status !== "İptal");
  const n = st => ks.filter(k => k.status === st).length;
  for (const p of X.periods.filter(p => p.status === "Aktif" && p.due)) {
    const d = Math.ceil((Date.parse(p.due) - Date.now()) / 864e5);
    if (d >= 0 && d <= 30) out.push({ icon: "calendar", cat: "Dönem", title: `${p.name} hedef girişi ${d} gün sonra kapanıyor`, sub: `Son tarih ${fdate(p.due)}`, action: "Döngüye git", fn: () => go("hr", "cycle") });
  }
  if (n("Hedef Belirleme")) out.push({ icon: "target", cat: "Performans döngüsü", title: `${n("Hedef Belirleme")} çalışan hedef belirlemede bekliyor`, sub: `${year} karneleri · hatırlatma gönderebilirsin`, action: "Kimde bekliyor", fn: () => go("hr", "cycle") });
  if (n("Yönetici Onayında")) out.push({ icon: "approve", cat: "Performans döngüsü", title: `${n("Yönetici Onayında")} form yönetici onayında`, sub: "Onay süresi dolanları takip et", action: "Kimde bekliyor", fn: () => go("hr", "cycle") });
  if (n("Kalibrasyon")) out.push({ icon: "scale", cat: "Kalibrasyon", title: `${n("Kalibrasyon")} çalışan kalibrasyon oturumunda`, sub: "Grupları departmanlar arasında dengele", action: "Oturumu aç", fn: () => go("hr", "calib") });
  const q = X.quarter?.name;
  const krs = X.kr.filter(kr => X.obj.get(kr.objId)?.status === "Aktif" && X.obj.get(kr.objId)?.period === q);
  const late = krs.filter(needsCheckin).length;
  if (late) out.push({ icon: "clock", cat: "OKR", title: `${late} anahtar sonucun check-in'i 7 günü geçti`, sub: `${q} · ${krs.length} aktif KR`, action: "Hedef yönetimi", fn: () => go("hr", "okr") });
  return out;
}

PV.hr = {
  heroSub: me => `${me.unit} · ${X.year?.name || ""} performans dönemi · ${X.quarter?.name || ""}`,
  quick: me => [
    { icon: "calendar", label: "Dönem yönetimi", sub: "Aç, kapat, aşama geçir", fn: () => go("hr", "cycle") },
    { icon: "scale", label: "Kalibrasyon oturumu", sub: X.year?.name, fn: () => go("hr", "calib") },
    { icon: "chart", label: "Şirket skoru", sub: "Departman ve grup dağılımı", fn: () => go("hr", "score") },
    { icon: "settings", label: "Yönetici Merkezi", sub: "Form türleri, yetkinlikler", fn: () => go("hr", "settings") }],
  todos: hrTodos,
  tilesTitle: "İK Analitiği",
  tiles: me => {
    const year = X.year?.name;
    const ks = [...X.karne.values()].filter(k => k.period === year && k.status !== "İptal");
    const approved = ks.filter(k => !["Hedef Belirleme", "Yönetici Onayında"].includes(k.status)).length;
    const q = X.quarter?.name;
    const objs = [...X.obj.values()].filter(o => o.period === q && o.status === "Aktif");
    const krs = X.kr.filter(kr => objs.some(o => o.id === kr.objId));
    const fresh = krs.filter(kr => !needsCheckin(kr)).length;
    const risk = objs.filter(o => ["warn", "bad"].includes(objTone(o))).length;
    const r = ks.length ? approved / ks.length : 0;
    return [
      { title: "Performans Döngüsü", sub: year, value: `%${Math.round(r * 100)}`, tone: r >= .8 ? "good" : r >= .5 ? "warn" : "bad", icon: "calendar", foot: `${approved}/${ks.length} form onaylı`, fn: () => go("hr", "cycle") },
      { title: "Check-in Disiplini", sub: q, value: krs.length ? `%${Math.round(fresh / krs.length * 100)}` : "–", tone: krs.length && fresh / krs.length < .7 ? "warn" : "good", icon: "trend", foot: `${fresh}/${krs.length} KR güncel`, fn: () => go("hr", "okr") },
      { title: "Riskli Hedefler", sub: q, value: String(risk), tone: risk ? "bad" : "good", icon: "flag", foot: `${objs.length} aktif hedeften`, fn: () => go("hr", "okr") },
      { title: "Kalibrasyon", sub: year, value: String(ks.filter(k => k.status === "Kalibrasyon").length), icon: "scale", foot: "oturumdaki çalışan", fn: () => go("hr", "calib") },
      { title: "Geri Bildirim", sub: "Toplam kayıt", value: String(X.gb.length), icon: "chat", foot: `${X.gb.filter(f => f.type === "Takdir").length} takdir`, fn: () => go("hr", "score") }];
  },
  tabs: [
    { id: "home", label: "Ana Sayfa", icon: "home", render: sfHome, badge: me => hrTodos(me).length },
    { id: "cycle", label: "Performans Döngüleri", icon: "calendar", render: hrCycle },
    { id: "okr", label: "Hedef Yönetimi (OKR)", icon: "target", render: hrOkr },
    { id: "calib", label: "Kalibrasyon", icon: "scale", render: hrCalib },
    { id: "score", label: "Şirket Skoru", icon: "chart", render: hrScore },
    { id: "settings", label: "Yönetici Merkezi", icon: "settings", render: hrSettings }
  ]
};

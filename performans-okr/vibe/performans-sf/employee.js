"use strict";
/* Çalışan personası + yönetici ekranının da kullandığı ortak OKR / check-in / geri bildirim bileşenleri. */

// ─── Ortak: OKR seçimleri ──────────────────────────────────────────────────
const myObjectives = (personId, period = X.quarter?.name) =>
  [...X.obj.values()].filter(o => o.ownerId === personId && o.period === period && o.status !== "İptal");
const deptObjectives = (unitId, period = X.quarter?.name) =>
  [...X.obj.values()].filter(o => o.level === "Departman" && o.deptId === unitId && o.period === period && o.status !== "İptal");
const companyObjectives = (period = X.quarter?.name) =>
  [...X.obj.values()].filter(o => o.level === "Şirket" && o.period === period && o.status !== "İptal");
const lastCheckin = kr => X.ciOf(kr.id).at(-1) || null;
function needsCheckin(kr) {
  const o = X.obj.get(kr.objId);
  if (!o || o.status !== "Aktif") return false;
  const last = lastCheckin(kr)?.date || kr.lastCi;
  return !last || daysSince(last) > 7;
}

// ─── Ortak: OKR kartı ──────────────────────────────────────────────────────
function okrCard(o, opts = {}) {
  const tone = objTone(o);
  const krs = X.krOf(o.id);
  const parent = o.parentId ? X.obj.get(o.parentId) : null;
  const owner = o.ownerId ? X.people.get(o.ownerId) : null;
  const meta = el("div", { class: "meta" },
    chip(o.status, o.status === "Aktif" ? "good" : o.status === "Onayda" ? "warn" : o.status === "Kapandı" ? "done" : "", false),
    chip(TONE_LABEL[tone], tone),
    o.type ? chip(o.type.startsWith("Zorunlu") ? "Zorunlu" : "İddialı", "brand", true) : null,
    chip(o.level + (o.level === "Departman" ? " · " + (o.dept || "") : ""), "", true),
    owner && opts.showOwner ? chip(owner.name, "", true) : null);
  const ctx = parent ? el("div", { class: "sub", style: { marginTop: "6px" } }, "↑ Katkı verdiği: ", el("b", { text: parent.name })) : null;
  const actions = el("div", { class: "row wrap", style: { marginTop: "10px" } });
  if (opts.canSubmit && o.status === "Taslak")
    actions.append(el("button", { class: "btn sm primary", text: "Onaya gönder", onclick: e => submitObjective(o, e.currentTarget) }));
  if (o.status === "Onayda") actions.append(chip(o.approval ? "Onaylayıcıda bekliyor" : "Onay isteği oluşuyor…", "warn", true));
  if (opts.approve && o.approval) actions.append(...approvalButtons(o.approval, o.name, ["obj", "kr"]));
  if (opts.extra) actions.append(...opts.extra(o));

  const card = el("div", { class: "okr" + (opts.ghost ? " parent" : "") },
    el("div", { class: "okr-head" },
      el("div", {}, el("h3", { text: o.name }), meta, ctx, actions.childNodes.length ? actions : null),
      el("div", { class: "prog" },
        el("div", { class: "pct", text: pct(o.progress) }),
        el("div", { class: "sub", text: o.expected != null && o.status === "Aktif" ? `Bugün beklenen ${pct(o.expected)}` : o.closeScore != null ? `Kapanış puanı ${fmt(o.closeScore, 2)}` : "" }),
        bar(o.progress, tone, o.status === "Aktif" ? o.expected : null, true))));
  if (!opts.collapsed) for (const kr of krs) card.append(krRow(kr, o, opts));
  if (!krs.length && !opts.collapsed) card.append(el("div", { class: "kr" }, el("span", { class: "muted", text: "Henüz Key Result yok." })));
  return card;
}

function krRow(kr, o, opts = {}) {
  const tone = krTone(kr, o);
  const cis = X.ciOf(kr.id);
  const last = cis.at(-1);
  const late = needsCheckin(kr);
  const vals = kr.type === "Kilometre Taşı"
    ? (kr.current >= 1 ? "Tamamlandı" : "Tamamlanmadı")
    : `${fmt(kr.start, 2)} → ${fmt(kr.current, 2)} / ${fmt(kr.target, 2)} ${kr.unit || ""}`;
  return el("div", { class: "kr" },
    el("div", {}, el("div", { class: "nm", text: kr.name }),
      el("div", { class: "vals" }, vals, kr.sourceKpi ? el("span", { text: " · KPI'dan beslenir" }) : null)),
    el("div", {}, el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" } },
      chip(TONE_LABEL[tone], tone), el("b", { text: pct(kr.progress) })), bar(kr.progress, tone, o.status === "Aktif" ? o.expected : null)),
    el("div", {}, confBars(cis), el("div", { class: "sub", style: { color: late ? "var(--bad)" : null }, text: last ? `Son: ${fdate(last.date)}` : "Check-in yok" })),
    el("div", {}, opts.canCheckin && o.status === "Aktif"
      ? el("button", { class: "btn sm" + (late ? " primary" : ""), text: "Check-in", onclick: () => checkinDrawer(kr, o) })
      : opts.onNudge && late ? el("button", { class: "btn sm", text: "Hatırlat", onclick: e => opts.onNudge(kr, e.currentTarget) }) : null));
}

async function submitObjective(o, btn) {
  if (X.krOf(o.id).length < 2) { toast("Onaya göndermek için en az 2 Key Result gerekli.", "bad"); return; }
  await busy(btn, async () => {
    await updateRec("obj", o.id, { [F.obj.durum]: "Onayda" });
    await refreshLater(["obj", "kr"], "OKR onaya gönderildi. Onaylayıcıya bildirim gitti.");
  });
}

function approvalButtons(req, title, keys) {
  return [
    el("button", { class: "btn sm good", text: "Onayla", onclick: e => busy(e.currentTarget, async () => {
      await approveReq(req.requestId); await refreshLater(keys, `“${title}” onaylandı.`); }) }),
    el("button", { class: "btn sm bad", text: "Reddet", onclick: () => rejectDrawer(req, title, keys) })
  ];
}
function rejectDrawer(req, title, keys) {
  const t = textarea({ placeholder: "Neyi değiştirmeli? (zorunlu)" });
  const { form, err } = formShell(field("Red gerekçesi", t, { required: true }));
  const send = el("button", { class: "btn bad", text: "Reddet", onclick: e => {
    if (!checkRequired(form, err)) return;
    busy(e.currentTarget, async () => { await rejectReq(req.requestId, t.value.trim()); drawer.close(); await refreshLater(keys, "Reddedildi, gerekçe iletildi."); }, err);
  } });
  drawer.open("Reddet: " + title, form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }), send]);
}

// ─── Ortak: check-in paneli (bugün beklenen + sapma) ───────────────────────
function checkinDrawer(kr, o, onDone) {
  const exp = krExpectedValue(kr, o);
  const last = lastCheckin(kr);
  const milestone = kr.type === "Kilometre Taşı";
  const val = input({ type: "number", step: "any", inputmode: "decimal", value: kr.current ?? "" });
  const done = el("div", { class: "seg", role: "group", "aria-label": "Durum" });
  if (milestone) {
    for (const [v, t] of [[0, "Tamamlanmadı"], [1, "Tamamlandı"]]) {
      done.append(el("button", { type: "button", "aria-pressed": (kr.current || 0) === v ? "true" : "false", text: t,
        onclick: e => { done.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", "false")); e.currentTarget.setAttribute("aria-pressed", "true"); val.value = v; } }));
    }
  }
  const conf = input({ type: "range", min: 1, max: 10, step: 1, value: last?.conf ?? kr.conf ?? 7 });
  const out = el("output", { text: conf.value });
  conf.addEventListener("input", () => { out.textContent = conf.value; out.style.color = conf.value >= 7 ? "var(--good)" : conf.value >= 5 ? "var(--warn)" : "var(--bad)"; });
  const doneTxt = textarea({ placeholder: "Bu hafta ne yaptın, neler ilerledi?" });
  const block = textarea({ placeholder: "Bir engel ya da ihtiyacın varsa yaz (KR sahibine bildirim gider)" });
  const dev = el("span", { class: "deviation" });
  const updDev = () => {
    const v = num(val.value);
    if (exp == null || v == null || milestone) { dev.textContent = ""; dev.className = "deviation"; return; }
    const span = (kr.target - kr.start) || 1;
    const d = (v - exp) / Math.abs(span);
    const up = (kr.target >= kr.start ? d : -d) >= 0;
    dev.textContent = (up ? "+" : "−") + Math.abs(Math.round(d * 100)) + " puan " + (up ? "planın önünde" : "planın gerisinde");
    dev.className = "deviation " + (up ? "up" : "down");
  };
  val.addEventListener("input", updDev); updDev();

  const ctx = el("div", { class: "card", style: { marginBottom: "16px", background: "var(--bg)", boxShadow: "none" } },
    el("div", { class: "nm", style: { fontWeight: 700 }, text: kr.name }),
    el("div", { class: "sub", text: o.name }),
    el("dl", { class: "kv", style: { marginTop: "10px" } },
      el("dt", { text: "Başlangıç → Hedef" }), el("dd", { text: `${fmt(kr.start, 2)} → ${fmt(kr.target, 2)} ${kr.unit || ""}` }),
      el("dt", { text: "Şu an" }), el("dd", { text: fmt(kr.current, 2) }),
      el("dt", { text: "Bugün beklenen" }), el("dd", { text: exp == null || milestone ? "–" : fmt(exp, 2) })),
    X.ciOf(kr.id).slice(-3).reverse().map(c => el("div", { class: "sub", style: { marginTop: "6px" } },
      `${fdate(c.date)} · ${fmt(c.value, 2)} · güven ${c.conf ?? "–"}`, c.done ? ` · ${c.done}` : "")));

  const { form, err } = formShell(
    ctx,
    milestone ? field("Durum", done) : field("Yeni değer", val, { required: true, help: kr.unit ? "Birim: " + kr.unit : null }),
    milestone ? null : el("div", { style: { marginTop: "-6px", marginBottom: "12px" } }, dev),
    field("Güven (1–10)", el("div", { class: "range" }, conf, out), { help: "Çeyrek sonunda hedefe ulaşma ihtimalin. 4 ve altı risk bildirimi üretir." }),
    field("Bu hafta yapılan", doneTxt),
    field("Engel / ihtiyaç", block));
  if (milestone) { val.value = kr.current || 0; }
  const save = el("button", { class: "btn primary", text: "Check-in kaydet", onclick: e => {
    if (!milestone && !checkRequired(form, err)) return;
    busy(e.currentTarget, async () => {
      await createRec("ci", {
        [F.ci.ad]: `${kr.name.slice(0, 40)} – ${todayISO()}`, [F.ci.tarih]: todayISO(), [F.ci.deger]: num(val.value) ?? 0,
        [F.ci.guven]: Number(conf.value), [F.ci.yapilan]: doneTxt.value.trim(), [F.ci.engel]: block.value.trim(), [F.ci.kr]: [kr.id]
      });
      if (onDone) { await onDone(); return; }
      drawer.close();
      await refreshLater(["ci", "kr", "obj"], "Check-in kaydedildi.");
    }, err);
  } });
  drawer.open("Check-in", form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }), save]);
}

// Haftalık güncelleme: KR'ları sırayla, atla seçeneğiyle
function weeklyUpdate(krs) {
  let i = 0;
  const step = () => {
    if (i >= krs.length) { drawer.close(); refreshLater(["ci", "kr", "obj"], "Haftalık güncelleme tamamlandı."); return; }
    const kr = krs[i], o = X.obj.get(kr.objId);
    checkinDrawer(kr, o, async () => { i++; step(); });
    document.getElementById("drawer-title").textContent = `Haftalık güncelleme · ${i + 1} / ${krs.length}`;
    document.getElementById("drawer-foot").prepend(el("button", { class: "btn", text: "Atla", onclick: () => { i++; step(); } }));
  };
  step();
}

// ─── Ortak: OKR oluşturma (Objective + 2–5 KR) ─────────────────────────────
function newObjectiveDrawer({ level, ownerId, deptId, title }) {
  const name = input({ placeholder: "Ör. Müşteriye ilk temasta çözüm sunmak" });
  const desc = textarea({ placeholder: "Neden önemli?" });
  const type = select(["Zorunlu (Committed)", "İddialı (Aspirational)"], { value: "İddialı (Aspirational)" }, null);
  const parents = level === "Şirket" ? [] : [...(level === "Kişi" && deptId ? deptObjectives(deptId) : []), ...companyObjectives()];
  const parent = select(parents.map(o => [o.id, `${o.level === "Şirket" ? "Şirket" : "Departman"} · ${o.name}`]), {}, "— Bağlama —");
  const krBox = el("div", {});
  const addKr = () => {
    const n = krBox.children.length + 1;
    const row = el("div", { class: "card", style: { boxShadow: "none", marginBottom: "10px", padding: "12px" } },
      field(`Key Result ${n}`, input({ class: "kr-name", placeholder: "Ölçülebilir sonuç" }), { required: n <= 2 }),
      el("div", { class: "two" },
        field("Tip", select(["Metrik", "Kilometre Taşı"], { class: "kr-type", value: "Metrik" }, null)),
        field("Birim", select(BIRIMLER, { class: "kr-unit" }, "—"))),
      el("div", { class: "two" },
        field("Başlangıç", input({ class: "kr-start", type: "number", step: "any", value: "0" })),
        field("Hedef", input({ class: "kr-target", type: "number", step: "any" }))));
    krBox.append(row);
  };
  addKr(); addKr();
  const { form, err } = formShell(
    field("Objective", name, { required: true, help: "Niteliksel, ilham veren bir cümle; sayı içermez." }),
    field("Açıklama / neden", desc),
    el("div", { class: "two" }, field("OKR türü", type), field("Dönem", input({ value: X.quarter?.name || "", disabled: true }))),
    level !== "Şirket" ? field("Üst Objective (hizalama)", parent) : null,
    el("h3", { text: "Key Result'lar", style: { margin: "6px 0 10px" } }), krBox,
    el("button", { type: "button", class: "btn sm", text: "+ Key Result ekle", onclick: () => { if (krBox.children.length < 5) addKr(); else toast("En fazla 5 KR.", "bad"); } }));

  const create = async (submit, btn) => {
    if (!checkRequired(form, err)) return;
    const rows = [...krBox.children].map(r => ({ name: r.querySelector(".kr-name").value.trim(), type: r.querySelector(".kr-type").value,
      unit: r.querySelector(".kr-unit").value, start: num(r.querySelector(".kr-start").value), target: num(r.querySelector(".kr-target").value) }))
      .filter(r => r.name);
    const bad = rows.find(r => r.type === "Metrik" && r.target == null);
    if (bad) { err.textContent = `“${bad.name}” için hedef değer gir.`; err.classList.add("show"); return; }
    await busy(btn, async () => {
      const oid = await createRec("obj", {
        [F.obj.ad]: name.value.trim(), [F.obj.aciklama]: desc.value.trim(), [F.obj.seviye]: level, [F.obj.tur]: type.value,
        [F.obj.donem]: X.quarter ? [X.quarter.id] : [], [F.obj.dept]: deptId ? [deptId] : [], [F.obj.sahipCalisan]: ownerId ? [ownerId] : [],
        [F.obj.ust]: parent.value ? [parent.value] : [], [F.obj.sahip]: ME_EMAIL
      });
      for (const r of rows) {
        await createRec("kr", { [F.kr.ad]: r.name, [F.kr.obj]: [oid], [F.kr.tip]: r.type, [F.kr.birim]: r.unit,
          [F.kr.bas]: r.type === "Metrik" ? (r.start ?? 0) : null, [F.kr.hedef]: r.type === "Metrik" ? r.target : null,
          [F.kr.guncel]: r.type === "Metrik" ? (r.start ?? 0) : null, [F.kr.sahip]: ME_EMAIL });
      }
      if (submit && rows.length >= 2) { await wait(1500); await updateRec("obj", oid, { [F.obj.durum]: "Onayda" }); }
      drawer.close();
      await refreshLater(["obj", "kr"], submit ? "OKR oluşturuldu ve onaya gönderildi." : "OKR taslak olarak kaydedildi.");
    }, err);
  };
  drawer.open(title || "Yeni OKR", form, [
    el("button", { class: "btn", text: "Taslak kaydet", onclick: e => create(false, e.currentTarget) }),
    el("button", { class: "btn primary", text: "Oluştur ve onaya gönder", onclick: e => create(true, e.currentTarget) })]);
}

// ─── Ortak: geri bildirim ──────────────────────────────────────────────────
const GB_CLASS = { "Takdir": "praise", "Gelişim Önerisi": "grow", "Geri Bildirim Talebi": "ask" };
function canSee(f, viewerId) {
  if (f.vis !== "Özel") return true;
  if ([f.from, f.to].includes(viewerId)) return true;
  return managerOf(f.to)?.id === viewerId;
}
function feedbackPost(f, viewerId) {
  const from = X.people.get(f.from), to = X.people.get(f.to);
  const isAsk = f.type === "Geri Bildirim Talebi";
  const post = el("article", { class: "post " + (GB_CLASS[f.type] || "") },
    el("div", { class: "who" }, avatar(from?.name || "?", true), el("b", { text: from?.name || "—" }),
      el("span", { class: "muted", text: isAsk ? "geri bildirim istedi:" : "→" }), el("b", { text: to?.name || "—" }),
      el("span", { class: "spacer" }), chip(f.type, f.type === "Takdir" ? "good" : isAsk ? "warn" : "brand", true),
      f.yet ? chip("🏅 " + f.yet, "brand", true) : null),
    el("div", { class: "msg", text: f.msg || "" }),
    f.reply ? el("div", { class: "reply" }, el("div", { class: "sub", text: `${to?.name || ""} yanıtladı` }), el("div", { text: f.reply })) : null,
    el("div", { class: "foot" }, el("span", { text: fdate(f.date) }), f.vis === "Özel" ? el("span", { text: "🔒 Özel" }) : el("span", { text: "🌐 Herkese açık" }),
      f.objId ? el("span", { text: "OKR: " + (X.obj.get(f.objId)?.name || "") }) : null));
  if (isAsk && !f.reply && f.to === viewerId)
    post.append(el("div", { style: { marginTop: "10px" } }, el("button", { class: "btn sm primary", text: "Yanıtla", onclick: () => replyDrawer(f) })));
  return post;
}
function replyDrawer(f) {
  const t = textarea({ placeholder: "Somut, davranışa dayalı bir yanıt yaz." });
  const { form, err } = formShell(
    el("div", { class: "callout", style: { marginBottom: "14px" } }, el("div", {}, el("b", { text: personName(f.from) + " soruyor: " }), f.msg || "")),
    field("Yanıtın", t, { required: true }));
  drawer.open("Geri bildirim talebini yanıtla", form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }),
    el("button", { class: "btn primary", text: "Gönder", onclick: e => {
      if (!checkRequired(form, err)) return;
      busy(e.currentTarget, async () => { await updateRec("gb", f.id, { [F.gb.yanit]: t.value.trim() }); drawer.close(); await refreshLater(["gb"], "Yanıt gönderildi."); }, err);
    } })]);
}
function feedbackDrawer(fromId, { mode = "give", toId = null, type = "Takdir", objId = null } = {}) {
  const ask = mode === "ask";
  const people = X.peopleList.filter(p => p.id !== fromId);
  const to = select(people.map(p => [p.id, `${p.name} · ${p.unit}`]), { value: toId || "" });
  let kind = type;
  const seg = el("div", { class: "seg", role: "group", "aria-label": "Tür" });
  const yet = select(X.yet.filter(y => y.active).map(y => [y.id, y.name]), {}, "— Yetkinlik rozeti (isteğe bağlı) —");
  const vis = select(["Herkese Açık", "Özel"], { value: type === "Takdir" ? "Herkese Açık" : "Özel" }, null);
  if (!ask) for (const t of ["Takdir", "Gelişim Önerisi"]) seg.append(el("button", { type: "button", "aria-pressed": t === kind ? "true" : "false", text: t,
    onclick: e => { kind = t; seg.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", "false")); e.currentTarget.setAttribute("aria-pressed", "true");
      vis.value = t === "Takdir" ? "Herkese Açık" : "Özel"; } }));
  const fromP = X.people.get(fromId);
  const okrs = [...X.obj.values()].filter(o => o.period === X.quarter?.name && o.status === "Aktif");
  const obj = select(okrs.map(o => [o.id, o.name]), { value: objId || "" }, "— İlgili OKR (isteğe bağlı) —");
  const msg = textarea({ placeholder: ask ? "Ne hakkında geri bildirim istiyorsun? (sunum, proje, davranış…)" : "Ne gördün, etkisi ne oldu? Somut ol." });
  const { form, err } = formShell(
    field(ask ? "Kimden istiyorsun" : "Kime", to, { required: true }),
    ask ? null : field("Tür", seg),
    field(ask ? "Sorun" : "Mesaj", msg, { required: true }),
    ask ? null : el("div", { class: "two" }, field("Yetkinlik", yet), field("Görünürlük", vis)),
    field("İlgili OKR", obj));
  drawer.open(ask ? "Geri bildirim iste" : "Geri bildirim ver", form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }),
    el("button", { class: "btn primary", text: ask ? "Talep gönder" : "Gönder", onclick: e => {
      if (!checkRequired(form, err)) return;
      const t = ask ? "Geri Bildirim Talebi" : kind;
      const short = { "Takdir": "Takdir", "Gelişim Önerisi": "Gelişim", "Geri Bildirim Talebi": "Talep" }[t];
      busy(e.currentTarget, async () => {
        await createRec("gb", { [F.gb.ad]: `${short} · ${fromP?.name} → ${personName(to.value)}`, [F.gb.tur]: t, [F.gb.mesaj]: msg.value.trim(),
          [F.gb.gorunurluk]: ask ? "Özel" : vis.value, [F.gb.tarih]: todayISO(), [F.gb.kimden]: [fromId], [F.gb.kime]: [to.value],
          [F.gb.yet]: !ask && yet.value ? [yet.value] : [], [F.gb.obj]: obj.value ? [obj.value] : [] });
        drawer.close();
        await refreshLater(["gb"], ask ? "Talep gönderildi." : "Geri bildirim gönderildi.");
      }, err);
    } })]);
}

// ─── Ortak: karne (KPI) görünümü ───────────────────────────────────────────
function weightMeters(k, kpis) {
  const box = el("div", { class: "weights" });
  for (const [label, key] of [["Operasyonel", "Operasyonel Hedef"], ["Proje", "Proje Hedefi"], ["Kurumsal", "Kurumsal Hedef"]]) {
    const sum = kpis.filter(x => x.type === key).reduce((s, x) => s + (x.weight || 0), 0);
    const tone = sum === 100 ? "good" : sum > 100 ? "bad" : "warn";
    box.append(el("div", { class: "w" }, el("div", { class: "row" }, el("span", { text: label }), el("b", { text: `%${fmt(sum, 0)} / 100`, style: { color: `var(--${tone})` } })),
      bar(Math.min(1, sum / 100), tone)));
  }
  return box;
}
function karneStepper(status) {
  const i = KARNE_DURUM.indexOf(status);
  return el("div", { class: "stepper", "aria-label": "Karne aşaması" },
    KARNE_DURUM.map((s, j) => el("span", { class: j < i ? "past" : j === i ? "on" : "", text: s })));
}
function kpiTable(k, { editActual, editPlan } = {}) {
  const kpis = X.kpiOf(k.id);
  const rows = [];
  for (const type of ["Operasyonel Hedef", "Proje Hedefi", "Kurumsal Hedef"]) {
    const list = kpis.filter(x => x.type === type);
    if (!list.length) continue;
    rows.push(el("tr", {}, el("td", { colspan: 8, style: { background: "#fbfaff", fontWeight: 700, color: "var(--navy)" }, text: type })));
    for (const h of list) {
      const act = editActual
        ? input({ class: "inline", type: "number", step: "any", value: h.actual ?? "", "aria-label": "Gerçekleşen: " + h.name,
          onchange: e => busy(e.target, async () => {
            await updateRec("kpi", h.id, { [F.kpi.gerceklesen]: num(e.target.value) });
            await refreshLater(["kpi", "karne", "kr", "obj"], "Gerçekleşen kaydedildi, puan yeniden hesaplanıyor.");
          }) })
        : fmt(h.actual, 2);
      const sc = h.score;
      const tone = sc == null ? "none" : sc >= 100 ? "good" : sc >= 60 ? "warn" : "bad";
      rows.push(el("tr", {},
        el("td", {}, el("div", { style: { fontWeight: 600 }, text: h.name }), h.locked ? el("span", { class: "sub", text: "🔒 kilitli" }) : null),
        el("td", {}, chip(h.dir || "–", h.dir === "Azalan" ? "brand" : "", true)),
        el("td", { class: "num", text: "%" + fmt(h.weight, 0) }),
        el("td", { class: "num", text: `${fmt(h.target, 2)} ${h.unit || ""}` }),
        el("td", { class: "num" }, act),
        el("td", { class: "num", text: h.real == null ? "–" : "%" + fmt(h.real, 1) }),
        el("td", { style: { minWidth: "120px" } }, el("div", { class: "row" }, el("b", { text: fmt(sc, 1) }), el("div", { style: { flex: 1 } }, bar((sc || 0) / 120, tone)))),
        el("td", {}, editPlan && !h.locked ? el("button", { class: "icon-btn", title: "Düzenle", text: "✎", onclick: () => kpiDrawer(k, h) }) : null)));
    }
  }
  if (!rows.length) return empty("Bu karnede henüz hedef yok.", "🎯");
  return el("div", { class: "tbl-wrap" }, el("table", {}, el("thead", {}, el("tr", {},
    ["Hedef", "Yönelim", "Ağırlık", "Hedeflenen", "Gerçekleşen", "Gerçekleşme", "Hedef puanı (0–120)", ""].map((t, i) => el("th", { class: i >= 2 && i <= 5 ? "num" : "", text: t })))),
  el("tbody", {}, rows)));
}
function kpiDrawer(k, h = null) {
  const types = [...X.htur.values()].sort((a, b) => a.code - b.code);
  const name = input({ value: h?.name || "" });
  const type = select(types.map(t => [t.id, t.name]), { value: h?.typeId || "" });
  const dir = select(["Artan", "Azalan"], { value: h?.dir || "Artan" }, null);
  const unit = select(BIRIMLER, { value: h?.unit || "" }, "—");
  const w = input({ type: "number", min: 0, max: 100, value: h?.weight ?? "" });
  const t = input({ type: "number", step: "any", value: h?.target ?? "" });
  const desc = textarea({ value: h?.desc || "" });
  const { form, err } = formShell(field("Hedef", name, { required: true }), el("div", { class: "two" }, field("Hedef türü", type, { required: true }), field("Yönelim", dir)),
    el("div", { class: "two" }, field("Ağırlık (%)", w, { required: true, help: "Aynı türdeki hedeflerin toplamı 100 olmalı." }), field("Birim", unit)),
    field("Hedeflenen", t, { required: true }), field("Açıklama / ölçüm yöntemi", desc));
  drawer.open(h ? "Hedefi düzenle" : "Hedef ekle · " + k.name, form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }),
    el("button", { class: "btn primary", text: "Kaydet", onclick: e => {
      if (!checkRequired(form, err)) return;
      const p = { [F.kpi.ad]: name.value.trim(), [F.kpi.tur]: [type.value], [F.kpi.yon]: dir.value, [F.kpi.birim]: unit.value || null,
        [F.kpi.agirlik]: num(w.value), [F.kpi.hedeflenen]: num(t.value), [F.kpi.aciklama]: desc.value.trim() || null };
      busy(e.currentTarget, async () => {
        if (h) await updateRec("kpi", h.id, p); else await createRec("kpi", { ...p, [F.kpi.karne]: [k.id] });
        drawer.close(); await refreshLater(["kpi", "karne"], "Hedef kaydedildi.");
      }, err);
    } })]);
}

// ─── Çalışan ekranları ─────────────────────────────────────────────────────
function employeeKarne(me) {
  const years = X.periods.filter(p => p.type === "Yıl").map(p => p.name).filter(y => X.karneOf(me.id, y));
  const year = state.ctx.karneYear && years.includes(state.ctx.karneYear) ? state.ctx.karneYear : (years.includes(X.year?.name) ? X.year.name : years.at(-1));
  const k = year ? X.karneOf(me.id, year) : null;
  const ysel = select(years, { value: year }, null);
  ysel.addEventListener("change", () => { state.ctx.karneYear = ysel.value; render(); });
  if (!k) return el("div", {}, head("Performans Formu"), empty("Henüz karnen yok. İK dönemi açtığında karnen otomatik oluşur."));
  const kpis = X.kpiOf(k.id);
  const done = k.status === "Tamamlandı";
  const canPlan = k.status === "Hedef Belirleme";
  const errors = ["Operasyonel Hedef", "Proje Hedefi", "Kurumsal Hedef"].filter(t => kpis.some(x => x.type === t) && kpis.filter(x => x.type === t).reduce((s, x) => s + (x.weight || 0), 0) !== 100);
  const actions = [ysel];
  if (canPlan) actions.push(el("button", { class: "btn", text: "+ Hedef ekle", onclick: () => kpiDrawer(k) }),
    el("button", { class: "btn primary", text: "Onaya gönder", onclick: e => {
      if (!kpis.length || errors.length) { toast(errors.length ? `Ağırlık toplamı %100 değil: ${errors.join(", ")}` : "Önce hedef ekle.", "bad"); return; }
      busy(e.currentTarget, async () => { await updateRec("karne", k.id, { [F.karne.durum]: "Yönetici Onayında" }); await refreshLater(["karne"], "Karne yöneticine gönderildi."); });
    } }));
  const yds = X.yd.filter(y => y.karneId === k.id);
  return el("div", {},
    head(`Performans Formu · ${k.period}`, `${k.form || ""} · Operasyonel %${fmt(k.rates.op, 0)} · Proje %${fmt(k.rates.pr, 0)} · Kurumsal %${fmt(k.rates.ku, 0)} · Yetkinlik %${fmt(k.rates.ye, 0)}`, ...actions),
    karneStepper(k.status),
    k.status === "Yönetici Onayında" ? el("div", { class: "callout warn section" }, "⏳ Karnen yöneticinin onayında. Onaylanınca hedeflerin kilitlenir.") : null,
    canPlan ? el("div", { class: "callout section" }, "Her hedef türünde ağırlık toplamı %100 olmalı. Tamamlayınca onaya gönder.") : null,
    el("div", { class: "grid g4 section" },
      stat("KPI skoru", fmt(k.kpiScore, 2), done ? "Kesin" : "Anlık, gerçekleşenlerle değişir", true),
      stat("Operasyonel", fmt(k.op, 1), `× %${fmt(k.rates.op, 0)}`), stat("Proje", fmt(k.pr, 1), `× %${fmt(k.rates.pr, 0)}`), stat("Kurumsal", fmt(k.ku, 1), `× %${fmt(k.rates.ku, 0)}`)),
    done ? el("div", { class: "grid g3 section" }, stat("Yetkinlik skoru", fmt(k.yetScore, 1), `× %${fmt(k.rates.ye, 0)}`), stat("Toplam puan", fmt(k.total, 2), "", true),
      el("div", { class: "card stat" }, el("div", { class: "label", text: "Final performans grubu" }), el("div", { style: { marginTop: "10px" } }, chip(k.final || k.group || "–", groupTone(k.final || k.group))))) : null,
    el("div", { class: "section" }, el("div", { class: "row", style: { marginBottom: "10px" } }, el("h2", { text: "Hedefler" }), el("span", { class: "spacer" }), weightMeters(k, kpis)),
      kpiTable(k, { editActual: ["Aktif", "Değerlendirme"].includes(k.status), editPlan: canPlan })),
    done && yds.length ? el("div", { class: "section" }, el("h2", { text: "Yetkinlik değerlendirmesi" }),
      el("div", { class: "grid g3" }, yds.map(y => el("div", { class: "card" }, el("b", { text: y.yet }), el("div", { class: "row", style: { marginTop: "8px" } },
        el("span", { style: { fontSize: "20px", fontWeight: 700, color: "var(--navy)" }, text: `${y.score ?? "–"} / 5` }), el("div", { style: { flex: 1 } }, bar((y.score || 0) / 5, "brand"))),
        y.note ? el("div", { class: "sub", style: { marginTop: "6px" }, text: y.note }) : null)))) : null,
    k.okrCount ? el("div", { class: "callout section" }, `Bu yıl ${k.okrCount} kişisel OKR · ortalama kapanış puanı ${fmt(k.okrAvg, 2)}. OKR sonuçları puana girmez, bilgi amaçlıdır.`) : null);
}

function employeeOkr(me) {
  const quarters = X.periods.filter(p => p.type === "Çeyrek" && [...X.obj.values()].some(o => o.period === p.name)).map(p => p.name);
  const q = state.ctx.okrQ && quarters.includes(state.ctx.okrQ) ? state.ctx.okrQ : X.quarter?.name;
  const qsel = select(quarters, { value: q }, null);
  qsel.addEventListener("change", () => { state.ctx.okrQ = qsel.value; render(); });
  const mine = myObjectives(me.id, q);
  const deptId = deptUnitOf(me.id);
  const dept = deptObjectives(deptId, q);
  const krs = mine.flatMap(o => X.krOf(o.id)).filter(kr => X.obj.get(kr.objId)?.status === "Aktif");
  return el("div", {},
    head("Hedef Planı · " + (q || ""), "Şirket → departman → kişi hizalaması. Renk, ilerlemenin bugün beklenen seviyeye göre durumudur.", qsel,
      krs.length ? el("button", { class: "btn", text: "Haftalık güncelleme", onclick: () => weeklyUpdate(krs) }) : null,
      q === X.quarter?.name ? el("button", { class: "btn primary", text: "+ Yeni OKR", onclick: () => newObjectiveDrawer({ level: "Kişi", ownerId: me.id, deptId }) }) : null),
    mine.length ? mine.map(o => okrCard(o, { canCheckin: true, canSubmit: true })) : empty("Bu çeyrek kişisel OKR'ın yok."),
    dept.length ? el("div", { class: "section" }, el("h2", { text: "Departmanımın OKR'ları" }), dept.map(o => okrCard(o, { ghost: true, collapsed: false }))) : null);
}

function employeeFeedback(me) {
  const f = state.ctx.gbTab || "received";
  const seg = el("div", { class: "seg" }, [["received", "Aldıklarım"], ["given", "Verdiklerim"], ["asks", "Talepler"], ["wall", "Takdir duvarı"]]
    .map(([k, t]) => el("button", { "aria-pressed": k === f ? "true" : "false", text: t, onclick: () => { state.ctx.gbTab = k; render(); } })));
  let list;
  if (f === "received") list = X.gb.filter(x => x.to === me.id && x.type !== "Geri Bildirim Talebi");
  else if (f === "given") list = X.gb.filter(x => x.from === me.id && x.type !== "Geri Bildirim Talebi");
  else if (f === "asks") list = X.gb.filter(x => x.type === "Geri Bildirim Talebi" && (x.from === me.id || x.to === me.id));
  else list = X.gb.filter(x => x.type === "Takdir" && x.vis !== "Özel");
  list = list.filter(x => canSee(x, me.id));
  const badges = {};
  for (const x of X.gb.filter(x => x.to === me.id && x.yet)) badges[x.yet] = (badges[x.yet] || 0) + 1;
  return el("div", {},
    head("Sürekli Performans", "Takdir herkese açık paylaşılabilir; gelişim önerileri ve talepler yalnızca taraflar ve yöneticiye görünür.",
      el("button", { class: "btn", text: "Geri bildirim iste", onclick: () => feedbackDrawer(me.id, { mode: "ask", toId: managerOf(me.id)?.id }) }),
      el("button", { class: "btn primary", text: "Takdir et / öneri ver", onclick: () => feedbackDrawer(me.id) })),
    Object.keys(badges).length ? el("div", { class: "row wrap", style: { marginBottom: "14px" } }, el("span", { class: "muted", text: "Rozetlerin:" }),
      Object.entries(badges).map(([k, v]) => chip(`🏅 ${k} × ${v}`, "brand", true))) : null,
    seg, el("div", { class: "feed section" }, list.length ? list.map(x => feedbackPost(x, me.id)) : empty("Burada henüz bir şey yok.", "💬")));
}

function employeeTodos(me) {
  const out = [];
  const k = X.karneOf(me.id);
  if (k?.status === "Hedef Belirleme") out.push({ icon: "target", cat: "Performans formu", title: "Hedeflerini tamamla ve onaya gönder", sub: `${k.period} karnesi · ağırlıklar %100 olmalı`, action: "Formu aç", fn: () => go("employee", "karne") });
  for (const kr of myObjectives(me.id).flatMap(o => X.krOf(o.id)).filter(needsCheckin))
    out.push({ icon: "trend", cat: "Check-in", title: kr.name, sub: lastCheckin(kr) ? `Son check-in ${daysSince(lastCheckin(kr).date)} gün önce` : "Henüz check-in yok", action: "Check-in yap", fn: () => checkinDrawer(kr, X.obj.get(kr.objId)) });
  for (const f of X.gb.filter(f => f.type === "Geri Bildirim Talebi" && f.to === me.id && !f.reply))
    out.push({ icon: "chat", cat: "Geri bildirim talebi", title: `${personName(f.from)} senden geri bildirim istiyor`, sub: f.msg ? f.msg.slice(0, 90) : null, action: "Yanıtla", fn: () => replyDrawer(f) });
  for (const o of myObjectives(me.id).filter(o => o.status === "Taslak"))
    out.push({ icon: "form", cat: "Hedef planı", title: `Taslak hedefi onaya gönder`, sub: o.name, action: "Hedeflere git", fn: () => go("employee", "okr") });
  if (k?.status === "Aktif") {
    const kpis = X.kpiOf(k.id);
    const last = kpis.map(x => x.updated).filter(Boolean).sort().at(-1);
    out.push({ icon: "form", cat: "Performans formu", title: "Gerçekleşen değerlerini güncelle", sub: `${kpis.length} hedef · son güncelleme ${last ? fdate(last) : "yok"}`, action: "Formu aç", fn: () => go("employee", "karne") });
  }
  const fresh = X.gb.find(f => f.to === me.id && f.type === "Takdir" && daysSince(f.date) <= 30);
  if (fresh) out.push({ icon: "star", cat: "Takdir", title: `${personName(fresh.from)} seni takdir etti`, sub: fresh.msg ? fresh.msg.slice(0, 90) : null, action: "Görüntüle", fn: () => go("employee", "feedback") });
  if (k?.status === "Yönetici Onayında") out.push({ icon: "clock", cat: "Bilgi", title: "Karnen yöneticinin onayında", sub: `${managerOf(me.id)?.name || "Yöneticin"} onaylayınca hedeflerin kilitlenir.`, action: "Görüntüle", fn: () => go("employee", "karne") });
  return out;
}

function employeeHomeExtra(me) {
  const k = X.karneOf(me.id);
  const objs = myObjectives(me.id);
  const fb = X.gb.filter(f => f.to === me.id && f.type !== "Geri Bildirim Talebi" && canSee(f, me.id)).slice(0, 3);
  return el("div", {},
    el("div", { class: "home-h" }, el("h2", { text: "Performansım" })),
    el("div", { class: "grid g2" },
      el("div", { class: "card" }, el("h2", { text: "Performans Formu · " + (X.year?.name || "") }),
        k ? el("div", {}, karneStepper(k.status), el("div", { style: { marginTop: "16px" } }, weightMeters(k, X.kpiOf(k.id))),
          el("div", { class: "row", style: { marginTop: "14px" } }, el("span", { class: "muted", text: "Anlık KPI skoru" }), el("b", { text: fmt(k.kpiScore, 2) }),
            el("span", { class: "spacer" }), el("button", { class: "btn sm", text: "Formu aç", onclick: () => go("employee", "karne") })))
          : empty("Bu yıl için formun henüz açılmadı.")),
      el("div", { class: "card" }, el("h2", { text: "Son geri bildirimler" }),
        fb.length ? el("div", { class: "feed" }, fb.map(f => feedbackPost(f, me.id))) : empty("Henüz geri bildirim yok.", "💬"))),
    el("div", { class: "home-h" }, el("h2", { text: "Hedeflerim · " + (X.quarter?.name || "") }),
      el("span", { class: "spacer" }), el("button", { class: "btn sm", text: "Tüm hedefler", onclick: () => go("employee", "okr") })),
    objs.length ? objs.map(o => okrCard(o, { canCheckin: true, canSubmit: true, collapsed: true }))
      : empty("Bu çeyrek kişisel hedefin yok."));
}

PV.employee = {
  heroSub: me => { const m = managerOf(me.id); return `${me.unit}${m ? " · Yöneticin: " + m.name : ""} · ${X.quarter?.name || ""}`; },
  quick: me => {
    const krs = myObjectives(me.id).flatMap(o => X.krOf(o.id)).filter(kr => X.obj.get(kr.objId)?.status === "Aktif");
    return [
      { icon: "star", label: "Takdir et", sub: "Bir çalışma arkadaşına", fn: () => feedbackDrawer(me.id) },
      { icon: "chat", label: "Geri bildirim iste", sub: "Yöneticinden veya ekipten", fn: () => feedbackDrawer(me.id, { mode: "ask", toId: managerOf(me.id)?.id }) },
      krs.length ? { icon: "trend", label: "Haftalık güncelleme", sub: `${krs.length} anahtar sonuç`, fn: () => weeklyUpdate(krs) } : null,
      { icon: "plus", label: "Hedef ekle", sub: X.quarter?.name, fn: () => newObjectiveDrawer({ level: "Kişi", ownerId: me.id, deptId: deptUnitOf(me.id) }) }];
  },
  todos: employeeTodos,
  tiles: me => {
    const k = X.karneOf(me.id);
    const objs = myObjectives(me.id);
    const act = objs.filter(o => o.status === "Aktif");
    const avg = act.length ? act.reduce((s, o) => s + (o.progress || 0), 0) / act.length : null;
    const tone = act.length ? toneOfDiff(act.reduce((s, o) => s + (o.diff ?? 0), 0) / act.length) : "";
    const late = objs.flatMap(o => X.krOf(o.id)).filter(needsCheckin).length;
    return [
      { title: "Performans Formu", sub: X.year?.name, value: k?.kpiScore != null ? fmt(k.kpiScore, 1) : "–", icon: "form", foot: k ? k.status : "Form yok", fn: () => go("employee", "karne") },
      { title: "Hedeflerim", sub: X.quarter?.name, value: pct(avg), tone, icon: "target", foot: `${objs.length} hedef · ${TONE_LABEL[tone] || "—"}`, fn: () => go("employee", "okr") },
      { title: "Check-in", sub: "7 günden eski", value: String(late), tone: late ? "warn" : "good", icon: "trend", foot: late ? "Güncelleme bekliyor" : "Güncel", fn: () => go("employee", "okr") },
      { title: "Sürekli Performans", sub: "Aldığın takdir", value: String(X.gb.filter(f => f.to === me.id && f.type === "Takdir").length), icon: "star", foot: "Geri bildirimler", fn: () => go("employee", "feedback") }];
  },
  homeExtra: employeeHomeExtra,
  tabs: [
    { id: "home", label: "Ana Sayfa", icon: "home", render: sfHome, badge: me => employeeTodos(me).length },
    { id: "karne", label: "Performans Formu", icon: "form", render: employeeKarne },
    { id: "okr", label: "Hedefler", icon: "target", render: employeeOkr },
    { id: "feedback", label: "Sürekli Performans", icon: "chat", render: employeeFeedback,
      badge: me => X.gb.filter(f => f.type === "Geri Bildirim Talebi" && f.to === me.id && !f.reply).length }
  ]
};

"use strict";
/* Yönetici personası: ekip özeti, onaylar, check-in akışı, takım OKR'ları, yetkinlik değerlendirmesi. */

function teamStats(me) {
  const team = teamOf(me.id);
  const rows = team.map(p => {
    const k = X.karneOf(p.id);
    const objs = myObjectives(p.id);
    const active = objs.filter(o => o.status === "Aktif");
    const krs = objs.flatMap(o => X.krOf(o.id));
    const lastCi = krs.flatMap(kr => X.ciOf(kr.id)).map(c => c.date).sort().at(-1) || null;
    return { p, k, objs, active, krs, lastCi,
      progress: active.length ? active.reduce((s, o) => s + (o.progress || 0), 0) / active.length : null,
      tone: active.length ? toneOfDiff(active.reduce((s, o) => s + (o.diff ?? 0), 0) / active.length) : "none",
      late: krs.some(needsCheckin),
      fb: X.gb.filter(f => f.to === p.id && f.type !== "Geri Bildirim Talebi").length };
  });
  return { team, rows };
}
function pendingApprovals(me) {
  const team = new Set(teamOf(me.id).map(p => p.id));
  const karneler = [...X.karne.values()].filter(k => team.has(k.personId) && k.status === "Yönetici Onayında");
  const unit = X.people.get(me.id)?.unitId;
  const objs = [...X.obj.values()].filter(o => o.status === "Onayda" && (team.has(o.ownerId) || (o.level === "Departman" && o.deptId === unit)));
  return { karneler, objs, count: karneler.length + objs.length };
}

function nudge(kr, btn) {
  return busy(btn, async () => {
    await addComment("kr", kr.id, "Hatırlatma: bu haftanın check-in'i bekleniyor. Değeri ve güven skorunu güncelleyebilir misin?");
    toast("Hatırlatma gönderildi (KR kaydına yorum olarak).", "good");
  });
}

function profileDrawer(p, me) {
  const k = X.karneOf(p.id);
  const objs = myObjectives(p.id);
  const fb = X.gb.filter(f => (f.to === p.id || f.from === p.id) && canSee(f, me.id)).slice(0, 4);
  const body = el("div", {},
    personTag(p),
    el("div", { class: "section" }, el("h3", { text: "Karne · " + (X.year?.name || "") }),
      k ? el("div", {}, karneStepper(k.status), el("dl", { class: "kv", style: { marginTop: "10px" } },
        el("dt", { text: "Form türü" }), el("dd", { text: k.form || "–" }),
        el("dt", { text: "KPI skoru (anlık)" }), el("dd", { text: fmt(k.kpiScore, 2) }),
        el("dt", { text: "Hedef sayısı" }), el("dd", { text: fmt(k.goals, 0) }),
        el("dt", { text: "Ağırlık hatası" }), el("dd", { text: k.wErr ? "Var" : "Yok" }))) : empty("Karne yok.")),
    el("div", { class: "section" }, el("h3", { text: "OKR'lar · " + (X.quarter?.name || "") }),
      objs.length ? objs.map(o => okrCard(o, { collapsed: true })) : el("p", { class: "muted", text: "Bu çeyrek kişisel OKR yok." })),
    el("div", { class: "section" }, el("h3", { text: "Son geri bildirimler" }),
      fb.length ? el("div", { class: "feed" }, fb.map(f => feedbackPost(f, me.id))) : el("p", { class: "muted", text: "Henüz yok." })));
  drawer.open(p.name, body, [
    el("button", { class: "btn", text: "Hedef ver (OKR)", onclick: () => newObjectiveDrawer({ level: "Kişi", ownerId: p.id, deptId: X.people.get(me.id).unitId, title: `${p.name} için OKR` }) }),
    el("button", { class: "btn primary", text: "Geri bildirim ver", onclick: () => feedbackDrawer(me.id, { toId: p.id }) })]);
}

function managerTeam(me) {
  const { team, rows } = teamStats(me);
  if (!team.length) return el("div", {}, head("Ekibim"), empty("Bu kişinin doğrudan raporu yok."));
  const withOkr = rows.filter(r => r.active.length).length;
  const tracked = rows.filter(r => r.krs.some(kr => X.obj.get(kr.objId)?.status === "Aktif")).length;
  const checked = rows.filter(r => r.krs.some(kr => X.obj.get(kr.objId)?.status === "Aktif") && !r.late).length;
  const approved = rows.filter(r => r.k && !["Hedef Belirleme", "Yönetici Onayında"].includes(r.k.status)).length;
  const ap = pendingApprovals(me);
  const table = el("div", { class: "tbl-wrap" }, el("table", {},
    el("thead", {}, el("tr", {}, ["Çalışan", "Karne", "KPI skoru", "OKR ilerlemesi", "Son check-in", "Geri bildirim", ""].map((t, i) => el("th", { class: i === 2 || i === 5 ? "num" : "", text: t })))),
    el("tbody", {}, rows.sort((a, b) => a.p.name.localeCompare(b.p.name, "tr")).map(r => el("tr", {},
      el("td", {}, el("button", { class: "icon-btn", style: { padding: 0, textAlign: "left" }, onclick: () => profileDrawer(r.p, me) }, personTag(r.p, r.p.unit + (r.p.account ? "" : " · hesabı yok")))),
      el("td", {}, r.k ? chip(r.k.status, karneTone(r.k.status)) : chip("Karne yok", "")),
      el("td", { class: "num", text: fmt(r.k?.kpiScore, 1) }),
      el("td", { style: { minWidth: "150px" } }, r.active.length ? el("div", {}, el("div", { class: "row", style: { justifyContent: "space-between", fontSize: "12px" } },
        chip(TONE_LABEL[r.tone], r.tone), el("b", { text: pct(r.progress) })), bar(r.progress, r.tone)) : el("span", { class: "muted", text: r.objs.length ? r.objs[0].status : "OKR yok" })),
      el("td", { style: { color: r.late ? "var(--bad)" : null, fontWeight: r.late ? 700 : 400 }, text: r.lastCi ? `${fdate(r.lastCi)} (${daysSince(r.lastCi)} gün)` : "–" }),
      el("td", { class: "num", text: String(r.fb) }),
      el("td", {}, el("div", { class: "row" },
        el("button", { class: "btn sm", text: "Takdir", onclick: () => feedbackDrawer(me.id, { toId: r.p.id }) }),
        r.late ? el("button", { class: "btn sm", text: "Hatırlat", onclick: e => { const kr = r.krs.find(needsCheckin); if (kr) nudge(kr, e.currentTarget); } }) : null)))))));
  return el("div", {},
    head("Ekibim", `${me.unit} · ${team.length} doğrudan rapor · ${X.quarter?.name || ""}`,
      el("button", { class: "btn", text: "Kendi hedeflerim →", onclick: () => { state.who.employee = me.id; go("employee", "home"); } }),
      ap.count ? el("button", { class: "btn primary", text: `${ap.count} onay bekliyor`, onclick: () => go("manager", "approvals") }) : null),
    el("div", { class: "grid g4" },
      stat("Aktif OKR'ı olan", `${withOkr}/${team.length}`, "Bu çeyrek kişisel OKR", true),
      stat("Check-in güncel", tracked ? `${checked}/${tracked}` : "–", "Son 7 günde check-in girenler"),
      stat("Onaylı karne", `${approved}/${team.length}`, X.year?.name + " hedefleri"),
      stat("Bekleyen onay", String(ap.count), "Karne + OKR")),
    el("div", { class: "section" }, table));
}

function managerApprovals(me) {
  const { karneler, objs } = pendingApprovals(me);
  return el("div", {},
    head("Onaylar", "Karnelerin KPI hedefleri ve ekibin OKR'ları senin onayını bekliyor. Red gerekçesi zorunludur."),
    !karneler.length && !objs.length ? empty("Bekleyen onay yok.", "✓") : null,
    karneler.length ? el("div", { class: "section" }, el("h2", { text: "Karne onayları" }),
      karneler.map(k => {
        const p = X.people.get(k.personId);
        return el("div", { class: "card", style: { marginBottom: "14px" } },
          el("div", { class: "row wrap", style: { marginBottom: "12px" } }, personTag(p, `${k.form} · ${k.period}`), el("span", { class: "spacer" }),
            k.approval ? approvalButtons(k.approval, k.name, ["karne", "kpi"]) : chip("Onay isteği oluşuyor…", "warn", true)),
          weightMeters(k, X.kpiOf(k.id)), el("div", { class: "section" }, kpiTable(k)));
      })) : null,
    objs.length ? el("div", { class: "section" }, el("h2", { text: "OKR onayları" }),
      objs.map(o => okrCard(o, { approve: true, showOwner: true }))) : null);
}

function managerFeed(me) {
  const team = new Set(teamOf(me.id).map(p => p.id));
  const unit = X.people.get(me.id)?.unitId;
  const objIds = new Set([...X.obj.values()].filter(o => o.period === X.quarter?.name && (team.has(o.ownerId) || (o.level === "Departman" && o.deptId === unit))).map(o => o.id));
  const krMap = new Map(X.kr.filter(kr => objIds.has(kr.objId)).map(kr => [kr.id, kr]));
  const cis = X.ci.filter(c => krMap.has(c.krId)).sort((a, b) => (b.date || "").localeCompare(a.date || "")).slice(0, 40);
  const onlyBlockers = !!state.ctx.onlyBlockers;
  const list = onlyBlockers ? cis.filter(c => c.blocker) : cis;
  return el("div", {},
    head("Check-in Akışı", "Ekibinin ve departmanının son check-in'leri. Engeller kırmızı işaretli.",
      el("button", { class: "btn", "aria-pressed": onlyBlockers ? "true" : "false", text: onlyBlockers ? "Tümünü göster" : "Yalnızca engeller", onclick: () => { state.ctx.onlyBlockers = !onlyBlockers; render(); } })),
    el("div", { class: "feed" }, list.length ? list.map(c => {
      const kr = krMap.get(c.krId), o = X.obj.get(kr.objId);
      const owner = o.ownerId ? X.people.get(o.ownerId) : null;
      const prev = X.ciOf(kr.id).filter(x => (x.date || "") < (c.date || "")).at(-1);
      const delta = prev && c.value != null && prev.value != null ? c.value - prev.value : null;
      return el("article", { class: "post" + (c.blocker ? " blocker" : "") },
        el("div", { class: "who" }, avatar(owner?.name || o.dept || "D", true), el("b", { text: owner?.name || ("Departman · " + (o.dept || "")) }),
          el("span", { class: "muted", text: "· " + fdate(c.date) }), el("span", { class: "spacer" }),
          chip(`Güven ${c.conf ?? "–"}`, c.conf >= 7 ? "good" : c.conf >= 5 ? "warn" : "bad")),
        el("div", { style: { marginTop: "6px", fontWeight: 600 }, text: kr.name }),
        el("div", { class: "sub" }, o.name, " · değer ", el("b", { text: fmt(c.value, 2) }),
          delta != null ? el("span", { class: "deviation " + (delta >= 0 === (kr.target >= kr.start) ? "up" : "down"), style: { marginLeft: "6px" }, text: (delta >= 0 ? "+" : "") + fmt(delta, 2) }) : null),
        c.done ? el("div", { class: "msg", text: "✔ " + c.done }) : null,
        c.blocker ? el("div", { class: "msg", style: { color: "var(--bad)", fontWeight: 600 }, text: "⚠ " + c.blocker }) : null,
        el("div", { class: "foot" },
          owner ? el("button", { class: "btn sm", text: "Takdir et", onclick: () => feedbackDrawer(me.id, { toId: owner.id, objId: o.id }) }) : null,
          el("button", { class: "btn sm", text: "Yorum yaz", onclick: () => commentDrawer(c) })));
    }) : empty("Son iki haftada check-in yok.", "📭")));
}
function commentDrawer(c) {
  const t = textarea({ placeholder: "Koçluk notu, soru ya da yardım teklifi…" });
  const { form, err } = formShell(field("Yorum", t, { required: true, help: "Check-in kaydına yorum olarak eklenir." }));
  drawer.open("Check-in'e yorum", form, [el("button", { class: "btn", text: "Vazgeç", onclick: drawer.close }),
    el("button", { class: "btn primary", text: "Gönder", onclick: e => {
      if (!checkRequired(form, err)) return;
      busy(e.currentTarget, async () => { await addComment("ci", c.id, t.value.trim()); drawer.close(); toast("Yorum eklendi.", "good"); }, err);
    } })]);
}

function managerOkr(me) {
  const unit = X.people.get(me.id)?.unitId;
  const dept = deptObjectives(unit);
  const team = teamOf(me.id);
  const teamObjs = team.flatMap(p => myObjectives(p.id));
  return el("div", {},
    head("Takım Hedefleri", `${me.unit} · ${X.quarter?.name || ""}. Departman KR'larının check-in'ini sen girersin; ekibe kişisel OKR atayabilirsin.`,
      el("button", { class: "btn", text: "+ Ekibe OKR ata", onclick: () => {
        const who = select(team.map(p => [p.id, p.name]), {}, "Kime?");
        const { form, err } = formShell(field("Çalışan", who, { required: true }));
        drawer.open("Ekibe OKR ata", form, [el("button", { class: "btn primary", text: "Devam", onclick: () => {
          if (!checkRequired(form, err)) return;
          newObjectiveDrawer({ level: "Kişi", ownerId: who.value, deptId: unit, title: `${personName(who.value)} için OKR` });
        } })]);
      } }),
      el("button", { class: "btn primary", text: "+ Departman OKR'ı", onclick: () => newObjectiveDrawer({ level: "Departman", deptId: unit, title: "Yeni departman OKR'ı" }) })),
    el("h2", { text: "Departman OKR'ları", style: { marginBottom: "10px" } }),
    dept.length ? dept.map(o => okrCard(o, { canCheckin: true, canSubmit: true, approve: false })) : empty("Bu çeyrek departman OKR'ı yok."),
    el("div", { class: "section" }, el("h2", { text: "Ekibin kişisel OKR'ları", style: { marginBottom: "10px" } }),
      teamObjs.length ? teamObjs.map(o => okrCard(o, { showOwner: true, onNudge: nudge, approve: true })) : empty("Ekipte kişisel OKR yok.")));
}

function managerReview(me) {
  const years = X.periods.filter(p => p.type === "Yıl").map(p => p.name);
  const year = state.ctx.revYear && years.includes(state.ctx.revYear) ? state.ctx.revYear : X.year?.name;
  const ysel = select(years, { value: year }, null);
  ysel.addEventListener("change", () => { state.ctx.revYear = ysel.value; render(); });
  const team = teamOf(me.id);
  const cards = team.map(p => {
    const k = X.karneOf(p.id, year);
    if (!k) return null;
    const yds = X.yd.filter(y => y.karneId === k.id);
    const editable = k.status === "Değerlendirme";
    return el("div", { class: "card", style: { marginBottom: "14px" } },
      el("div", { class: "row wrap" }, personTag(p, `${k.form} · ${k.status}`), el("span", { class: "spacer" }),
        el("div", { style: { textAlign: "right" } }, el("div", { class: "sub", text: "Yetkinlik skoru" }), el("b", { style: { fontSize: "18px" }, text: fmt(k.yetScore, 1) }))),
      yds.length ? el("div", { class: "tbl-wrap section" }, el("table", {}, el("tbody", {}, yds.map(y => {
        const seg = el("div", { class: "seg", role: "group", "aria-label": y.yet + " puanı" });
        for (let s = 1; s <= 5; s++) seg.append(el("button", { type: "button", "aria-pressed": y.score === s ? "true" : "false", disabled: !editable, text: String(s),
          onclick: e => busy(e.currentTarget, async () => { await updateRec("yd", y.id, { [F.yd.puan]: s }); await refreshLater(["yd", "karne"], `${y.yet}: ${s}/5`); }) }));
        return el("tr", {}, el("td", { style: { fontWeight: 600 }, text: y.yet }), el("td", {}, seg), el("td", { class: "sub", text: y.note || "" }));
      })))) : el("p", { class: "muted", text: editable ? "Değerlendirme formları oluşturuluyor…" : "Yetkinlik değerlendirmesi karne Değerlendirme aşamasına geçince açılır." }));
  }).filter(Boolean);
  return el("div", {}, head("Yetkinlik Değerlendirmesi", "Karne Değerlendirme aşamasındayken her yetkinliği 1–5 arası puanla. Toplam puanın %10'u.", ysel),
    cards.length ? cards : empty("Bu yıl ekibin için karne yok."));
}

function managerTodos(me) {
  const out = [];
  const { karneler, objs } = pendingApprovals(me);
  for (const k of karneler) out.push({ icon: "approve", cat: "Onay", title: `${personName(k.personId)} · performans formu hedefleri`, sub: `${k.form || ""} · ${k.period}${k.approval?.expiryDateUtc ? " · son " + fdate(k.approval.expiryDateUtc) : ""}`, action: "İncele", fn: () => go("manager", "approvals") });
  for (const o of objs) out.push({ icon: "approve", cat: "Hedef onayı", title: o.name, sub: o.ownerId ? personName(o.ownerId) : "Departman hedefi", action: "İncele", fn: () => go("manager", "approvals") });
  for (const f of X.gb.filter(f => f.type === "Geri Bildirim Talebi" && f.to === me.id && !f.reply))
    out.push({ icon: "chat", cat: "Geri bildirim talebi", title: `${personName(f.from)} geri bildirim istiyor`, sub: f.msg ? f.msg.slice(0, 90) : null, action: "Yanıtla", fn: () => replyDrawer(f) });
  const team = teamOf(me.id);
  const evals = team.map(p => X.karneOf(p.id)).filter(k => k?.status === "Değerlendirme");
  if (evals.length) out.push({ icon: "form", cat: "Değerlendirme", title: `${evals.length} çalışanın yetkinlik değerlendirmesi bekliyor`, sub: evals.slice(0, 3).map(k => personName(k.personId)).join(", "), action: "Değerlendir", fn: () => go("manager", "review") });
  const lateRows = teamStats(me).rows.filter(r => r.late);
  if (lateRows.length) out.push({ icon: "clock", cat: "Check-in", title: `${lateRows.length} ekip üyesinin check-in'i gecikti`, sub: lateRows.slice(0, 3).map(r => r.p.name).join(", "), action: "Ekibe git", fn: () => go("manager", "team") });
  return out;
}

function managerHomeExtra(me) {
  const { rows } = teamStats(me);
  if (!rows.length) return null;
  return el("div", {},
    el("div", { class: "home-h" }, el("h2", { text: "Ekibim" }), el("span", { class: "muted", text: `${rows.length} doğrudan rapor` }),
      el("span", { class: "spacer" }), el("button", { class: "btn sm", text: "Ekip görünümü", onclick: () => go("manager", "team") })),
    el("div", { class: "team-strip" }, rows.sort((a, b) => a.p.name.localeCompare(b.p.name, "tr")).map(r => el("button", { class: "tm", onclick: () => profileDrawer(r.p, me) },
      (() => { const av = avatar(r.p.name); av.classList.add("lg"); return av; })(),
      el("b", { text: r.p.name }), el("small", { text: r.p.unit }),
      r.active.length ? chip(TONE_LABEL[r.tone], r.tone) : chip(r.k?.status || "Form yok", r.k ? karneTone(r.k.status) : "")))));
}

PV.manager = {
  heroSub: me => `${me.unit} · ${teamOf(me.id).length} doğrudan rapor · ${X.quarter?.name || ""}`,
  quick: me => [
    { icon: "star", label: "Takdir et", sub: "Ekipten birine", fn: () => feedbackDrawer(me.id, { toId: teamOf(me.id)[0]?.id }) },
    { icon: "approve", label: "Onaylar", sub: `${pendingApprovals(me).count} bekliyor`, fn: () => go("manager", "approvals") },
    { icon: "trend", label: "Check-in akışı", sub: "Ekibin son güncellemeleri", fn: () => go("manager", "feed") },
    { icon: "target", label: "Kendi hedeflerim", sub: "Çalışan görünümüne geç", fn: () => { state.who.employee = me.id; go("employee", "home"); } }],
  todos: managerTodos,
  tiles: me => {
    const { team, rows } = teamStats(me);
    const tracked = rows.filter(r => r.krs.some(kr => X.obj.get(kr.objId)?.status === "Aktif"));
    const ok = tracked.filter(r => !r.late).length;
    const ap = pendingApprovals(me).count;
    const act = rows.filter(r => r.progress != null);
    const avg = act.length ? act.reduce((s, r) => s + r.progress, 0) / act.length : null;
    const evals = team.map(p => X.karneOf(p.id)).filter(k => k?.status === "Değerlendirme").length;
    return [
      { title: "Ekibim", sub: me.unit, value: String(team.length), icon: "team", foot: "doğrudan rapor", fn: () => go("manager", "team") },
      { title: "Onay Bekleyenler", sub: "Form + hedef", value: String(ap), tone: ap ? "warn" : "good", icon: "approve", foot: ap ? "İşlem bekliyor" : "Hepsi onaylı", fn: () => go("manager", "approvals") },
      { title: "Check-in Disiplini", sub: "Son 7 gün", value: tracked.length ? `${ok}/${tracked.length}` : "–", tone: tracked.length && ok < tracked.length ? "warn" : "good", icon: "trend", foot: "güncel çalışan", fn: () => go("manager", "feed") },
      { title: "Takım Hedefleri", sub: X.quarter?.name, value: pct(avg), icon: "target", foot: "ortalama ilerleme", fn: () => go("manager", "okr") },
      { title: "Yetkinlik Değerlendirmesi", sub: X.year?.name, value: String(evals), icon: "form", foot: evals ? "değerlendirme bekliyor" : "bekleyen yok", fn: () => go("manager", "review") }];
  },
  homeExtra: managerHomeExtra,
  tabs: [
    { id: "home", label: "Ana Sayfa", icon: "home", render: sfHome, badge: me => managerTodos(me).length },
    { id: "team", label: "Ekibim", icon: "team", render: managerTeam },
    { id: "approvals", label: "Onaylar", icon: "approve", render: managerApprovals, badge: me => pendingApprovals(me).count },
    { id: "feed", label: "Check-in Akışı", icon: "trend", render: managerFeed },
    { id: "okr", label: "Takım Hedefleri", icon: "target", render: managerOkr },
    { id: "review", label: "Yetkinlik Değerlendirmesi", icon: "form", render: managerReview }
  ]
};

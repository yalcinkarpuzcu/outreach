/* Görevlerim: yalnızca kendine atanan görevi güncelleme, öncül kilidi, onaya gönderme, onay kutusu */
"use strict";

let ME = null, ALL = [], BYID = new Map(), TAB = "mine", MYDEPTS = new Set();
const panel = document.getElementById("panel");
const showClosed = document.getElementById("chk-closed");

const mine = () => ALL.filter(t => t.type !== "Faz" && t.owner && String(t.owner.id) === String(ME.id));
const myApprovals = () => ALL.filter(t => {
  const ar = t.rec.approvalRequest;
  return ar && ar.status === 0 && (ar.usersIds || []).map(String).includes(String(ME.id));
});

function openPredNames(t) {
  return t.deps.map(d => BYID.get(d.id)).filter(p => p && !p.closed).map(p => p.name);
}

async function load() {
  stateLoading(panel, "Görevler yükleniyor…");
  try {
    const [recs, depts] = await Promise.all([fetchAll("G", { includeApprovalRequest: true }), fetchAll("D").catch(() => [])]);
    MYDEPTS = new Set(depts.filter(d => [v(d, "D", "Departman Yöneticisi"), ...(v(d, "D", "Ekip Üyeleri") || []), v(d, "D", "Onaylayıcı")]
      .some(u => u && String(u.id) === String(ME.id))).map(d => v(d, "D", "Departman")));
    ALL = recs.map(r => taskModel(r, "G"));
    BYID = new Map(ALL.map(t => [t.id, t]));
    const nMine = mine().filter(t => !t.closed).length, nOnay = myApprovals().length;
    const b1 = document.getElementById("c-mine"), b2 = document.getElementById("c-onay");
    b1.textContent = String(nMine); b1.hidden = !nMine;
    b2.textContent = String(nOnay); b2.hidden = !nOnay;
    render();
    const h = decodeURIComponent(location.hash.slice(1));
    if (h && BYID.has(h)) { openDetail(BYID.get(h)); history.replaceState(null, "", location.pathname); }
  } catch (e) {
    stateError(panel, e, load);
  }
}

function render() {
  if (TAB === "onay") return renderApprovals();
  if (TAB === "dept") return renderDept();
  let list = mine();
  if (!showClosed.checked) list = list.filter(t => !t.closed);
  if (!list.length) {
    stateEmpty(panel, "Size atanmış açık görev yok", showClosed.checked ? "Henüz size atanmış görev bulunmuyor." : "Tüm görevleriniz kapalı. Kapananları görmek için yukarıdaki kutuyu işaretleyin.");
    return;
  }
  const groups = new Map();
  list.sort((a, b) => (a.end ?? 0) - (b.end ?? 0));
  for (const t of list) { if (!groups.has(t.projectName)) groups.set(t.projectName, []); groups.get(t.projectName).push(t); }
  const box = el("div");
  for (const [pn, ts] of groups) {
    box.append(el("div", { class: "task-group" }, el("h3", { text: pn || "Projesiz" }), ...ts.map(card)));
  }
  clear(panel).append(box);
}

function card(t) {
  const locked = t.openPreds > 0 && ["Başlamadı", "Başlayabilir"].includes(t.status);
  const acts = el("div", { class: "acts" });
  const btn = (text, cls, fn, dis) => acts.append(el("button", { class: "btn sm " + (cls || ""), type: "button", text, disabled: dis || null, onclick: fn }));
  switch (t.status) {
    case "Başlamadı": case "Başlayabilir":
      btn("▶ Başlat", "primary", () => setStatus(t, "Devam Ediyor"), locked); break;
    case "Devam Ediyor": case "Revizyon Gerekli":
      if (t.approvalNeeded) btn("✍ Onaya gönder", "primary", () => setStatus(t, "Onay Bekliyor"));
      else btn("✓ Tamamla", "good", () => setStatus(t, "Tamamlandı"));
      break;
    case "Beklemede":
      btn("▶ Devam et", "primary", () => setStatus(t, "Devam Ediyor"), locked); break;
  }
  btn("Detay", "", () => openDetail(t));
  const c = el("article", { class: "card tcard", id: "t-" + t.id },
    el("div", null,
      el("h4", { text: t.name }),
      el("div", { class: "meta" }, chip(t.status),
        el("span", { text: fmtDay(t.start) + " → " + fmtDay(t.end) }),
        t.late ? el("span", { class: "tag late", text: "Gecikti" }) : null,
        t.approvalNeeded ? el("span", { class: "tag", text: "✍ Onay gerekli" }) : null,
        t.milestone ? el("span", { class: "tag", text: "◆ Kilometre taşı" }) : null,
        el("span", { text: "%" + Math.round(t.pct || 0) }))),
    acts);
  if (locked) c.append(el("div", { class: "lockmsg", text: "🔒 Öncüller tamamlanmadan başlatılamaz: " + openPredNames(t).join(", ") }));
  if (t.status === "Onay Bekliyor") c.append(el("div", { class: "lockmsg", style: "color:var(--violet)", text: "✍ Onay bekleniyor: " + (userName(t.approver) || "onaylayıcı") }));
  if (t.status === "Revizyon Gerekli") c.append(el("div", { class: "lockmsg", style: "color:var(--serious)", text: "↩ Onaylayıcı revizyon istedi. Gerekçe bildiriminizde ve Onay Geçmişi'nde." }));
  return c;
}

/* Durum değişikliği — kural motoru Workiom otomasyonlarında; sonucu kayıttan okunur */
async function setStatus(t, label) {
  const cardEl = document.getElementById("t-" + t.id);
  cardEl && cardEl.querySelectorAll("button").forEach(b => b.disabled = true);
  try {
    await updateRecord("G", t.id, { [fid("G", "Durum")]: label });
    toast("Güncellendi, iş akışı kuralları kontrol ediliyor…");
    await new Promise(r => setTimeout(r, 2500));
    const rec = await getRecord("G", t.id);
    const now = lbl(rec[fid("G", "Durum")]);
    if (label === "Devam Ediyor" && now === "Başlamadı") toast("⛔ Öncül görevler tamamlanmadığı için başlatılamadı.", "err", 5000);
    else if (label === "Tamamlandı" && now === "Onay Bekliyor") toast("Bu görev onay gerektiriyor — onaya gönderildi.", "", 4500);
    else if (now === "Onay Bekliyor") toast("Onay talebi " + (userName(t.approver) || "onaylayıcıya") + " gönderildi.", "ok");
    else if (now === "Tamamlandı") toast("Görev tamamlandı. Ardıl görevlerin sorumlularına bildirim gider.", "ok");
    else toast("Durum: " + now, "ok");
  } catch (e) {
    if (!(e instanceof SessionGone)) toast(e.message, "err", 5000);
  }
  load();
}

/* ── detay çekmecesi: %, notlar, dokümanlar ───────────────────────── */
let drawerEls = null;
function closeDrawer() { if (drawerEls) { drawerEls.forEach(x => x.remove()); drawerEls = null; } }

function openDetail(t) {
  closeDrawer();
  const own = t.owner && String(t.owner.id) === String(ME.id);
  const err = el("div", { class: "error-box", role: "alert" });
  const back = el("div", { class: "drawer-back", onclick: closeDrawer });
  const body = el("div", { class: "body" });
  const foot = el("footer");
  const dr = el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "d-t" },
    el("header", null, chip(t.status), el("h2", { id: "d-t", text: t.name }),
      el("div", { class: "meta", style: "font-size:12.5px;color:var(--text-secondary)", text: t.projectName + " · " + fmtDay(t.start) + " → " + fmtDay(t.end) })),
    body, foot);
  drawerEls = [back, dr];
  document.body.append(back, dr);

  const kv = el("dl", { class: "kv" });
  const row = (k, val) => kv.append(el("dt", { text: k }), el("dd", null, val));
  row("Departman", t.dept || "—");
  row("Onay", t.approvalNeeded ? "Gerekli · " + (userName(t.approver) || "—") + (t.approvalState ? " · " + t.approvalState : "") : "Gerekmiyor");
  row("Gerçekleşen", (t.actualStart != null ? fmtDay(t.actualStart) : "—") + " → " + (t.actualEnd != null ? fmtDay(t.actualEnd) : "—"));
  body.append(err, kv);
  if (t.rec[fid("G", "Açıklama")]) body.append(el("div", { class: "section-t", text: "Kabul kriteri / açıklama" }), el("p", { style: "white-space:pre-wrap;margin:0", text: t.rec[fid("G", "Açıklama")] }));

  body.append(el("div", { class: "section-t", text: "Öncüller" }));
  const pl = el("ul", { class: "pred-list" });
  if (!t.deps.length) pl.append(el("li", { text: "Öncül yok" }));
  t.deps.forEach(d => { const p = BYID.get(d.id); pl.append(el("li", null, el("span", { text: p ? p.name : d.label }), p ? chip(p.status) : "")); });
  body.append(pl);

  const editable = own && !t.closed && t.status !== "Onay Bekliyor";
  const pct = el("input", { type: "range", class: "range", id: "d-pct", min: "0", max: "100", step: "5", value: String(Math.round(t.pct || 0)), disabled: !editable || null });
  const pctOut = el("output", { for: "d-pct", text: "%" + Math.round(t.pct || 0) });
  pct.addEventListener("input", () => { pctOut.textContent = "%" + pct.value; });
  const notes = el("textarea", { class: "input", id: "d-notes", rows: "4", disabled: !editable || null });
  notes.value = t.notes || "";
  body.append(el("div", { class: "section-t", text: "İlerleme ve notlar" }),
    el("div", { class: "field" }, el("label", { for: "d-pct" }, "Tamamlanma ", pctOut), pct),
    el("div", { class: "field" }, el("label", { for: "d-notes", text: "Notlar" }), notes));

  // dokümanlar
  const files = el("div", { class: "files" });
  const paintFiles = list => {
    clear(files);
    if (!list.length) files.append(el("div", { class: "hint", style: "color:var(--text-muted);font-size:13px", text: "Doküman yok (protokol, rapor, sertifika…)" }));
    list.forEach(f => files.append(el("div", { class: "file" }, el("span", { text: "📄" }), el("span", { text: f.FileName || "dosya" }),
      el("button", { class: "btn sm", type: "button", text: "İndir", onclick: () => downloadFile(f).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); }) }))));
  };
  paintFiles(t.files);
  body.append(el("div", { class: "section-t", text: "Dokümanlar" }), files);
  if (own) {
    const inp = el("input", { type: "file", id: "d-file", class: "sr", multiple: true });
    const up = el("label", { class: "btn sm", for: "d-file", style: "margin-top:8px;cursor:pointer", text: "＋ Doküman ekle" });
    inp.addEventListener("change", async () => {
      if (!inp.files.length) return;
      up.textContent = "Yükleniyor…";
      try {
        const uid = (await currentUser()).id;
        const existing = t.files.map(f => ({ _id: f._id, AnonymousForm: false, ContentType: f.ContentType, ExpiryDate: null, FileName: f.FileName, FileToken: f.FileToken,
          FileUrl: f.FileUrl, HasThumbnail: !!f.HasThumbnail, IsPermanent: true, Size: f.Size, ThumbnailUrl: f.ThumbnailUrl, UserId: uid }));
        for (const file of inp.files) {
          const u = await uploadFile(file);
          if (u) existing.push(toFileFieldValue(u, file, uid));
        }
        await updateRecord("G", t.id, { [fid("G", "Dokümanlar")]: existing });
        const rec = await getRecord("G", t.id);
        t.files = rec[fid("G", "Dokümanlar")] || [];
        paintFiles(t.files);
        toast("Doküman eklendi", "ok");
      } catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; }
      finally { up.textContent = "＋ Doküman ekle"; inp.value = ""; }
    });
    body.append(inp, up);
  }

  if (!own) body.append(el("p", { style: "color:var(--text-muted);font-size:12.5px", text: "Bu görev size atanmadığı için yalnızca görüntüleyebilirsiniz." }));
  const histBox = el("div");
  body.append(el("div", { class: "section-t", text: "Değişiklik geçmişi" }), histBox);
  renderHistory(histBox, "G", t.id);
  const save = el("button", { class: "btn primary", type: "button", text: "Kaydet", disabled: !editable || null });
  save.addEventListener("click", async () => {
    save.disabled = true; clear(err);
    try {
      const payload = {};
      if (Number(pct.value) !== Math.round(t.pct || 0)) payload[fid("G", "% Tamamlanma")] = Number(pct.value);
      if (notes.value !== (t.notes || "")) payload[fid("G", "Notlar")] = notes.value === "" ? null : notes.value;
      if (Object.keys(payload).length) await updateRecord("G", t.id, payload);
      toast("Kaydedildi", "ok"); closeDrawer(); load();
    } catch (e) { if (!(e instanceof SessionGone)) err.textContent = e.message; save.disabled = false; }
  });
  if (editable && t.status === "Devam Ediyor")
    foot.append(el("button", { class: "btn", type: "button", text: "⏸ Beklemeye al", onclick: () => { closeDrawer(); setStatus(t, "Beklemede"); } }));
  foot.append(el("a", { class: "btn", href: "plan.html?id=" + encodeURIComponent(t.project), text: "Planda gör" }),
    el("button", { class: "btn", type: "button", text: "Kapat", onclick: closeDrawer }), save);
}

/* ── departmanım: ekibin görevleri (salt okunur) ───────────────────── */
function renderDept() {
  if (!MYDEPTS.size) { stateEmpty(panel, "Bir departmana bağlı değilsiniz", "Departman üyeliği Workiom'daki Departmanlar listesinden yönetilir."); return; }
  let list = ALL.filter(t => t.type !== "Faz" && MYDEPTS.has(t.dept));
  if (!showClosed.checked) list = list.filter(t => !t.closed);
  if (!list.length) { stateEmpty(panel, "Departmanınızda açık görev yok", [...MYDEPTS].join(", ")); return; }
  list.sort((a, b) => (a.end ?? 0) - (b.end ?? 0));
  const tbl = el("table", { class: "sum" }, el("thead", null, el("tr", null, ...["Görev", "Proje", "Sorumlu", "Bitiş", "Durum", ""].map(h => el("th", { text: h })))));
  const tb = el("tbody");
  for (const t of list) tb.append(el("tr", null,
    el("td", null, el("b", { text: t.name }), t.late ? el("span", { class: "tag late", style: "margin-inline-start:6px", text: "Gecikti" }) : null),
    el("td", { text: t.projectName }), el("td", { text: userName(t.owner) || "—" }), el("td", { text: fmtDay(t.end) }), el("td", null, chip(t.status)),
    el("td", null, el("button", { class: "btn sm", type: "button", text: "Detay", onclick: () => openDetail(t) }))));
  tbl.append(tb);
  clear(panel).append(el("p", { class: "hint-bar", text: "Departman: " + [...MYDEPTS].join(", ") + " · Yalnızca size atanan görevleri güncelleyebilirsiniz; diğerleri salt okunurdur." }),
    el("div", { class: "card tbl-wrap" }, tbl));
}

/* ── onay kutusu ──────────────────────────────────────────────────── */
function renderApprovals() {
  const list = myApprovals();
  if (!list.length) { stateEmpty(panel, "Onayınızı bekleyen görev yok", "Bir görev onaya gönderildiğinde burada ve Workiom bildirimlerinizde görünür."); return; }
  const box = el("div");
  for (const t of list) {
    const msg = el("textarea", { class: "input", rows: "2", placeholder: "Red gerekçesi (reddederken zorunlu)", "aria-label": "Red gerekçesi" });
    const errB = el("div", { class: "error-box", role: "alert" });
    const ok = el("button", { class: "btn good sm", type: "button", text: "✓ Onayla" });
    const no = el("button", { class: "btn danger sm", type: "button", text: "↩ Reddet" });
    const rid = t.rec.approvalRequest.requestId;
    ok.addEventListener("click", () => decide(rid, true, null, [ok, no], errB));
    no.addEventListener("click", () => {
      if (!msg.value.trim()) { errB.textContent = "Reddetmek için gerekçe yazın."; msg.setAttribute("aria-invalid", "true"); msg.focus(); return; }
      decide(rid, false, msg.value.trim(), [ok, no], errB);
    });
    box.append(el("article", { class: "card tcard", style: "grid-template-columns:1fr" },
      el("div", null, el("h4", { text: t.name }),
        el("div", { class: "meta" }, el("span", { text: t.projectName }), el("span", { text: "Sorumlu: " + (userName(t.owner) || "—") }),
          el("span", { text: "Plan bitiş: " + fmtDay(t.end) }), t.files.length ? el("span", { class: "tag", text: "📄 " + t.files.length + " doküman" }) : el("span", { class: "tag", text: "doküman yok" }))),
      t.notes ? el("p", { style: "margin:0;white-space:pre-wrap;font-size:13px", text: t.notes }) : null,
      t.files.length ? el("div", { class: "files" }, ...t.files.map(f => el("div", { class: "file" }, el("span", { text: "📄 " + (f.FileName || "dosya") }),
        el("button", { class: "btn sm", type: "button", text: "İndir", onclick: () => downloadFile(f).catch(e => { if (!(e instanceof SessionGone)) toast(e.message, "err"); }) })))) : null,
      errB, msg, el("div", { class: "acts", style: "justify-content:flex-start" }, ok, no)));
  }
  clear(panel).append(box);
}

async function decide(rid, approve, message, buttons, errB) {
  buttons.forEach(b => b.disabled = true);
  clear(errB);
  try {
    const q = "approvalRequestId=" + encodeURIComponent(rid) + (approve ? "" : "&message=" + encodeURIComponent(message));
    await api("POST", "/api/services/app/AutomationApprovalRequest/" + (approve ? "Approve" : "Reject") + "?" + q);
    toast(approve ? "Onaylandı — görev tamamlandı, ardıllar açılıyor." : "Reddedildi — görev revizyon için sorumluya döndü.", "ok", 4500);
    setTimeout(load, 1500);
  } catch (e) {
    if (!(e instanceof SessionGone)) { errB.textContent = e.message; buttons.forEach(b => b.disabled = false); }
  }
}

/* ── dosya yardımcıları (Workiom dosya uç noktaları: /api/services/app öneki YOK) ── */
async function uploadFile(file) {
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); return null; }
  delete headers["Content-Type"];          // let the browser set the multipart boundary
  const body = new FormData();
  body.append("files", file);
  const res = await fetch(`${await apiBase()}/File/Upload`, { method: "POST", headers, body });
  const json = await res.json().catch(() => null);
  if (res.status === 401 || json?.unAuthorizedRequest) { redirectToLogin(); return null; }
  if (!json?.success) throw new Error(json?.error?.message || "Yükleme başarısız");
  return json.result[0];
}

function toFileFieldValue(uploaded, originalFile, userId) {
  return {
    _id: uploaded.fileToken,
    AnonymousForm: false,
    ContentType: uploaded.fileType,
    ExpiryDate: null,
    FileName: uploaded.fileName,
    FileToken: uploaded.fileToken,
    FileUrl: uploaded.fileUrl,
    HasThumbnail: !!uploaded.hasThumbnail,
    IsPermanent: true,
    Size: originalFile.size,
    ThumbnailUrl: uploaded.thumbnailUrl,
    UserId: userId
  };
}

async function downloadFile(file) {
  const id = file._id || file.FileToken;
  const headers = workiomHeaders();
  if (!headers) { redirectToLogin(); return; }
  const res = await fetch(`${await apiBase()}/api/services/app/File/GeneratePublicDownloadUrl/${encodeURIComponent(id)}?forceDownload=true`, { headers });
  if (res.status === 401) { redirectToLogin(); return; }
  const data = await res.json().catch(() => null);
  if (!res.ok || data?.success === false) throw new Error(data?.error?.message || `HTTP ${res.status}`);
  const url = data?.result?.url;
  if (!url) throw new Error("Response had no result.url");
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

/* ── başlat ───────────────────────────────────────────────────────── */
function selectTab(tab) {
  TAB = tab;
  document.getElementById("tab-mine").setAttribute("aria-selected", tab === "mine" ? "true" : "false");
  document.getElementById("tab-onay").setAttribute("aria-selected", tab === "onay" ? "true" : "false");
  document.getElementById("tab-dept").setAttribute("aria-selected", tab === "dept" ? "true" : "false");
  render();
}
document.getElementById("tab-mine").addEventListener("click", () => selectTab("mine"));
document.getElementById("tab-onay").addEventListener("click", () => selectTab("onay"));
document.getElementById("tab-dept").addEventListener("click", () => selectTab("dept"));
document.getElementById("btn-refresh").addEventListener("click", load);
showClosed.addEventListener("change", render);

initShell("gorev").then(me => { ME = me; load(); }).catch(e => { if (!(e instanceof SessionGone)) stateError(panel, e, () => location.reload()); });

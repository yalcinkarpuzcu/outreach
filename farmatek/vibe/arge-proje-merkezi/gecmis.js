/* Değişiklik günlüğü: uygulama genelinde Workiom kayıt geçmişi */
"use strict";

const box = document.getElementById("log");
const more = document.getElementById("btn-more");
const fList = document.getElementById("f-list"), fQ = document.getElementById("f-q");
const fUser = document.getElementById("f-user"), fDates = document.getElementById("f-dates");
const PAGE = 100;
let ITEMS = [], skip = 0, done = false;
const KRITIK = /Başlangıç|Bitiş|Sorumlu|Durum|Onaylayıcı|Öncüller|Proje Yöneticisi/;

async function fetchPage() {
  more.disabled = true;
  try {
    const r = await api("POST", "/api/services/app/History/GetAllPaged?appId=" + encodeURIComponent(SCHEMA.APP.id) + "&commentAsPlainText=true",
      { maxResultCount: PAGE, skipCount: skip });
    const items = Array.isArray(r) ? r : (r.items || []);
    ITEMS.push(...items.filter(h => h.isVisible !== false));
    skip += PAGE;
    done = items.length < PAGE;
    render();
  } catch (e) {
    if (!ITEMS.length) stateError(box, e, reload); else if (!(e instanceof SessionGone)) toast(e.message, "err");
  } finally { more.disabled = false; }
}

function render() {
  const q = fQ.value.trim().toLocaleLowerCase("tr");
  const list = ITEMS.filter(h => (!fList.value || h.listName === fList.value)
    && (!fUser.checked || h.automationId == null)
    && (!fDates.checked || h.approvalRequestItem || Object.keys(h.record || {}).some(k => KRITIK.test(k)))
    && (!q || [h.itemName, h.username, h.listName].join(" ").toLocaleLowerCase("tr").includes(q)));
  more.hidden = done;
  if (!list.length) { stateEmpty(box, "Eşleşen kayıt yok", done ? "Filtreleri değiştirin." : "Filtreleri değiştirin veya daha eski kayıtları yükleyin."); return; }
  const groups = new Map();
  for (const h of list) {
    const day = new Date(h.date).toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    if (!groups.has(day)) groups.set(day, []);
    groups.get(day).push(h);
  }
  clear(box);
  for (const [day, hs] of groups) box.append(el("div", { class: "section-t", text: day + " · " + hs.length + " işlem" }), el("ul", { class: "hist" }, ...hs.map(h => histEntry(h, true))));
}

function reload() { ITEMS = []; skip = 0; done = false; stateLoading(box, "Günlük yükleniyor…"); fetchPage(); }

[fList, fUser, fDates].forEach(x => x.addEventListener("change", render));
fQ.addEventListener("input", render);
more.addEventListener("click", fetchPage);
document.getElementById("btn-refresh").addEventListener("click", reload);
initShell("gecmis").then(reload).catch(e => { if (!(e instanceof SessionGone)) stateError(box, e, () => location.reload()); });

"use strict";
/* Kırpart · Bildirimler
 * Workiom'da kullanıcıya gelen bildirimleri (otomasyon bildirimleri, onay talepleri, kayıt
 * güncellemeleri) üst bardaki zil ile gösterir. Oturum çerezleriyle çalışır; app.js'teki
 * api(), h() ve $ yardımcılarını kullanır. İki vibe app'te de aynı dosyadır.
 */
(() => {
  const APP_ID = "79cfb7b3-73e6-447c-9db9-0c9be5968705";   // Kırpart Tedarikçi Portalı (Workiom)
  const POLL_MS = 60000;

  const TXT = {
    tr: { title: "Bildirimler", unread: "Okunmamış", all: "Tümü", markAll: "Tümünü okundu say",
          empty: "Okunmamış bildiriminiz yok.", emptyAll: "Henüz bildirim yok.", open: "Kaydı aç", workiom: "Workiom'da aç ↗", notHere: "Bu kayıt burada görüntülenemiyor; Workiom'da açabilirsiniz.",
          approve: "Onayla / Reddet ↗", error: "Hata", approval: "Onay bekliyor", loadErr: "Bildirimler yüklenemedi",
          more: "Daha fazla yükle", fresh: n => n === 1 ? "1 yeni bildirim" : n + " yeni bildirim", now: "şimdi",
          min: n => n + " dk önce", hour: n => n + " sa önce", day: n => n + " gün önce", bell: "Bildirimler" },
    en: { title: "Notifications", unread: "Unread", all: "All", markAll: "Mark all as read",
          empty: "No unread notifications.", emptyAll: "No notifications yet.", open: "Open record", workiom: "Open in Workiom ↗", notHere: "This record can't be shown here; you can open it in Workiom.",
          approve: "Approve / Reject ↗", error: "Error", approval: "Approval pending", loadErr: "Could not load notifications",
          more: "Load more", fresh: n => n === 1 ? "1 new notification" : n + " new notifications", now: "now",
          min: n => n + " min ago", hour: n => n + " h ago", day: n => n + " d ago", bell: "Notifications" }
  };
  const lang = () => (typeof LANG !== "undefined" && LANG === "en" ? "en" : "tr");
  const tx = (k, ...a) => { const v = TXT[lang()][k]; return typeof v === "function" ? v(...a) : v; };

  const N = { open: false, mode: "unread", items: [], total: 0, unread: null, loading: false, error: null, page: 30 };
  let bell, badge, panel, list;

  function query(state, max) {
    const p = new URLSearchParams({ appId: APP_ID, isArchived: "false", maxResultCount: String(max), skipCount: "0" });
    if (state != null) p.set("state", String(state));
    return "/api/services/app/Notification/GetUserNotifications?" + p;
  }

  function setUnread(n) {
    if (N.unread != null && n > N.unread && !N.open && typeof toast === "function") toast(tx("fresh", n - N.unread));
    N.unread = n;
    badge.hidden = !n;
    badge.textContent = n > 99 ? "99+" : String(n);
    bell.setAttribute("aria-label", tx("bell") + (n ? " (" + n + ")" : ""));
  }

  async function poll() {
    if (document.hidden) return;
    try {
      const r = await api("GET", query(0, 1));
      setUnread(r?.unreadCount ?? r?.totalCount ?? 0);
    } catch (e) {
      console.warn("[Bildirimler] sayaç okunamadı:", e.message);
    }
  }

  async function load() {
    N.loading = true; N.error = null; render();
    try {
      const r = await api("GET", query(N.mode === "unread" ? 0 : null, N.page));
      N.items = r?.items || [];
      N.total = r?.totalCount ?? N.items.length;
      setUnread(r?.unreadCount ?? 0);
    } catch (e) {
      N.error = e.message;
    }
    N.loading = false; render();
  }

  function ago(iso) {
    const s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (!isFinite(s)) return "";
    if (s < 60) return tx("now");
    if (s < 3600) return tx("min", Math.floor(s / 60));
    if (s < 86400) return tx("hour", Math.floor(s / 3600));
    if (s < 7 * 86400) return tx("day", Math.floor(s / 86400));
    return new Date(iso).toLocaleDateString(lang() === "tr" ? "tr-TR" : "en-GB", { day: "numeric", month: "short", year: "numeric" });
  }

  async function markRead(un) {
    if (un.state !== 0) return;
    un.state = 1;
    setUnread(Math.max(0, (N.unread || 1) - 1));
    render();
    try { await api("POST", "/api/services/app/Notification/SetNotificationAsRead", { id: un.id }); }
    catch (e) { un.state = 0; setUnread((N.unread || 0) + 1); render(); console.warn("[Bildirimler]", e.message); }
  }

  async function markAll() {
    try {
      await api("POST", "/api/services/app/Notification/SetAllNotificationsAsRead");
      N.items.forEach(i => { i.state = 1; });
      setUnread(0);
      if (N.mode === "unread") N.items = [];
      render();
    } catch (e) {
      if (typeof toast === "function") toast(e.message, "bad");
    }
  }

  /* Kayıt bu uygulamanın listelerinden birindeyse uygulama içinde açılır (app.js: openFromNotification). */
  function canOpenHere(listId) {
    return typeof openFromNotification === "function" && typeof L === "object" && Object.values(L).includes(listId);
  }

  async function openInApp(listId, recordId) {
    toggle(false);
    if (openFromNotification(listId, recordId)) return;
    // Kayıt yeni olabilir: verileri sessizce yenileyip bir kez daha dene.
    if (typeof loadAll === "function") { try { await loadAll({ quiet: true }); } catch (_) { /* yükleme hatasını app.js gösterir */ } }
    if (!openFromNotification(listId, recordId) && typeof toast === "function") toast(tx("notHere"));
  }

  function item(un) {
    const n = un.notification || {};
    const p = n.data?.properties || {};
    const msg = p.notificationMessage || n.data?.message || p.Message || "";
    const kind = n.notificationName || "";
    const isFail = kind === "App.AutomationFailNotification" || n.severity >= 3;
    const isApproval = kind === "App.AutomationApprovalRequest";
    const head = p.title || p.listName || p.automationName || p.appName || "Workiom";
    const url = p.recordUrl || null;
    const listId = n.listId || p.listId;
    const inApp = !isApproval && n.recordId && canOpenHere(listId);

    const row = h("li", { class: "nt-item" + (un.state === 0 ? " is-unread" : "") + (isFail ? " is-fail" : "") },
      h("div", { class: "nt-top" },
        h("span", { class: "nt-head", text: head }),
        isFail ? h("span", { class: "nt-tag nt-tag-fail", text: tx("error") }) : null,
        isApproval ? h("span", { class: "nt-tag", text: tx("approval") }) : null,
        h("span", { class: "nt-time", text: ago(n.creationTime), title: new Date(n.creationTime).toLocaleString() })
      ),
      p.recordTitle && p.recordTitle !== head ? h("div", { class: "nt-rec", text: p.recordTitle }) : null,
      h("div", { class: "nt-msg", text: msg }),
      inApp || url ? h("div", { class: "nt-actions" },
        inApp ? h("button", { class: "nt-open", type: "button", text: tx("open"),
                              onclick: e => { e.stopPropagation(); markRead(un); openInApp(listId, n.recordId); } }) : null,
        url ? h("a", { class: "nt-link", href: url, target: "_blank", rel: "noopener", text: isApproval ? tx("approve") : tx("workiom"),
                       onclick: e => { e.stopPropagation(); markRead(un); } }) : null) : null
    );
    row.addEventListener("click", () => markRead(un));
    return row;
  }

  function render() {
    if (!panel) return;
    panel.querySelector(".nt-title").textContent = tx("title");
    const [bU, bA] = panel.querySelectorAll(".nt-seg button");
    bU.textContent = tx("unread"); bA.textContent = tx("all");
    bU.classList.toggle("is-active", N.mode === "unread");
    bA.classList.toggle("is-active", N.mode === "all");
    const mk = panel.querySelector(".nt-markall");
    mk.textContent = tx("markAll");
    mk.disabled = !N.unread;

    if (N.loading && !N.items.length) { list.replaceChildren(h("li", { class: "nt-state" }, h("span", { class: "spinner" }))); return; }
    if (N.error) { list.replaceChildren(h("li", { class: "nt-state nt-err", text: tx("loadErr") + ": " + N.error })); return; }
    if (!N.items.length) { list.replaceChildren(h("li", { class: "nt-state", text: N.mode === "unread" ? tx("empty") : tx("emptyAll") })); return; }
    const rows = N.items.map(item);
    if (N.total > N.items.length) rows.push(h("li", { class: "nt-state" },
      h("button", { class: "btn btn-outline btn-sm", type: "button", text: tx("more"), onclick: e => { e.stopPropagation(); N.page += 30; load(); } })));
    list.replaceChildren(...rows);
  }

  function toggle(force) {
    N.open = force ?? !N.open;
    panel.hidden = !N.open;
    bell.setAttribute("aria-expanded", String(N.open));
    if (N.open) { N.page = 30; load(); }
  }

  function setup() {
    const actions = document.querySelector(".topbar-actions");
    if (!actions || typeof workiomHeaders !== "function" || !workiomHeaders()) return;

    badge = h("span", { class: "nt-badge", hidden: true });
    bell = h("button", { class: "btn btn-ghost nt-bell", type: "button", "aria-haspopup": "true", "aria-expanded": "false", title: tx("bell") },
      badge);
    bell.insertAdjacentHTML("afterbegin", '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15L6 16zM10 20a2 2 0 0 0 4 0" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>');

    list = h("ul", { class: "nt-list" });
    panel = h("div", { class: "nt-panel", role: "dialog", "aria-label": tx("title"), hidden: true },
      h("div", { class: "nt-panel-head" },
        h("strong", { class: "nt-title" }),
        h("button", { class: "nt-markall", type: "button", onclick: markAll })
      ),
      h("div", { class: "nt-seg" },
        h("button", { type: "button", onclick: () => { N.mode = "unread"; N.items = []; load(); } }),
        h("button", { type: "button", onclick: () => { N.mode = "all"; N.items = []; load(); } })
      ),
      list
    );

    const wrap = h("div", { class: "nt-wrap" }, bell, panel);
    actions.insertBefore(wrap, document.getElementById("btn-refresh"));

    bell.addEventListener("click", e => { e.stopPropagation(); toggle(); });
    panel.addEventListener("click", e => e.stopPropagation());
    document.addEventListener("click", () => { if (N.open) toggle(false); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && N.open) { toggle(false); bell.focus(); } });
    for (const b of document.querySelectorAll(".lang button")) b.addEventListener("click", () => { bell.title = tx("bell"); render(); });
    document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });

    render();
    poll();
    setInterval(poll, POLL_MS);
  }

  document.addEventListener("DOMContentLoaded", setup);
})();

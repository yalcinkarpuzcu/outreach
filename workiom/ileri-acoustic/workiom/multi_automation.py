"""
MultiAppAutomationBuilder — extends AutomationBuilder for multi-app solutions.

Additions over the base builder:
  • Lists are resolved across ALL state files (list names must be unique across
    the solution), so create_record / find_records / loop can target lists in
    other apps (correct appId is sent).
  • time_trigger: negative offset → "before" (timeTriggerType 0), else "after" (1).
  • webhook trigger ("webhook") → generates an app webhook (type 4).
  • to_roles accepts role NAMES (resolved via ROLE_IDS passed in).
  • to_field accepts "loop:Field" inside find_records.
  • send_email → compiled as an in-app notification (subject + body) to the same
    recipients (Workiom's SendEmail payload is not exposed via the public API).
  • Conditions: `{{F}} in ('A','B')`, `{{F}} not in (...)`, `{{loop:F}}`,
    `{{trigger:F}}` (inside find_records the bare `{{F}}` means the loop record).
  • Messages / formulas: `{{loop:F}}` and `{{trigger:F}}` refs.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from workiom.automation_builder import (
    AutomationBuilder, AutomationBuildError, ACTION_TYPE_MAP, TRIGGER_TYPE_MAP,
    field_ref, option_ref, source_field_ref, loop_field_ref, uuid_to_z,
)
from workiom.client import WorkiomAPIError
from workiom.state import STATE_DIR

TRIGGER_TYPE_MAP.setdefault("webhook", 4)
ACTION_TYPE_MAP["send_email"] = 3   # compiled as notify (see module docstring)


def _expand_in(cond: str) -> str:
    """{{F}} in ('A','B') → ({{F}} = 'A' or {{F}} = 'B'); `not in` → and/!=."""
    def rep(m: re.Match) -> str:
        ref, neg, body = m.group(1), m.group(2), m.group(3)
        vals = re.findall(r"'([^']*)'", body)
        if neg:
            return "(" + " and ".join(f"{ref} != '{v}'" for v in vals) + ")"
        return "(" + " or ".join(f"{ref} = '{v}'" for v in vals) + ")"
    return re.sub(r"(\{\{[^{}]+\}\})\s+(not\s+)?in\s*\(([^)]*)\)", rep, cond)


def _has_find(a) -> bool:
    if a.get("type") in ("find_records", "loop"):
        return True
    if a.get("type") == "condition":
        return any(_has_find(x) for x in a.get("then", []) + a.get("else", []))
    return False


def _and(g, e):
    return e if not g else f"({g}) and ({e})"


def flatten_finds(actions: list, guard: str | None = None) -> list:
    """Workiom motoru: bir koşul dalında yalnızca İLK find_records çalışıyor (canlı testle
    doğrulandı); üst seviyede hepsi çalışıyor. İçinde find olan koşulları açar: her find kendi
    üst seviye koşuluna (ata koşulların birleşimi, else için Not(...)) taşınır; sıra korunur."""
    out, pending = [], []

    def flush():
        if pending:
            out.append({"type": "condition", "if": guard, "then": list(pending)} if guard else None)
            if not guard:
                out.pop()
                out.extend(pending)
            pending.clear()

    for a in actions:
        if a.get("type") == "condition" and _has_find(a):
            flush()
            out.extend(flatten_finds(a.get("then", []), _and(guard, a["if"])))
            if a.get("else"):
                out.extend(flatten_finds(a["else"], _and(guard, f"Not({a['if']})")))
        elif a.get("type") in ("find_records", "loop"):
            pending.append(a)
            flush()
        else:
            pending.append(a)
    flush()
    return out


class MultiAppAutomationBuilder(AutomationBuilder):

    def __init__(self, client, state, role_ids: dict[str, int] | None = None):
        super().__init__(client, state)
        self.role_ids = role_ids or {}
        self._registry: dict[str, tuple[str, str]] = {}
        for sf in STATE_DIR.glob("*.json"):
            data = json.loads(sf.read_text())
            for lname, ldata in data.get("lists", {}).items():
                if ldata.get("id"):
                    self._registry[lname] = (data["app_id"], ldata["id"])

    # ── list resolution ──────────────────────────────────────────────────────
    def _list_id(self, name: str) -> str:
        if name not in self._registry:
            raise AutomationBuildError(f"List '{name}' not found in any state file")
        return self._registry[name][1]

    def _app_id(self, name: str) -> str:
        return self._registry[name][0]

    def _load_cache(self, list_name: str) -> None:
        if list_name in self._cache:
            return
        list_id = self._list_id(list_name)
        raw = self.client.get_all_fields(list_id)
        cache = {}
        by_id = {f["id"]: f for f in raw}
        for f in raw:
            if (not f.get("staticListValues") and f.get("lookupFieldId") and f.get("linkedFieldId")
                    and f.get("dataType") in (4, 16, 17)):
                hop = by_id.get(f["lookupFieldId"])
                if hop and hop.get("linkedListId"):
                    try:
                        src = next(x for x in self.client.get_all_fields(hop["linkedListId"])
                                   if x["id"] == f["linkedFieldId"])
                        f = {**f, "staticListValues": src.get("staticListValues", [])}
                    except (StopIteration, WorkiomAPIError):
                        pass
            cache[f["name"]] = {
                "id": f["id"], "dataType": f.get("dataType", -1),
                "options": {o["label"]: o["id"] for o in f.get("staticListValues", [])
                            if "label" in o and "id" in o},
            }
        self._cache[list_name] = cache

    # ── payload ──────────────────────────────────────────────────────────────
    def _build_payload(self, spec: dict) -> dict:
        ctx = spec["trigger"].get("list")
        if ctx:
            self._load_cache(ctx)
        return {
            "name": spec["name"],
            "isActive": spec.get("active", True),
            "trigger": self._build_trigger(spec["trigger"]),
            "actions": [self._build_action(a, ctx) for a in flatten_finds(spec.get("actions", []))],
        }

    def _build_trigger(self, trig: dict) -> dict:
        t = trig["type"]
        if isinstance(t, str):
            t = TRIGGER_TYPE_MAP[t]
        lname = trig.get("list")
        lid = self._list_id(lname) if lname else None
        if t == 0:
            return {"type": 0, "listId": lid}
        if t == 1:
            r: dict[str, Any] = {"type": 1, "listId": lid}
            if trig.get("watch_field"):
                r["fieldId"] = self._fid(lname, trig["watch_field"])
            return r
        if t == 2:
            off = trig.get("offset", 0)
            return {"type": 2, "listId": lid,
                    "dateFieldId": self._fid(lname, trig["date_field"]),
                    "offset": abs(off), "offsetType": 0,
                    "timeTriggerType": 0 if off < 0 else 1}
        if t == 3:
            return {"type": 3, "cronExpression": trig["cron"]}
        if t == 4:
            info = self.client.post("/api/services/app/Automation/GenerateWebhook", {},
                                    params={"appId": self.state.app_id, "authRequired": "false"})
            return {"type": 4, "webhookId": info["webhookId"]}
        if t == 5:
            return {"type": 5, "listId": lid}
        raise AutomationBuildError(f"Unknown trigger type: {t}")

    def _build_action(self, action: dict, ctx, *, loop_ctx=None, loop_uuid=None) -> dict:
        t = action["type"]
        if t == "send_email":
            msg = action.get("subject", "")
            if action.get("body"):
                msg = f"{msg}\n{action['body']}" if msg else action["body"]
            action = {**action, "type": "notify", "message": "✉️ " + msg}
            t = "notify"
        if isinstance(t, str):
            t = ACTION_TYPE_MAP[t]

        if t == 3:  # notify
            return {"id": str(uuid.uuid4()), "isEnabled": True,
                    "successWithWarningsEnabled": False, "issues": [], "type": 3,
                    "user": self._user_target(action, ctx, loop_ctx, loop_uuid),
                    "message": self._msg(action.get("message", ""), ctx, loop_ctx, loop_uuid)}

        if t == 2:  # condition
            return {"id": str(uuid.uuid4()), "isEnabled": True,
                    "successWithWarningsEnabled": False, "issues": [], "type": 2,
                    "condition": self._cond(action["if"], ctx, loop_ctx, loop_uuid),
                    "showBasic": False,
                    "successActions": [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                       for a in action.get("then", [])],
                    "failedActions": [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                      for a in action.get("else", [])]}

        if t == 10:  # approval
            body = super()._build_action({**action, "approver": self._approver_spec(action.get("approver", ""))},
                                         ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
            return body

        body = super()._build_action(action, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
        # Fix appId / listId for cross-app targets
        if t in (0, 7, 12) and action.get("list"):
            body["appId"] = self._app_id(action["list"])
            body["listId"] = self._list_id(action["list"])
        if t == 7 and loop_ctx:
            # Nested find_records: `loop:X` filter values refer to the OUTER loop record
            where = action.get("where", [])
            where = [where] if isinstance(where, dict) else where
            for flt, w in zip(body["filters"], where):
                v = w.get("value")
                if isinstance(v, str) and v.startswith("loop:"):
                    name = v[5:]
                    if name in ("_id", "id"):
                        flt["value1Mapping"] = {"type": 0, "sourceField": f"_id_A_{loop_uuid}"}
                    else:
                        flt["value1Mapping"] = {"type": 0, "sourceField":
                                                loop_field_ref(self._fid(loop_ctx, name), loop_uuid)}
        return body

    # ── helpers ──────────────────────────────────────────────────────────────
    def _approver_spec(self, approver):
        if isinstance(approver, str) and approver.startswith("roles:"):
            names = [x.strip() for x in approver[6:].split(",") if x.strip()]
            ids = [str(self.role_ids[n]) if n in self.role_ids else n for n in names]
            return "roles:" + ",".join(ids)
        return approver

    def _user_target(self, action, ctx, loop_ctx, loop_uuid) -> dict:
        roles = [self.role_ids.get(r, r) for r in action.get("to_roles", [])]
        users = list(action.get("to_users", []))
        if "to_field" in action:
            f = action["to_field"]
            if f.startswith("loop:"):
                fid = self._fid(loop_ctx, f[5:])
                tgt = {"type": 1, "userField": loop_field_ref(fid, loop_uuid)}
            else:
                tgt = {"type": 1, "userField": source_field_ref(self._fid(ctx, f))}
            return tgt
        return {"type": 0, "userIds": users, "roleIds": roles}

    def _ref(self, token: str, ctx, loop_ctx, loop_uuid, *, default_loop: bool) -> tuple[str, int | None]:
        """Resolve a {{token}} → (ref string, field id, list name)."""
        token = token.strip()
        if token.startswith("trigger:"):
            name = token[8:]
            return field_ref(self._fid(ctx, name)), self._fid(ctx, name), ctx
        if token.startswith("loop:"):
            name = token[5:]
            return field_ref(self._fid(loop_ctx, name), loop_uuid), self._fid(loop_ctx, name), loop_ctx
        if default_loop and loop_ctx:
            return field_ref(self._fid(loop_ctx, token), loop_uuid), self._fid(loop_ctx, token), loop_ctx
        return field_ref(self._fid(ctx, token)), self._fid(ctx, token), ctx

    def _msg(self, msg: str, ctx, loop_ctx, loop_uuid) -> str:
        def sub(m):
            try:
                return self._ref(m.group(1), ctx, loop_ctx, loop_uuid, default_loop=False)[0]
            except AutomationBuildError:
                print(f"      ⚠️  message ref '{m.group(1)}' not found")
                return m.group(0)
        return re.sub(r"\{\{(.+?)\}\}", sub, msg)

    def _cond(self, cond: str, ctx, loop_ctx, loop_uuid) -> str:
        cond = _expand_in(cond)
        dl = bool(loop_ctx)

        def blank(m):
            fn = "IsNotBlank" if "not" in m.group(1).lower() else "IsBlank"
            return f"{fn}({self._ref(m.group(2), ctx, loop_ctx, loop_uuid, default_loop=dl)[0]})"
        cond = re.sub(r"(is\s*not\s*blank|is\s*blank)\s*\(\s*\{\{([^{}]+?)\}\}\s*\)", blank, cond,
                      flags=re.IGNORECASE)

        def eq(m):
            ref, fid, lname = self._ref(m.group(1), ctx, loop_ctx, loop_uuid, default_loop=dl)
            op, label = m.group(2), m.group(3)
            opt = self._opt_uuid(lname, self._name_of(lname, fid), label)
            if opt:
                suffix = loop_uuid if (lname == loop_ctx and dl and not m.group(1).strip().startswith("trigger:")) else None
                rhs = option_ref(fid, opt, suffix)
            else:
                rhs = f'"{label}"'
            return f"{ref}{' <> ' if op in ('!=', '<>') else ' = '}{rhs}"
        cond = re.sub(r"\{\{([^{}]+?)\}\}\s*(!=|<>|=)\s*'([^']*)'", eq, cond)

        def plain(m):
            return self._ref(m.group(1), ctx, loop_ctx, loop_uuid, default_loop=dl)[0]
        cond = re.sub(r"\{\{([^{}]+?)\}\}", plain, cond)
        cond = re.sub(r"\s!=\s", " <> ", cond)
        return cond

    def _name_of(self, lname, fid):
        for n, e in self._cache.get(lname, {}).items():
            if e["id"] == fid:
                return n
        return ""

    def _build_mappings(self, fields, target, source, *, loop_ctx=None, loop_uuid=None):
        out = []
        for fname, val in fields.items():
            if isinstance(val, str) and val.startswith("formula:"):
                fid = self._fid(target, fname)
                expr = re.sub(r"\{\{(.+?)\}\}",
                              lambda m: self._ref(m.group(1), source, loop_ctx, loop_uuid,
                                                  default_loop=False)[0],
                              val[8:])
                out.append({"fieldId": fid, "appendValue": False,
                            "value": {"type": 2, "formula": expr}})
            else:
                out.extend(super()._build_mappings({fname: val}, target, source,
                                                   loop_ctx=loop_ctx, loop_uuid=loop_uuid))
        return out

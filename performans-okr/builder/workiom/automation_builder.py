"""
AutomationBuilder — compiles human-readable automation specs to Workiom API payloads.

Confirmed schema patterns (from live workspace analysis):
  - Field refs in conditions/messages: _F_{fieldId}_A_00000000z0000z0000z0000z000000000000
  - Option refs in conditions:         _F_{fieldId}_A_..._V_{uuid_z_format}
  - UUID z-format: replace all '-' with 'z' (e.g. 47b423db-0a7e → 47b423dbz0a7e)
  - Source fields in create/update:    {fieldId}_A_00000000-0000-0000-0000-000000000000
  - Special current-record link:       _id_A_00000000-0000-0000-0000-000000000000
  - fieldValueMappings option UUIDs:   normal dash format (type 1 static value)

Spec format:
  {
    "name": "My Automation",
    "active": True,
    "trigger": {
      "type": "record_created",   # or int: 0
      # For "record_updated":   "list", "watch_field" (optional — omit to fire on any field)
      # For "time_trigger":     "list", "date_field", "offset" (days, negative=before)
      # For "cron":             "cron" (cron expression string)
      # For "record_deleted":   "list"
      "list": "List Name",
    },
    "actions": [
      # Notify:
      {
        "type": "notify",
        "to_users": [userId, ...],     # specific user IDs
        "to_field":  "Manager",        # OR: user from a USER/MULTIUSER field
        "to_roles":  [roleId, ...],    # OR: users by role
        "message": "Hello {{First Name}} — your {{Status}} has changed."
      },

      # Condition (wrap other actions):
      {
        "type": "condition",
        "if": "{{Status}} = 'Hired'",         # see condition syntax below
        "then": [ ... ],                       # actions if true
        "else": [ ... ],                       # actions if false (optional)
      },

      # Approval gate:
      {
        "type": "approval",
        "title":    "Approval Requested",                  # plain string
        "subtitle": "Pending approval for {{Name}}",       # compiled with {{field}} refs
        "approver": "field:Manager",                       # user from a USER field
        # OR: "approver": "users:110539,110540"            # specific user IDs
        # OR: "approver": "roles:5,6"                      # users by role ID
        "timeout_days": None,                              # or int (e.g. 3)
        "require_rejection_message": False,
        "on_approve": [ ... ],                             # actions if approved
        "on_reject":  [ ... ],                             # actions if rejected
      },

      # Update current record:
      {
        "type": "update_record",
        "fields": {
          "Status":    "Completed",             # static label (resolved to option UUID)
          "Closed At": "formula:Today()",       # formula value
        }
      },

      # Create a record in another list:
      {
        "type": "create_record",
        "list": "Target List",
        "fields": {
          "Name":    "formula:Concat('Task: ', 'value')",
          "Owner":   "copy:Assigned To",       # copy field from trigger record
          "Link":    "id",                     # copy current record's _id as a link
        }
      },

      # Loop — iterate over records in a list, run actions for each:
      {
        "type": "loop",
        "list":        "Target List",          # required: which list to iterate
        "view":        "Active Tasks",         # optional: filter via a saved view
        "sort_by":     "Due Date ASC",         # optional: "FieldName ASC|DESC"
        "max_records": 10,                     # optional: default 10
        "actions":    [ ... ],                 # actions to run per record
        "no_results": [ ... ],                 # optional: run if no records found
      },
    ]
  }

Condition syntax:
  {{Field}} = 'Option Label'           → field ref equals option UUID
  {{Field}} != 'Value' / {{F}} <> 'V'  → not-equals
  isBlank({{Field}})                   → IsBlank(field ref)
  isNotBlank({{Field}})                → IsNotBlank(field ref)
  {{F1}} = 'V1' and {{F2}} = 'V2'     → AND combination
  {{F1}} = 'V1' or {{F2}} = 'V2'      → OR combination

Approver spec syntax (string shorthand):
  "field:Field Name"       → user from a USER/MULTIUSER field on the record
  "users:111,222"          → specific user IDs (comma-separated)
  "roles:5,6"              → users by role ID (comma-separated)
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState

# ─── Field reference helpers ──────────────────────────────────────────────────

_Z_SUFFIX = "_A_00000000z0000z0000z0000z000000000000"   # used in condition/message refs
_D_SUFFIX  = "_A_00000000-0000-0000-0000-000000000000"  # used in source-field refs


def field_ref(field_id: int, loop_uuid: str | None = None) -> str:
    """Condition / message reference: _F_<id>_A_<z-suffix>.

    When `loop_uuid` is set (a find_records action's UUID, dash format), the
    suffix carries that UUID in z-format — required for conditions evaluated
    against the CURRENT iteration record inside a find_records loop. Without
    it the field reference resolves against the trigger record (all-zero
    UUID), which is "missing" for cron-triggered automations.
    """
    if loop_uuid:
        return f"_F_{field_id}_A_{uuid_to_z(loop_uuid)}"
    return f"_F_{field_id}{_Z_SUFFIX}"


def uuid_to_z(uid: str) -> str:
    """47b423db-0a7e-42f1-83b5-18966ee376b4  →  47b423dbz0a7ez42f1z83b5z18966ee376b4"""
    return uid.replace("-", "z")


def option_ref(field_id: int, option_uuid: str, loop_uuid: str | None = None) -> str:
    """Condition option: _F_{fieldId}_A_..._V_{uuid_z_format}"""
    return f"{field_ref(field_id, loop_uuid)}_V_{uuid_to_z(option_uuid)}"


def source_field_ref(field_id: int | str) -> str:
    """fieldValueMappings source: {fieldId}_A_00000000-0000-0000-0000-000000000000

    The all-zero UUID suffix marks "this is from the trigger record".
    For find_records loops, the suffix carries the find_records action's UUID
    instead — see loop_field_ref().
    """
    return f"{field_id}{_D_SUFFIX}"


def loop_field_ref(field_id: int | str, loop_uuid: str) -> str:
    """Source-field ref for a record in the CURRENT find_records iteration.

    Workiom encodes "which context to read from" in the UUID suffix:
      • trigger record  → all-zero UUID  (00000000-0000-0000-0000-000000000000)
      • loop record     → the find_records action's `id` UUID
    Confirmed by reverse-engineering automation 10 on sascodemo (2026-05-10).
    """
    return f"{field_id}_A_{loop_uuid}"


# ─── Type maps ────────────────────────────────────────────────────────────────

TRIGGER_TYPE_MAP: dict[str, int] = {
    "record_created": 0,
    "record_updated": 1,
    "time_trigger":   2,
    "cron":           3,
    "record_deleted": 5,
}

ACTION_TYPE_MAP: dict[str, int] = {
    "create_record":   0,
    "update_record":   1,
    "condition":       2,
    "notify":          3,
    "send_email":      4,
    "send_email_via":  5,   # email via integration (Gmail/Outlook/SMTP)
    "find_records":    7,
    "call_api":        9,   # confirmed type 9 (not 8) from live workspace data
    "approval":        10,
    "delete_record":   11,
    "loop":            12,  # iterate over records in a list/view
    "ai_agent":        15,  # Workiom AI agent
}


# ─── Errors ───────────────────────────────────────────────────────────────────

class AutomationBuildError(Exception):
    pass


# ─── Builder ──────────────────────────────────────────────────────────────────

class AutomationBuilder:
    """Compiles human-readable automation specs to Workiom API payloads and creates them."""

    def __init__(self, client: WorkiomClient, state: AppState):
        self.client = client
        self.state  = state
        # Cache: list_name → {field_name: {"id": int, "dataType": int, "options": {label: uuid}}}
        self._cache: dict[str, dict[str, dict]] = {}

    # ─── Public ───────────────────────────────────────────────────────────────

    def build_all(self, app_id: str, auto_specs: list[dict]) -> None:
        for spec in auto_specs:
            self._ensure_automation(app_id, spec)

    # ─── Idempotency ──────────────────────────────────────────────────────────

    def _ensure_automation(self, app_id: str, spec: dict) -> int | None:
        name = spec["name"]
        if self.state.get_automation_id(name):
            self._log(name, "exists (state)")
            return self.state.get_automation_id(name)

        # Check live API
        try:
            for a in self.client.get_all_automations(app_id):
                if a["name"] == name:
                    self.state.set_automation_id(name, a["id"])
                    self._log(name, "exists (API)")
                    return a["id"]
        except WorkiomAPIError:
            pass

        # Build and create
        try:
            body   = self._build_payload(spec)
            result = self.client.create_automation(app_id, body)
            self.state.set_automation_id(name, result["id"])
            self._log(name, "created", str(result["id"]))
            return result["id"]
        except AutomationBuildError as e:
            print(f"    ⚠️  ⚡ [{name}] build error: {e}")
            return None
        except WorkiomAPIError as e:
            print(f"    ⚠️  ⚡ [{name}] API error: {e.message}")
            return None

    # ─── Payload ──────────────────────────────────────────────────────────────

    def _build_payload(self, spec: dict) -> dict:
        ctx = spec["trigger"].get("list")
        if ctx:
            self._load_cache(ctx)
        return {
            "name":     spec["name"],
            "isActive": spec.get("active", True),
            "trigger":  self._build_trigger(spec["trigger"]),
            "actions":  [self._build_action(a, ctx) for a in spec.get("actions", [])],
        }

    # ─── Trigger ──────────────────────────────────────────────────────────────

    def _build_trigger(self, trig: dict) -> dict:
        t = trig["type"]
        if isinstance(t, str):
            t = TRIGGER_TYPE_MAP[t]

        list_name = trig.get("list")
        list_id   = self.state.get_list_id(list_name) if list_name else None

        if t == 0:  # record_created
            return {"type": 0, "listId": list_id}

        if t == 1:  # record_updated
            result: dict[str, Any] = {"type": 1, "listId": list_id}
            if trig.get("watch_field"):
                result["fieldId"] = self._fid(list_name, trig["watch_field"])
            return result

        if t == 2:  # time_trigger (relative to a date field)
            date_fid = self._fid(list_name, trig["date_field"]) if trig.get("date_field") else None
            return {
                "type":            2,
                "listId":          list_id,
                "dateFieldId":     date_fid,
                "offset":          abs(trig.get("offset", 0)),
                "offsetType":      0,   # 0 = days
                "timeTriggerType": 1,   # 1 = fire N days before/after the date
            }

        if t == 3:  # cron / recurring
            return {"type": 3, "cronExpression": trig["cron"]}

        if t == 5:  # record_deleted
            return {"type": 5, "listId": list_id}

        raise AutomationBuildError(f"Unknown trigger type: {t}")

    # ─── Actions ──────────────────────────────────────────────────────────────

    def _build_action(self, action: dict, ctx: str | None,
                      *, loop_ctx: str | None = None,
                      loop_uuid: str | None = None) -> dict:
        """Compile one action to its API payload.

        ctx       — list name of the trigger record (used to resolve `trigger:Field`)
        loop_ctx  — list name of the find_records iteration list, when this action
                    is nested inside a find_records (used to resolve `loop:Field`)
        loop_uuid — the find_records action's UUID, used in sourceField suffix for
                    "current iteration record" references
        """
        t = action["type"]
        if isinstance(t, str):
            t = ACTION_TYPE_MAP[t]

        aid  = str(uuid.uuid4())
        base = {"id": aid, "isEnabled": True, "successWithWarningsEnabled": False, "issues": []}

        # ── Notify ────────────────────────────────────────────────────────────
        if t == 3:
            if "to_loop_field" in action:
                fid = self._fid(loop_ctx, action["to_loop_field"])
                user = {"type": 1, "userField": loop_field_ref(fid, loop_uuid)}
            else:
                user = self._build_user_target(action, ctx)
            return {
                **base,
                "type":    3,
                "user":    user,
                "message": self._compile_message(action.get("message", ""), ctx),
            }

        # ── Condition ─────────────────────────────────────────────────────────
        if t == 2:
            # Inside a find_records / loop block the condition is evaluated against
            # the CURRENT iteration record, so its {{Field}} refs should resolve
            # against `loop_ctx` AND use the find_records action UUID as the
            # `_A_` suffix (not the all-zero trigger-record suffix). Outside
            # loops (normal triggers) use `ctx` and the trigger suffix.
            condition_ctx = loop_ctx if loop_ctx else ctx
            return {
                **base,
                "type":          2,
                "condition":     self._compile_condition(action["if"], condition_ctx,
                                                          loop_uuid=loop_uuid),
                "showBasic":     False,
                "successActions": [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                    for a in action.get("then", [])],
                "failedActions":  [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                    for a in action.get("else", [])],
            }

        # ── Update record (current) ───────────────────────────────────────────
        if t == 1:
            # "target: trigger" forces the trigger record even inside find_records.
            # Without it, update_record inside find_records targets the loop record.
            force_trigger = action.get("target") == "trigger"
            if force_trigger or not loop_uuid:
                records_mapping = {"type": 0, "actionId": "00000000-0000-0000-0000-000000000000"}
                lhs_ctx = ctx
            else:
                records_mapping = {"type": 0, "actionId": loop_uuid}
                lhs_ctx = loop_ctx
            return {
                **base,
                "type": 1,
                "recordsMapping": records_mapping,
                "fieldValueMappings": self._build_mappings(
                    action.get("fields", {}), lhs_ctx, ctx,
                    loop_ctx=loop_ctx, loop_uuid=loop_uuid,
                ),
            }

        # ── Create record ─────────────────────────────────────────────────────
        if t == 0:
            target = action.get("list")
            if target:
                self._load_cache(target)
            return {
                **base,
                "type":   0,
                "appId":  self.state.app_id,
                "listId": self.state.get_list_id(target) if target else None,
                "fieldValueMappings": self._build_mappings(
                    action.get("fields", {}), target, ctx,
                    loop_ctx=loop_ctx, loop_uuid=loop_uuid,
                ),
            }

        # ── Approval ──────────────────────────────────────────────────────────
        if t == 10:
            return {
                **base,
                "type":                      10,
                "title":                     action.get("title", "Approval Requested"),
                "subtitle":                  self._compile_message(action.get("subtitle", ""), ctx),
                "approvals":                 self._build_approver(action.get("approver", ""), ctx),
                "timeoutInDays":             action.get("timeout_days"),
                "isRejectionMessageRequired": action.get("require_rejection_message", False),
                "recordsMapping":            {"type": 0, "actionId": "00000000-0000-0000-0000-000000000000"},
                "approveActions":            [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                                for a in action.get("on_approve", [])],
                "rejectActions":             [self._build_action(a, ctx, loop_ctx=loop_ctx, loop_uuid=loop_uuid)
                                                for a in action.get("on_reject", [])],
            }

        # ── Delete record ─────────────────────────────────────────────────────
        if t == 11:
            # Inside a find_records loop, delete acts on the current loop record.
            records_mapping = (
                {"type": 0, "actionId": loop_uuid}
                if loop_uuid
                else {"type": 0, "actionId": "00000000-0000-0000-0000-000000000000"}
            )
            return {**base, "type": 11, "recordsMapping": records_mapping}

        # ── find_records (DYNAMIC iteration scoped to the trigger record) ─────
        # Use this — NOT `loop` (type 12) — when you need to iterate child records
        # of the trigger (e.g. "PR Items where PR = trigger PO's PR"). The filter's
        # value1Mapping carries a sourceField with the all-zero UUID suffix, which
        # Workiom evaluates at runtime against the trigger record's field.
        # Confirmed shape from automation 10 on sascodemo (2026-05-10).
        if t == 7:
            target = action.get("list")
            if not target:
                raise AutomationBuildError("find_records action requires a 'list' key")
            self._load_cache(target)
            list_id = self.state.get_list_id(target)

            # Build filters — `where` may be a single dict or a list of dicts.
            where = action.get("where", [])
            if isinstance(where, dict):
                where = [where]
            filters = [self._build_find_filter(w, find_list=target, trigger_ctx=ctx)
                       for w in where]

            # Optional saved view (additional static filter)
            view_id = (self.state.get_view_id(target, action["view"])
                       if action.get("view") else None)

            # Sorting — same shape as loop's: "Field Name ASC|DESC"
            sorting = self._compile_sorting(action.get("sort_by"), target)

            # The find_records action's UUID is referenced by inner actions that
            # need to read fields from the CURRENT iteration record.
            return {
                **base,                          # base["id"] = the find UUID
                "type":          7,
                "appId":         action.get("app_id", self.state.app_id),
                "listId":        list_id,
                "viewId":        view_id,
                "sorting":       sorting,
                "recordsCount":  action.get("max", action.get("max_records", 200)),
                "filters":       filters,
                "actions":       [self._build_action(a, ctx,
                                                       loop_ctx=target,
                                                       loop_uuid=aid)
                                    for a in action.get("actions", [])],
                "noResultActions": [self._build_action(a, ctx,
                                                        loop_ctx=loop_ctx,
                                                        loop_uuid=loop_uuid)
                                    for a in action.get("no_results", [])],
            }

        # ── Loop (iterate records) ────────────────────────────────────────────
        # Loop iterates a list/saved-view with a STATIC filter — use find_records
        # (type 7) instead when you need the iteration scoped to the trigger.
        if t == 12:
            target = action.get("list")
            if not target:
                raise AutomationBuildError("Loop action requires a 'list' key")
            if target:
                self._load_cache(target)
            list_id = self.state.get_list_id(target)
            view_id = (self.state.get_view_id(target, action["view"])
                       if action.get("view") else None)
            sorting = self._compile_sorting(action.get("sort_by"), target)
            return {
                **base,
                "type":          12,
                "appId":         self.state.app_id,
                "listId":        list_id,
                "viewId":        view_id,
                "sorting":       sorting,
                "recordsCount":  action.get("max_records", 10),
                "actions":       [self._build_action(a, ctx,
                                                       loop_ctx=target,
                                                       loop_uuid=aid)
                                    for a in action.get("actions", [])],
                "noResultActions": [self._build_action(a, ctx,
                                                        loop_ctx=loop_ctx,
                                                        loop_uuid=loop_uuid)
                                    for a in action.get("no_results", [])],
            }

        raise AutomationBuildError(f"Unsupported action type: {t} — check A.* constants for supported types")

    # ─── Helpers for find_records / loop ──────────────────────────────────────

    _FILTER_OP_MAP = {
        "equals": 1, "=": 1, "==": 1,
        "not_equals": 2, "!=": 2, "<>": 2,
        "contains": 3,
        "is_blank":     4,
        "is_not_blank": 5,
        # Add more as Workiom exposes them; falls back to raw int if user passes one.
    }

    def _build_find_filter(self, where: dict, *, find_list: str,
                           trigger_ctx: str | None) -> dict:
        """Compile a find_records filter clause to its API shape.

        Spec form:  {"field": "<field on find list>",
                     "op":    "equals" | "!=" | int,
                     "value": "trigger:<Field on trigger>"  | "loop:<Field>" | <static> }
        """
        find_fid = self._fid(find_list, where["field"])
        op_in = where.get("op", "equals")
        op_int = (self._FILTER_OP_MAP.get(op_in, op_in) if isinstance(op_in, str) else op_in)

        return {
            "fieldId":       find_fid,
            "value1Mapping": self._compile_filter_value(
                where.get("value"), trigger_ctx=trigger_ctx,
                find_list=find_list, find_field=where["field"],
            ),
            "value2Mapping": (self._compile_filter_value(
                where["value2"], trigger_ctx=trigger_ctx,
                find_list=find_list, find_field=where["field"],
            ) if where.get("value2") is not None else None),
            "operator": op_int,
        }

    def _compile_filter_value(self, val: Any, *, trigger_ctx: str | None,
                              find_list: str, find_field: str | None = None) -> dict:
        """Compile a filter value to value1Mapping/value2Mapping shape.

        • "trigger:Field"  → sourceField from trigger record (all-zero suffix)
        • "loop:Field"     → sourceField from current find record (find UUID suffix —
                              note: filter values resolve at find time so we use
                              find list ctx with all-zero suffix here)
        • "<SELECT option label>" → static type-1 value with the option UUID resolved
                                    (so equality filters against SELECT/STATUS fields
                                    actually match the stored option UUID)
        • "<literal>"      → static type-1 value (unchanged)
        """
        if isinstance(val, str) and val.startswith("trigger:"):
            fname = val[len("trigger:"):]
            fid = (self._fid(trigger_ctx, fname) if fname not in ("_id", "id")
                   else "_id")
            return {"type": 0, "sourceField": source_field_ref(fid)}
        if isinstance(val, str) and val.startswith("loop:"):
            # rare in filters but supported for nested finds
            fname = val[len("loop:"):]
            fid = (self._fid(find_list, fname) if fname not in ("_id", "id")
                   else "_id")
            return {"type": 0, "sourceField": source_field_ref(fid)}
        # Literal value — if the find field is a SELECT/STATUS and the value matches
        # one of its option labels, resolve to the option UUID (the stored shape).
        if isinstance(val, str) and find_field:
            try:
                opt_uuid = self._opt_uuid(find_list, find_field, val)
                if opt_uuid:
                    return {"type": 1, "value": opt_uuid}
            except AutomationBuildError:
                pass
        return {"type": 1, "value": val}

    def _compile_sorting(self, sort_by: str | None,
                          list_name: str | None) -> str | None:
        if not sort_by:
            return None
        parts = sort_by.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].upper() in ("ASC", "DESC") and list_name:
            try:
                fid = self._fid(list_name, parts[0].strip())
                return f"{fid} {parts[1].upper()}"
            except AutomationBuildError:
                pass
        return sort_by  # pass-through raw

    # ─── User target ──────────────────────────────────────────────────────────

    def _build_user_target(self, action: dict, ctx: str | None) -> dict:
        if "to_field" in action:
            fid = self._fid(ctx, action["to_field"])
            return {"type": 1, "userField": source_field_ref(fid)}
        return {
            "type":    0,
            "userIds": list(action.get("to_users", [])),
            "roleIds": list(action.get("to_roles", [])),
        }

    # ─── Approver ─────────────────────────────────────────────────────────────

    def _build_approver(self, approver: str | dict, ctx: str | None) -> dict:
        """
        Parse approver spec:
          "field:Manager"     → {type: 1, userField: "fieldId_A_..."}
          "users:110539,222"  → {type: 0, userIds: [110539, 222], roleIds: []}
          "roles:5,6"         → {type: 0, userIds: [], roleIds: [5, 6]}
          {}                  → pass-through dict (raw API shape)
        """
        if isinstance(approver, dict):
            return approver  # already raw API shape

        if not approver:
            return {"type": 0, "userIds": [], "roleIds": []}

        if approver.startswith("field:"):
            field_name = approver[len("field:"):]
            fid = self._fid(ctx, field_name)
            return {"type": 1, "userField": source_field_ref(fid)}

        if approver.startswith("users:"):
            ids = [int(x.strip()) for x in approver[len("users:"):].split(",") if x.strip()]
            return {"type": 0, "userIds": ids, "roleIds": []}

        if approver.startswith("roles:"):
            ids = [int(x.strip()) for x in approver[len("roles:"):].split(",") if x.strip()]
            return {"type": 0, "userIds": [], "roleIds": ids}

        raise AutomationBuildError(
            f"Invalid approver spec '{approver}'. "
            f"Use 'field:FieldName', 'users:id1,id2', or 'roles:id1,id2'."
        )

    # ─── Field value mappings ─────────────────────────────────────────────────

    def _build_mappings(self, fields: dict, target: str | None, source: str | None,
                        *, loop_ctx: str | None = None,
                        loop_uuid: str | None = None) -> list[dict]:
        """
        Value spec strings:
          "Some Label"            → type 1 static (option UUID if SELECT, else raw string)
          "formula:Today()"       → type 2 formula
          "copy:Field Name"       → type 0 copy from source ctx (legacy alias for trigger:)
          "trigger:Field Name"    → type 0 read from trigger record (all-zero suffix)
          "trigger:_id"           → type 0 trigger record's _id (for back-link fields)
          "loop:Field Name"       → type 0 read from current find_records iteration
                                     (uses the find_records action's UUID as suffix)
          "loop:_id"              → type 0 current iteration record's _id
          "id" / "_id"            → type 0 trigger record's _id (legacy)
        """
        mappings = []
        for fname, val in fields.items():
            fid = self._fid(target, fname)
            mapping_val: dict[str, Any]

            # ── trigger record references ────────────────────────────────────
            if val in ("id", "_id"):
                mapping_val = {"type": 0, "sourceField": f"_id{_D_SUFFIX}"}

            elif isinstance(val, str) and val.startswith("trigger:"):
                src_name = val[len("trigger:"):]
                if src_name in ("_id", "id"):
                    mapping_val = {"type": 0, "sourceField": f"_id{_D_SUFFIX}"}
                else:
                    src_fid = self._fid(source, src_name)
                    mapping_val = {"type": 0, "sourceField": source_field_ref(src_fid)}

            # ── loop (current find_records iteration) references ─────────────
            elif isinstance(val, str) and val.startswith("loop:"):
                if not loop_uuid or not loop_ctx:
                    raise AutomationBuildError(
                        f"'{val}' used outside a find_records / loop block — "
                        f"loop refs are only valid inside iterating actions."
                    )
                src_name = val[len("loop:"):]
                if src_name in ("_id", "id"):
                    mapping_val = {"type": 0, "sourceField": f"_id_A_{loop_uuid}"}
                else:
                    src_fid = self._fid(loop_ctx, src_name)
                    mapping_val = {"type": 0, "sourceField": loop_field_ref(src_fid, loop_uuid)}

            elif isinstance(val, str) and val.startswith("formula:"):
                expr = val[len("formula:"):]

                def _ref(m, _src=source, _lctx=loop_ctx, _luuid=loop_uuid):
                    name = m.group(1).strip()
                    if name.startswith("loop:"):
                        return field_ref(self._fid(_lctx, name[5:]), _luuid)
                    return field_ref(self._fid(_src, name))
                mapping_val = {"type": 2, "formula": re.sub(r"\{\{(.+?)\}\}", _ref, expr)}

            elif isinstance(val, str) and val.startswith("copy:"):
                # Legacy alias for trigger: — kept for back-compat.
                src_name = val[len("copy:"):]
                src_fid  = self._fid(source, src_name)
                mapping_val = {"type": 0, "sourceField": source_field_ref(src_fid)}

            else:
                # Static: try to resolve as option label → UUID (normal dash format)
                opt = self._opt_uuid(target, fname, str(val))
                mapping_val = {"type": 1, "value": opt if opt else str(val)}

            mappings.append({"fieldId": fid, "appendValue": False, "value": mapping_val})
        return mappings

    # ─── Message compiler ─────────────────────────────────────────────────────

    def _compile_message(self, msg: str, ctx: str | None) -> str:
        """{{Field Name}} → _F_{id}_A_..."""
        def sub(m: re.Match) -> str:
            name = m.group(1).strip()
            try:
                return field_ref(self._fid(ctx, name))
            except AutomationBuildError:
                print(f"      ⚠️  Message: field '{name}' not found in '{ctx}'")
                return m.group(0)
        return re.sub(r"\{\{(.+?)\}\}", sub, msg)

    # ─── Condition compiler ───────────────────────────────────────────────────

    def _compile_condition(self, cond: str, ctx: str | None,
                            loop_uuid: str | None = None) -> str:
        """
        Transforms human-readable condition to Workiom internal format.

        When `loop_uuid` is set, field refs carry that UUID as the `_A_` suffix
        (z-format) — required for conditions inside find_records loops where
        the condition is evaluated against the CURRENT iteration record. Without
        it the refs use the all-zero UUID (trigger record) which doesn't exist
        for cron-triggered loops and renders as "field is missing" in the UI.

        Handles:
          {{F}} = 'V'        →  _F_id_A_... = _F_id_A_..._V_{uuid_z}  (SELECT option)
          {{F}} != 'V'       →  _F_id_A_... <> _F_id_A_..._V_{uuid_z}
          {{F}} = 'V'        →  _F_id_A_... = "V"  (TEXT/NUMBER fields — raw value)
          isBlank({{F}})     →  IsBlank(_F_id_A_...)
          isNotBlank({{F}})  →  IsNotBlank(_F_id_A_...)
          and / or           →  kept as-is (already Workiom syntax)
        """
        # 1. isBlank / isNotBlank wrappers
        def _blank(m: re.Match) -> str:
            fn   = "IsNotBlank" if "not" in m.group(1).lower() else "IsBlank"
            name = m.group(2).strip()
            try:
                return f"{fn}({field_ref(self._fid(ctx, name), loop_uuid)})"
            except AutomationBuildError:
                return m.group(0)

        cond = re.sub(
            r"(is\s*not\s*blank|is\s*blank)\s*\(\s*\{\{([^{}]+?)\}\}\s*\)",
            _blank,
            cond,
            flags=re.IGNORECASE,
        )

        # 2. {{Field}} = / != / <> 'Value'
        def _eq(m: re.Match) -> str:
            fname = m.group(1).strip()
            op    = m.group(2).strip()
            label = m.group(3)
            try:
                fid   = self._fid(ctx, fname)
                fref  = field_ref(fid, loop_uuid)
                opt   = self._opt_uuid(ctx, fname, label)
                if opt:
                    rhs = option_ref(fid, opt, loop_uuid)
                else:
                    rhs = f'"{label}"'
                api_op = " <> " if op in ("!=", "<>") else " = "
                return f"{fref}{api_op}{rhs}"
            except AutomationBuildError:
                return m.group(0)

        cond = re.sub(
            r"\{\{([^{}]+?)\}\}\s*(!=|<>|=)\s*'([^']*)'",
            _eq,
            cond,
        )

        # 3. Remaining bare {{Field}} references
        def _plain(m: re.Match) -> str:
            name = m.group(1).strip()
            try:
                return field_ref(self._fid(ctx, name), loop_uuid)
            except AutomationBuildError:
                return m.group(0)

        cond = re.sub(r"\{\{([^{}]+?)\}\}", _plain, cond)
        return cond

    # ─── Field cache ──────────────────────────────────────────────────────────

    def _load_cache(self, list_name: str) -> None:
        if list_name in self._cache:
            return
        list_id = self.state.get_list_id(list_name)
        if not list_id:
            raise AutomationBuildError(f"List '{list_name}' not in state — build it first.")
        try:
            raw = self.client.get_all_fields(list_id)
        except WorkiomAPIError as e:
            raise AutomationBuildError(f"Cannot fetch fields for '{list_name}': {e}")

        cache = {}
        for f in raw:
            entry = {
                "id":       f["id"],
                "dataType": f.get("dataType", -1),
                "options":  {opt["label"]: opt["id"]
                             for opt in f.get("staticListValues", [])
                             if "label" in opt and "id" in opt},
            }
            cache[f["name"]] = entry
            # STATUS field on PROCESS lists: always register under "Status" alias
            if f.get("dataType") == 16 and "Status" not in cache:
                cache["Status"] = entry
        self._cache[list_name] = cache

    def _fid(self, list_name: str | None, field_name: str) -> int:
        """Look up a field ID from cache."""
        if not list_name:
            raise AutomationBuildError(f"No context list for field '{field_name}'")
        self._load_cache(list_name)
        entry = self._cache.get(list_name, {}).get(field_name)
        if not entry:
            raise AutomationBuildError(f"Field '{field_name}' not found in list '{list_name}'")
        return entry["id"]

    def _opt_uuid(self, list_name: str | None, field_name: str, label: str) -> str | None:
        """Return option UUID for a SELECT/STATUS/MULTISELECT field, or None."""
        if not list_name:
            return None
        try:
            self._load_cache(list_name)
            entry = self._cache.get(list_name, {}).get(field_name)
            if not entry:
                return None
            return entry["options"].get(label)
        except AutomationBuildError:
            return None

    # ─── Logging ──────────────────────────────────────────────────────────────

    @staticmethod
    def _log(name: str, action: str, id_: str = "") -> None:
        id_str = f" ({id_})" if id_ and "created" in action else ""
        status = "✅" if "created" in action else "·"
        print(f"  {status} ⚡ [automation] {name:<45s} {action}{id_str}")

"""
Builder — idempotent engine that turns a spec dict into a live Workiom app.

Build phases (in order):
  1.   App         — create or find by name, apply icon/color
  1.5  Folders     — create or find by name (state-only idempotency)
  2.   Lists       — create or find by name, assigned to folder if applicable
  3.   Fields      — non-LINK fields first, then LINK fields (so targets exist)
  4.   Views       — create or find by name per list
  5.   Forms       — create or find by name per list
  6.   Automations — stubbed (logged, not created)

Spec format supports both:
  - Top-level "lists" key (legacy / no folders)
  - "folders" key: [{"name": "...", "lists": [...]}]  (folder-grouped)

Every create is guarded: check state → check live API → create.
State is saved after every successful operation.
"""
from __future__ import annotations

import time as _time
import uuid as _uuid
from typing import Any

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.constants import F, W, AGG, FREQ, COLORS, color_for
from workiom.resolver import Resolver, ResolutionError
from workiom.state import AppState


class Builder:
    def __init__(self, client: WorkiomClient, state: AppState,
                 resolver: Resolver, verbose: bool = True):
        self.client = client
        self.state = state
        self.resolver = resolver
        self.verbose = verbose
        # Cache for SELECT/STATUS/MULTISELECT option labels → UUIDs
        # Key: "{list_name}::{field_name}", Value: {label: uuid, ...}
        self._option_cache: dict[str, dict[str, str]] = {}
        # Cache for field dataType: "{list_name}::{field_name}" → int
        self._field_type_cache: dict[str, int] = {}
        # Cache for systemFieldType: "{list_name}::{field_name}" → int (0 = user field)
        self._system_field_cache: dict[str, int] = {}
        # Cache for linked list primary field ID: linkedListId → primary_field_id
        self._linked_primary_cache: dict[str, int] = {}
        # Cache for LINK field → linked list ID: "{list_name}::{field_name}" → linkedListId
        self._linked_list_id_cache: dict[str, str] = {}

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _all_list_specs(self, spec: dict) -> list[tuple[dict, str | None]]:
        """
        Return a flat list of (list_spec, folder_name) tuples in creation order.
        Top-level lists come first (folder_name=None), then folder lists in order.
        """
        result = [(ls, None) for ls in spec.get("lists", [])]
        for folder_spec in spec.get("folders", []):
            for ls in folder_spec.get("lists", []):
                result.append((ls, folder_spec["name"]))
        return result

    def build(self, spec: dict) -> AppState:
        print(f"\n{'═'*60}")
        print(f"  Building: {spec['name']}")
        print(f"{'═'*60}")

        # Phase 1: App
        app_id = self._ensure_app(spec)

        # Phase 1.5: Folders (must exist before lists are assigned to them)
        for i, folder_spec in enumerate(spec.get("folders", [])):
            self._ensure_folder(app_id, folder_spec, order=i)

        # Phase 2: All lists (must exist before any LINK fields are created)
        for list_spec, folder_name in self._all_list_specs(spec):
            folder_id = self.state.get_folder_id(folder_name) if folder_name else None
            self._ensure_list(app_id, list_spec, folder_id=folder_id)

        # Phase 2.5: Customize the system Status field on Process/Task lists.
        # Spec key: "status_options" = ["Draft", "Pending", ...] OR
        # [{"label":"Draft","color":"#8ed6ff","closed":False}, ...].
        # Plus optional "default_status" (must match a label).
        for list_spec, _ in self._all_list_specs(spec):
            if "status_options" in list_spec:
                self._customize_status_field(list_spec)

        # Phase 3: Fields — fetch live field map ONCE per list, then three passes
        for list_spec, _ in self._all_list_specs(spec):
            list_name = list_spec["name"]
            list_id = self.state.get_list_id(list_name)
            self._sync_fields_to_state(list_name, list_id)  # one API call per list
            # Pass A: scalar fields (everything except LINK and LOOKUP)
            for field_spec in list_spec.get("fields", []):
                ftype = field_spec.get("type")
                if ftype != F.LINK and ftype != F.LOOKUP:
                    self._ensure_field(list_name, list_id, field_spec)
            # Pass B: LINK fields (targets now guaranteed to exist)
            for field_spec in list_spec.get("fields", []):
                if field_spec.get("type") == F.LINK:
                    self._ensure_field(list_name, list_id, field_spec)

        # Phase 3.5: LOOKUP fields — must run AFTER all LINK fields exist on
        # every list so the target field on the linked list is in the cache.
        for list_spec, _ in self._all_list_specs(spec):
            list_name = list_spec["name"]
            list_id   = self.state.get_list_id(list_name)
            # Re-sync so newly created LINK fields are in the cache
            self._sync_fields_to_state(list_name, list_id)
            for field_spec in list_spec.get("fields", []):
                if field_spec.get("type") == F.LOOKUP:
                    self._ensure_field(list_name, list_id, field_spec)

        # Phase 4: Views — re-sync field cache first (new lists were empty during Phase 3)
        for list_spec, _ in self._all_list_specs(spec):
            list_name = list_spec["name"]
            list_id   = self.state.get_list_id(list_name)
            self._sync_fields_to_state(list_name, list_id)
            for view_spec in list_spec.get("views", []):
                self._ensure_view(list_name, list_id, view_spec)

        # Phase 4.5: Configure column visibility for all GRID views
        for list_spec, _ in self._all_list_specs(spec):
            list_name = list_spec["name"]
            list_id   = self.state.get_list_id(list_name)
            self._sync_fields_to_state(list_name, list_id)
            for view_spec in list_spec.get("views", []):
                if view_spec.get("type") == 0:  # V.GRID
                    view_id = self.state.get_view_id(list_name, view_spec["name"])
                    if view_id:
                        self._configure_grid_columns(list_name, list_id, view_id,
                                                     view_spec["name"], view_spec)

        # Phase 5: Forms
        for list_spec, _ in self._all_list_specs(spec):
            list_id = self.state.get_list_id(list_spec["name"])
            for form_spec in list_spec.get("forms", []):
                self._ensure_form(app_id, list_spec["name"], list_id, form_spec)

        # Phase 5.5: Record Layouts
        for list_spec, _ in self._all_list_specs(spec):
            if "layout" not in list_spec:
                continue
            list_name = list_spec["name"]
            list_id   = self.state.get_list_id(list_name)
            layouts = list_spec["layout"]
            if isinstance(layouts, dict):
                layouts = [layouts]
            for layout_spec in layouts:
                self._ensure_layout(list_name, list_id, layout_spec)

        # Phase 5.6: Layout settings — per-field validation + required-when logic.
        # Compiles `validation` / `required_when` keys on each field spec into
        # LayoutSetting records (must run after layouts so we have layout IDs).
        self._apply_layout_settings(spec)

        # Phase 6: Automations
        automations = spec.get("automations", [])
        if automations:
            from workiom.automation_builder import AutomationBuilder
            print(f"\n  ⚡ Automations ({len(automations)} defined):")
            ab = AutomationBuilder(self.client, self.state)
            ab.build_all(app_id, automations)

        # Phase 7: Reports
        reports = spec.get("reports", [])
        if reports:
            print(f"\n  📊 Reports ({len(reports)} defined):")
            for report_spec in reports:
                self._ensure_report(app_id, report_spec)

        print(f"\n  ✅  Build complete: {spec['name']}\n")
        return self.state

    # ─── App ──────────────────────────────────────────────────────────────────

    def _validate_state(self):
        """
        If state has an app_id, verify it still exists in the live API.
        If it's gone (deleted externally), wipe the state so we rebuild fresh.
        """
        if not self.state.app_id:
            return
        apps = self.client.get_all_apps()
        live_ids = {a["id"] for a in apps}
        if self.state.app_id not in live_ids:
            print(f"  ⚠️  State has stale app ID — app was deleted externally. Resetting state.")
            self.state.wipe()
            # Re-init state (wipe removes the file; re-create blank)
            self.state._data = {
                "app_name": self.state.app_name,
                "app_id": None,
                "folders": {},
                "lists": {},
                "automations": {},
                "reports": {},
            }

    def _ensure_app(self, spec: dict) -> str:
        name = spec["name"]

        # Validate state against live API first
        self._validate_state()

        # Check state
        if self.state.app_id:
            self._log("app", name, "exists (state)")
            # Still apply icon/color in case they changed
            self._apply_app_meta(self.state.app_id, spec)
            return self.state.app_id

        # Check live API
        apps = self.client.get_all_apps()
        for app in apps:
            if app["name"] == name:
                self._log("app", name, "exists (API)")
                self.state.app_id = app["id"]
                self._apply_app_meta(app["id"], spec)
                return app["id"]

        # Create
        result = self.client.create_app(
            name=name,
            description=spec.get("description", ""),
            icon=spec.get("icon", ""),
            color=spec.get("color", ""),
        )
        self.state.app_id = result["id"]
        self._log("app", name, "created", result["id"])
        return result["id"]

    def _apply_app_meta(self, app_id: str, spec: dict):
        """Update icon/color on an existing app if spec provides them."""
        if spec.get("icon") or spec.get("color"):
            try:
                self.client.update_app(
                    app_id=app_id,
                    name=spec["name"],
                    description=spec.get("description", ""),
                    icon=spec.get("icon", ""),
                    color=spec.get("color", ""),
                )
            except WorkiomAPIError:
                pass  # Non-fatal

    # ─── Folder ───────────────────────────────────────────────────────────────

    def _ensure_folder(self, app_id: str, folder_spec: dict, order: int = 0) -> str | None:
        name = folder_spec["name"]

        # State-only idempotency (Folders/GetAll is not accessible via X-Api-Key)
        if self.state.get_folder_id(name):
            self._log("folder", name, "exists (state)")
            return self.state.get_folder_id(name)

        try:
            result = self.client.create_folder(app_id=app_id, name=name, order=order)
        except WorkiomAPIError as e:
            if "not available in your current plan" in str(e):
                self._log("folder", name, "skipped (plan does not support folders)")
                return None
            raise
        self.state.set_folder_id(name, result["id"])
        self._log("folder", name, "created", result["id"])
        return result["id"]

    # ─── List ─────────────────────────────────────────────────────────────────

    def _ensure_list(self, app_id: str, list_spec: dict,
                     folder_id: str | None = None) -> str:
        name = list_spec["name"]

        # Check state
        if self.state.get_list_id(name):
            self._log("list", name, "exists (state)")
            return self.state.get_list_id(name)

        # Check live API
        live_lists = self.client.get_all_lists(app_id)
        for lst in live_lists:
            if lst["name"] == name:
                self._log("list", name, "exists (API)")
                self.state.set_list_id(name, lst["id"])
                return lst["id"]

        # Create
        result = self.client.create_list(
            app_id=app_id,
            name=name,
            icon=list_spec.get("icon", "far fa-stream"),
            folder_id=folder_id,
            list_type=list_spec.get("list_type", 0),
        )
        self.state.set_list_id(name, result["id"])
        self._log("list", name, "created", result["id"])
        if list_spec.get("primary"):
            try:
                pf = next(f for f in self.client.get_all_fields(result["id"]) if f.get("isPrimary"))
                pf["name"] = list_spec["primary"]
                pf["isRequired"] = False   # zorunluluk formlarda; otomasyonlar kayıt açabilsin
                self.client.update_field(result["id"], pf["id"], pf)
                self._log("field", list_spec["primary"], "primary renamed")
            except (StopIteration, WorkiomAPIError) as e:
                print(f"    ⚠️  Primary rename failed on '{name}': {e}")
        return result["id"]

    # ─── Customize system Status on Process/Task lists ────────────────────────

    def _customize_status_field(self, list_spec: dict) -> None:
        """
        Replace the auto-generated Status options on a Process (type=2) or
        Task (type=1) list with the labels/colors from the spec.

        Spec accepts either:
            "status_options": ["Draft", "Pending", "Done"]
        Or:
            "status_options": [
                {"label": "Draft",   "color": "#8ed6ff", "closed": False},
                {"label": "Pending", "color": "#f5c044", "closed": False},
                {"label": "Done",    "color": "#5bd77e", "closed": True},
            ]
        Plus optional "default_status": "Draft" (must match a label;
        defaults to first label).
        """
        list_name = list_spec["name"]
        list_id = self.state.get_list_id(list_name)
        if not list_id:
            return

        opts = list_spec["status_options"]
        if not opts:
            return
        default_label = list_spec.get("default_status") or (
            opts[0] if isinstance(opts[0], str) else opts[0].get("label")
        )

        # Find the system Status field (dataType=16)
        try:
            fields = self.client.get_all_fields(list_id)
        except WorkiomAPIError as e:
            print(f"    ⚠️  Cannot fetch fields for '{list_name}': {e.message}")
            return
        status_field = next(
            (f for f in fields if f.get("dataType") == F.STATUS),
            None,
        )
        if not status_field:
            print(f"    ⚠️  No system Status field on '{list_name}' "
                  f"(is list_type 1 or 2?) — status_options ignored")
            return

        # Skip if labels already match (idempotency)
        existing_labels = [o.get("label") for o in status_field.get("staticListValues", [])]
        spec_labels = [
            opt if isinstance(opt, str) else opt.get("label") for opt in opts
        ]
        if existing_labels == spec_labels and status_field.get("defaultValue") == default_label:
            self._log("status", list_name, "exists (already customized)")
            return

        new_static = []
        for i, opt in enumerate(opts):
            if isinstance(opt, str):
                label, color, closed = opt, color_for(i), False
            else:
                label = opt["label"]
                color = opt.get("color", color_for(i))
                closed = opt.get("closed", False)
            new_static.append({
                "id": str(_uuid.uuid4()),
                "label": label,
                "color": color,
                "order": i,
                "isClosed": closed,
            })

        body = {**status_field, "staticListValues": new_static, "defaultValue": default_label}
        try:
            self.client.update_field(list_id, status_field["id"], body)
            self._log("status", list_name, f"customized ({len(new_static)} options)")
        except WorkiomAPIError as e:
            print(f"    ⚠️  Status update for '{list_name}' failed: {e.message}")

    # ─── Field ────────────────────────────────────────────────────────────────

    def _sync_fields_to_state(self, list_name: str, list_id: str):
        """
        Fetch all live fields for a list in ONE API call and cache in state.
        Also populates _option_cache and _field_type_cache for filter resolution.
        Called once per list before processing any fields.
        """
        try:
            live_fields = self.client.get_all_fields(list_id)
            for f in live_fields:
                fname = f["name"]
                if not self.state.get_field_id(list_name, fname):
                    self.state.set_field_id(list_name, fname, f["id"])
                # Cache field type, system status, and linked list ID for LINK fields
                cache_key = f"{list_name}::{fname}"
                self._field_type_cache[cache_key] = f.get("dataType", -1)
                self._system_field_cache[cache_key] = f.get("systemFieldType", 0)
                if f.get("dataType") == F.LINK and f.get("linkedListId"):
                    self._linked_list_id_cache[cache_key] = f["linkedListId"]
                # Register system Status field under the canonical "Status" alias
                # regardless of its localized display name (e.g. "Durum" in Turkish)
                if f.get("dataType") == F.STATUS and not self.state.get_field_id(list_name, "Status"):
                    self.state.set_field_id(list_name, "Status", f["id"])
                # Cache option labels → UUIDs for SELECT/STATUS/MULTISELECT
                if f.get("dataType") in (F.SELECT, F.STATUS, F.MULTISELECT):
                    opts = {
                        opt["label"]: opt["id"]
                        for opt in f.get("staticListValues", [])
                        if "label" in opt and "id" in opt
                    }
                    self._option_cache[cache_key] = opts
        except WorkiomAPIError as e:
            print(f"    ⚠️  Could not sync fields for '{list_name}': {e.message}")

    def _resolve_linked_primary(self, linked_list_id: str) -> int | None:
        """Return the primary field ID of a linked list (cached)."""
        if linked_list_id in self._linked_primary_cache:
            return self._linked_primary_cache[linked_list_id]
        try:
            fields = self.client.get_all_fields(linked_list_id)
            primary = next((f["id"] for f in fields if f.get("isPrimary")), None)
            self._linked_primary_cache[linked_list_id] = primary
            return primary
        except WorkiomAPIError:
            return None

    def _ensure_field(self, list_name: str, list_id: str,
                      field_spec: dict) -> int | None:
        name = field_spec["name"]

        # State is pre-synced from API by _sync_fields_to_state — just check it
        if self.state.get_field_id(list_name, name):
            self._log("field", name, "exists (state)")
            return self.state.get_field_id(list_name, name)

        # Not found — create it
        body = self._build_field_payload(field_spec, list_id, list_name)
        if body is None:
            return None  # Skipped (e.g. unresolvable link)

        try:
            result = self.client.create_field(list_id, body)
            self.state.set_field_id(list_name, name, result["id"])
            self._log("field", name, "created", str(result["id"]))
            if field_spec.get("type") == F.LINK and field_spec.get("backlink"):
                self._rename_backlink(body["linkedListId"], result, field_spec["backlink"])
            return result["id"]
        except WorkiomAPIError as e:
            print(f"    ⚠️  Field '{name}' failed: {e.message}")
            return None

    def _rename_backlink(self, target_list_id: str, created: dict, new_name: str) -> None:
        """Rename the auto-created twin (back-link) on the target list."""
        twin_id = created.get("linkedFieldId")
        try:
            fields = self.client.get_all_fields(target_list_id)
            twin = next((f for f in fields if f["id"] == twin_id), None)
            if not twin:
                twin = next((f for f in fields if f.get("linkedFieldId") == created["id"]), None)
            if not twin:
                print(f"    ⚠️  Back-link twin for '{created.get('name')}' not found")
                return
            if twin["name"] != new_name:
                twin["name"] = new_name
                twin["allowMultiple"] = True
                self.client.update_field(target_list_id, twin["id"], twin)
            self._log("field", new_name, "back-link", str(twin["id"]))
        except WorkiomAPIError as e:
            print(f"    ⚠️  Back-link rename '{new_name}' failed: {e.message}")

    def _build_lookup_payload(self, field_spec: dict,
                              list_name: str | None) -> dict | None:
        """
        Compile a LOOKUP field spec to a Workiom Fields/Create payload.

        Spec:
            {"name": "Department Head", "type": F.LOOKUP,
             "via": "Department", "lookup_field": "Head"}

        Result (note the API's swapped naming):
            {
              "name": "Department Head",
              "dataType": <source field's dataType>,   # e.g. 6 for USER
              "linkedFieldId": <field id on the LINKED list — the projection source>,
              "isLookup": True,
              "lookupFieldId": <LINK field id on THIS list — the hop>,
              "isRequired": False
            }
        """
        name = field_spec["name"]
        via_name = field_spec.get("via")
        lookup_name = field_spec.get("lookup_field")
        if not (list_name and via_name and lookup_name):
            print(f"    ⚠️  Skipping LOOKUP '{name}': missing list_name/via/lookup_field")
            return None

        # 1. The LINK field id on THIS list
        link_field_id = self.state.get_field_id(list_name, via_name)
        if not link_field_id:
            print(f"    ⚠️  Skipping LOOKUP '{name}': "
                  f"LINK field '{via_name}' not yet in state on '{list_name}'")
            return None

        # 2. The target list's id (cached from _sync_fields_to_state)
        linked_list_id = self._linked_list_id_cache.get(f"{list_name}::{via_name}")
        if not linked_list_id:
            print(f"    ⚠️  Skipping LOOKUP '{name}': "
                  f"linked list for '{via_name}' not found in cache")
            return None

        # 3. Fetch the linked list's fields to find lookup_name's id + dataType
        try:
            linked_fields = self.client.get_all_fields(linked_list_id)
        except WorkiomAPIError as e:
            print(f"    ⚠️  Skipping LOOKUP '{name}': "
                  f"cannot fetch linked list fields: {e.message}")
            return None

        target = next((f for f in linked_fields if f.get("name") == lookup_name), None)
        if not target:
            print(f"    ⚠️  Skipping LOOKUP '{name}': "
                  f"field '{lookup_name}' not found on linked list")
            return None

        return {
            "name": name,
            "dataType": target.get("dataType"),
            "linkedFieldId": target["id"],     # field on the linked list (source)
            "isLookup": True,
            "lookupFieldId": link_field_id,    # LINK field on THIS list (hop)
            "isRequired": False,
            "isVisible": True,                  # default-visible (Workiom hides if null)
        }

    def _build_field_payload(self, field_spec: dict,
                              list_id: str,
                              list_name: str | None = None) -> dict | None:
        """Convert a spec field dict into a Workiom API payload."""
        dtype = field_spec["type"]

        # ── LOOKUP — projects a field from a linked list ──────────────────────
        # Spec: {"name": "Department Head", "type": F.LOOKUP, "via": "Department",
        #        "lookup_field": "Head"}
        #   via         = the LINK field on THIS list that points to the linked list
        #   lookup_field = the field on the linked list whose value to display
        if dtype == F.LOOKUP:
            return self._build_lookup_payload(field_spec, list_name)

        body: dict[str, Any] = {
            "name": field_spec["name"],
            "dataType": dtype,
            "isRequired": field_spec.get("required", False),
            "isVisible": field_spec.get("visible", True),
            "defaultValue": field_spec.get("default", None),
        }

        # Select / MultiSelect / Status — add staticListValues
        if dtype in (F.SELECT, F.MULTISELECT, F.STATUS):
            options = field_spec.get("options", [])
            custom_colors = field_spec.get("colors", [])
            static_list = []
            for i, opt in enumerate(options):
                if isinstance(opt, dict):
                    label = opt.get("label", str(opt))
                    color = opt.get("color", custom_colors[i] if i < len(custom_colors) else color_for(i))
                else:
                    label = opt
                    color = custom_colors[i] if i < len(custom_colors) else color_for(i)
                static_list.append({
                    "id": str(_uuid.uuid4()),  # must be proper UUID to avoid option ID corruption
                    "label": label,
                    "color": color,
                    "order": i,
                })
            body["staticListValues"] = static_list
            # Prevent Workiom from auto-assigning a default
            body["defaultValue"] = None
            body["isRequired"] = False  # Required select causes empty-record errors

        # TEXT field — enableFormatting: True for multiline
        elif dtype == F.TEXT and field_spec.get("multiline"):
            body["enableFormatting"] = True
            body["allowMultiple"] = True

        # LINK field — resolve target list
        elif dtype == F.LINK:
            target_list_name = field_spec.get("target_list")
            target_app_name = field_spec.get("target_app")

            if target_app_name:
                # Cross-app link
                try:
                    target_app_id = self.resolver.resolve_app(target_app_name)
                    target_list_id = self.resolver.resolve_list(
                        target_app_name, target_list_name
                    )
                except ResolutionError as e:
                    print(f"    ⚠️  Skipping LINK field '{field_spec['name']}': {e}")
                    return None
            else:
                # Same-app link — target list must already be in state
                target_app_id = self.state.app_id
                target_list_id = self.state.get_list_id(target_list_name)
                if not target_list_id:
                    print(f"    ⚠️  Skipping LINK '{field_spec['name']}': "
                          f"target list '{target_list_name}' not in state yet.")
                    return None

            body["linkedAppId"] = target_app_id
            body["linkedListId"] = target_list_id
            body["allowMultiple"] = field_spec.get("multiple", False)
            if field_spec.get("backlink"):
                body["isAssociation"] = True
                body["hasAssociatedLinkedField"] = True
            body["isRequired"] = False
            body["defaultValue"] = None

        return body

    # ─── View ─────────────────────────────────────────────────────────────────

    def _configure_grid_columns(self, list_name: str, list_id: str,
                                 view_id: int, view_name: str,
                                 view_spec: dict) -> None:
        """Make all list fields visible as columns in a GRID view via UpdateState."""
        field_display_states = []
        for fname, fid in self.state.get_all_fields(list_name).items():
            cache_key = f"{list_name}::{fname}"
            is_system = self._system_field_cache.get(cache_key, 0) != 0
            is_link   = self._field_type_cache.get(cache_key, -1) == F.LINK
            entry: dict = {"fieldId": fid}
            if is_link and not is_system:
                entry["displayState"] = True
                linked_list_id = self._linked_list_id_cache.get(cache_key)
                primary_fid = (self._resolve_linked_primary(linked_list_id)
                               if linked_list_id else None)
                entry["projectedFieldIds"] = [primary_fid] if primary_fid else []
            elif not is_system:
                entry["displayState"] = True
            field_display_states.append(entry)

        state_body = {
            "name": view_name,
            "viewType": 0,
            "filters": [],
            "filterCollectionOperator": 0,
            "groupingSorting": 0,
            "state": {
                "fieldDisplayStateObjects": field_display_states,
                "kanbanCardStateObjects": [],
            },
            "order": 0,
            "accessibility": view_spec.get("accessibility", 0),
            "roleIds": [],
            "sourceViewId": view_id,
            "conditionalColorFilters": [],
        }
        try:
            self.client.update_view_state(view_id, list_id, state_body)
            self._log("view", view_name, "columns configured")
        except WorkiomAPIError as e:
            print(f"    ⚠️  View '{view_name}' column config failed: {e.message}")

    def _ensure_view(self, list_name: str, list_id: str,
                     view_spec: dict) -> int | None:
        name = view_spec["name"]

        # Check state
        if self.state.get_view_id(list_name, name):
            self._log("view", name, "exists (state)")
            return self.state.get_view_id(list_name, name)

        # Check live API
        live_views = self.client.get_all_views(list_id)
        for v in live_views:
            if v["name"] == name:
                self._log("view", name, "exists (API)")
                self.state.set_view_id(list_name, name, v["id"])
                return v["id"]

        # Build payload
        body = self._build_view_payload(list_name, view_spec)
        if body is None:
            return None

        try:
            result = self.client.create_view(list_id, body)
            view_id = result["id"]
            self.state.set_view_id(list_name, name, view_id)
            self._log("view", name, "created", str(view_id))

            # Post-creation: apply filters via Views/Update
            if view_spec.get("filter"):
                filters = self._build_view_filter(list_name, view_spec["filter"])
                if filters:
                    update_body = {
                        "name": name,
                        "viewType": view_spec["type"],
                        "filters": filters,
                        "filterCollectionOperator": 0,
                        "groupingSorting": 0,
                        "order": 0,
                        "accessibility": view_spec.get("accessibility", 0),
                        "roleIds": [],
                        "conditionalColorFilters": [],
                    }
                    try:
                        self.client.update_view(view_id, list_id, update_body)
                        self._log("view", name, "filter applied")
                    except WorkiomAPIError as e:
                        print(f"    ⚠️  View '{name}' filter update failed: {e.message}")

            # Post-creation: set document state via Views/UpdateState
            if view_spec.get("type") == 6 and view_spec.get("template"):
                state = self._compile_document_template(list_name, view_spec["template"])
                # name_field: field used as the document title ("Choose document name")
                # Falls back to "Name" then to the first user field
                name_field = view_spec.get("name_field", "Name")
                name_fid = self.state.get_field_id(list_name, name_field)
                if not name_fid:
                    # fallback: first field in the list
                    all_fields = self.state.get_all_fields(list_name)
                    name_fid = next(iter(all_fields.values()), None) if all_fields else None
                state_body = {
                    "name": name,
                    "viewType": 6,
                    "filters": [],
                    "filterCollectionOperator": 0,
                    "fieldId": name_fid,
                    "groupingSorting": 0,
                    "state": state,
                    "order": 0,
                    "accessibility": view_spec.get("accessibility", 0),
                    "roleIds": [],
                    "sourceViewId": view_id,
                    "conditionalColorFilters": [],
                }
                try:
                    self.client.update_view_state(view_id, list_id, state_body)
                    self._log("view", name, "document state applied")
                except WorkiomAPIError as e:
                    print(f"    ⚠️  View '{name}' UpdateState failed: {e.message}")

            return view_id
        except WorkiomAPIError as e:
            print(f"    ⚠️  View '{name}' failed: {e.message}")
            return None

    def _build_view_payload(self, list_name: str,
                             view_spec: dict) -> dict | None:
        body: dict[str, Any] = {
            "name": view_spec["name"],
            "viewType": view_spec["type"],
            "accessibility": view_spec.get("accessibility", 0),
        }

        # group_by → resolve field ID for KANBAN
        if view_spec.get("group_by"):
            field_id = self.state.get_field_id(list_name, view_spec["group_by"])
            if not field_id:
                print(f"    ⚠️  View '{view_spec['name']}': "
                      f"group_by field '{view_spec['group_by']}' not found — skipping.")
                return None
            body["fieldId"] = field_id

        # date_field → for CALENDAR / TIMELINE
        if view_spec.get("date_field"):
            field_id = self.state.get_field_id(list_name, view_spec["date_field"])
            if field_id:
                body["fieldId"] = field_id

        return body

    def _build_view_filter(self, list_name: str, filter_spec: dict) -> list[dict] | None:
        """Build the filters array for a view update call."""
        field_id = self.state.get_field_id(list_name, filter_spec["field"])
        if not field_id:
            return None
        op    = filter_spec.get("op", "equals")
        label = filter_spec.get("value")   # None for is_blank / is_not_blank
        cache_key = f"{list_name}::{filter_spec['field']}"
        dtype = self._field_type_cache.get(cache_key, -1)
        if op in ("is_blank", "is_not_blank"):
            # No value needed; operator 4=is_blank, 5=is_not_blank
            value    = None
            operator = 4 if op == "is_blank" else 5
        elif dtype in (F.SELECT, F.STATUS, F.MULTISELECT):
            opts = self._option_cache.get(cache_key, {})
            labels = label if isinstance(label, list) else [label]
            uuids  = [{"label": l, "id": opts[l]} for l in labels if l in opts]
            if not uuids:
                missing = [l for l in labels if l not in opts]
                print(f"    ⚠️  View filter: option(s) {missing} not found in "
                      f"'{filter_spec['field']}' — skipping filter.")
                return None
            value    = uuids
            operator = 4 if op == "not_in" else 3  # 4=is-not-any-of, 3=is-any-of
        else:
            value    = label
            op_map   = {"not_equals": 2}
            operator = op_map.get(op, 0)  # default 0 = equals
        return [{
            "fieldId": field_id,
            "operator": operator,
            "value": value,
            "value2": None,
            "valueMappingType": None,
            "value2MappingType": None,
        }]

    def _compile_document_template(self, list_name: str,
                                    template: list[dict]) -> dict:
        """
        Compile a human-readable template spec into an EditorJS state dict.

        Block types:
          {"type": "paragraph", "text": "...", "align": "left"}
          {"type": "header",    "text": "...", "level": 2, "align": "center"}
          {"type": "field",     "name": "FieldName", "align": "left"}
        """
        blocks = []
        for i, block in enumerate(template):
            block_id = f"blk{i:04d}"
            btype    = block["type"]
            align    = block.get("align", "left")

            if btype == "paragraph":
                blocks.append({
                    "id":   block_id,
                    "type": "paragraph",
                    "data": {"text": block.get("text", "")},
                    "tunes": {"textAlignment": {"alignment": align}},
                })

            elif btype == "header":
                blocks.append({
                    "id":   block_id,
                    "type": "header",
                    "data": {"text": block.get("text", ""), "level": block.get("level", 2)},
                    "tunes": {"textAlignment": {"alignment": align}},
                })

            elif btype == "field":
                fname = block["name"]
                fid   = self.state.get_field_id(list_name, fname)
                if not fid:
                    print(f"    ⚠️  Document template: "
                          f"field '{fname}' not found in '{list_name}' — skipping")
                    continue
                cache_key = f"{list_name}::{fname}"
                dtype = self._field_type_cache.get(cache_key, 0)
                blocks.append({
                    "id":   block_id,
                    "type": f"df_{fid}",
                    "data": {
                        "isDynamicField": True,
                        "field": {"id": fid, "dataType": dtype},
                        "config": {"fileWidth": ""},
                    },
                    "tunes": {"textAlignment": {"alignment": align}},
                })

        # Build fieldDisplayStateObjects for every field in this list.
        # User fields (non-LINK, systemFieldType=0): {"fieldId", "displayState": True}
        # LINK fields: {"fieldId", "displayState": True, "projectedFieldIds": [primary_id]}
        #   Must include projectedFieldIds pointing to the linked list's primary field.
        #   Without it, the browser sends projectedFields:[null] in Data/All, causing
        #   "Error converting null to System.Int64" errors.
        # System fields (systemFieldType>0): {"fieldId"} only — no displayState
        field_display_states = []
        for fname, fid in self.state.get_all_fields(list_name).items():
            cache_key = f"{list_name}::{fname}"
            is_system = self._system_field_cache.get(cache_key, 0) != 0
            is_link   = self._field_type_cache.get(cache_key, -1) == F.LINK
            entry: dict = {"fieldId": fid}
            if is_link and not is_system:
                entry["displayState"] = True
                linked_list_id = self._linked_list_id_cache.get(cache_key)
                primary_fid = self._resolve_linked_primary(linked_list_id) if linked_list_id else None
                entry["projectedFieldIds"] = [primary_fid] if primary_fid else []
            elif not is_system:
                entry["displayState"] = True
            field_display_states.append(entry)

        return {
            "documentCustomSize": {},
            "documentElements": {},
            "editorJsData": {
                "time":    int(_time.time() * 1000),
                "blocks":  blocks,
                "version": "2.29.1",
            },
            "fieldDisplayStateObjects": field_display_states,
            "kanbanCardStateObjects":   [],
        }

    # ─── Form ─────────────────────────────────────────────────────────────────

    def _ensure_form(self, app_id: str, list_name: str,
                     list_id: str, form_spec: dict) -> str | None:
        name = form_spec["name"]

        # Check state
        if self.state.get_form_id(list_name, name):
            self._log("form", name, "exists (state)")
            return self.state.get_form_id(list_name, name)

        # Check live API
        try:
            live_forms = self.client.get_all_forms(app_id)
        except WorkiomAPIError:
            live_forms = []

        for form in live_forms:
            if form.get("name") == name and form.get("listId") == list_id:
                self._log("form", name, "exists (API)")
                self.state.set_form_id(list_name, name, form["id"])
                return form["id"]

        # Build payload
        body = self._build_form_payload(list_id, list_name, form_spec)

        try:
            result = self.client.create_form(body)
            self.state.set_form_id(list_name, name, result["id"])
            self._log("form", name, "created", result["id"])
            return result["id"]
        except WorkiomAPIError as e:
            print(f"    ⚠️  Form '{name}' failed: {e.message}")
            return None

    def _build_form_payload(self, list_id: str, list_name: str,
                             form_spec: dict) -> dict:
        form_fields = []
        field_names = form_spec.get("fields", [])

        for order, fname in enumerate(field_names):
            field_id = self.state.get_field_id(list_name, fname)
            if not field_id:
                continue  # Skip fields not found in state
            form_fields.append({
                "fieldId":          field_id,
                "name":             fname,   # label shown on the form
                "isVisible":        True,
                "isRequired":       form_spec.get("required_fields", {}).get(fname, False),
                "order":            order,
                "placeholder":      form_spec.get("placeholders", {}).get(fname, ""),
                "description":      form_spec.get("descriptions", {}).get(fname, ""),
                "projectedFieldIds": [],     # must be empty array, not null
            })

        return {
            "listId": list_id,
            "name": form_spec["name"],
            "description": form_spec.get("description", ""),
            "color": form_spec.get("color", "#4e86f7"),
            "backgroundColor": form_spec.get("background_color", ""),
            "endMessage": form_spec.get("end_message",
                                        "Your submission has been received. Thank you!"),
            "isPrivate": form_spec.get("private", False),
            "formFields": form_fields,
        }

    # ─── Record Layouts ───────────────────────────────────────────────────────

    def _ensure_layout(self, list_name: str, list_id: str,
                       layout_spec: dict) -> str | None:
        name = layout_spec.get("name", "Default")

        existing_id = self.state.get_layout_id(list_name, name)
        if existing_id:
            self._log("layout", f"{list_name} / {name}", "already exists", existing_id)
            return existing_id

        body = self._build_layout_body(list_name, list_id, layout_spec)
        if body is None:
            return None

        try:
            result = self.client.create_layout(body)
            layout_id = result["id"]
            self.state.set_layout_id(list_name, name, layout_id)
            self._log("layout", f"{list_name} / {name}", "created", layout_id)
            return layout_id
        except WorkiomAPIError as e:
            print(f"  ✗ [layout    ] {list_name} / {name}: {e}")
            return None

    def _build_layout_body(self, list_name: str, list_id: str,
                           layout_spec: dict) -> dict | None:
        """Compile a layout spec into a RecordLayout API payload."""
        tabs_payload = []
        for tab_spec in layout_spec.get("tabs", []):
            col_count = tab_spec.get("columns", 1)
            # Bucket widgets by column number (1-indexed in spec)
            buckets: dict[int, list[dict]] = {i: [] for i in range(1, col_count + 1)}

            for group in tab_spec.get("groups", []):
                col = max(1, min(group.get("col", 1), col_count))
                widget: dict = {
                    "id":   str(_uuid.uuid4()),
                    "name": group.get("name", ""),
                    "type": 1 if group.get("type") == "activities" else 0,
                }
                if widget["type"] == 0:
                    field_ids = []
                    for fname in group.get("fields", []):
                        fid = self.state.get_field_id(list_name, fname)
                        if fid is not None:
                            field_ids.append(fid)
                        else:
                            print(f"    ⚠️  Layout field '{fname}' not found in {list_name}")
                    widget["fieldIds"] = field_ids
                buckets[col].append(widget)

            tabs_payload.append({
                "id":           str(_uuid.uuid4()),
                "name":         tab_spec.get("name", "Tab"),
                "columnsCount": col_count,
                "columns": [
                    {"id": str(_uuid.uuid4()), "widgets": buckets[c]}
                    for c in range(1, col_count + 1)
                ],
            })

        return {
            "name":            layout_spec.get("name", "Default"),
            "listId":          list_id,
            "isDefaultLayout": layout_spec.get("default", False),
            "tabs":            tabs_payload,
        }

    # ─── Layout Settings (validation + required-when) ─────────────────────────

    def _apply_layout_settings(self, spec: dict) -> None:
        """
        Compile each field spec's `validation` / `required_when` keys into
        LayoutSetting records, scoped to the list's default layout.

        Spec format:
            {"name": "Estimated Total", "type": F.CURRENCY,
             "validation": {"if": "{Estimated Total} > 0",
                            "message": "Must be > 0"},
             "required_when": "{Bid Type} = 'Sealed Bid'"}

        Multiple validations can be passed as a list; required_when can be
        a single condition string (one type-0 expression).
        """
        # Lazy import to avoid circulars
        from workiom.automation_builder import AutomationBuilder
        ab = AutomationBuilder(self.client, self.state)

        any_to_apply = any(
            f.get("validation") or f.get("required_when")
            for ls, _ in self._all_list_specs(spec)
            for f in ls.get("fields", [])
        )
        if not any_to_apply:
            return

        print(f"\n  🛡  Layout settings (validation + logic):")

        for list_spec, _ in self._all_list_specs(spec):
            list_name = list_spec["name"]
            list_id   = self.state.get_list_id(list_name)
            if not list_id:
                continue

            # Find the default record layout for this list
            layout_id = self._get_default_layout_id(list_name, list_id)
            if not layout_id:
                # Skip if no layout — rules are layout-scoped
                continue

            # Cache existing settings to keep idempotent
            try:
                existing = self.client.get_layout_settings(list_id)
            except WorkiomAPIError as e:
                print(f"    ⚠️  [{list_name}] cannot fetch settings: {e.message}")
                continue
            by_entity = {str(s["entityId"]): s for s in existing}

            # Pre-load field cache for compilation
            ab._load_cache(list_name)

            for fspec in list_spec.get("fields", []):
                fname = fspec.get("name")
                if not fname:
                    continue
                # LayoutSetting expressions use the SHORT field-ref form
                # `_F_{id}` (no `_A_00000000z...` suffix that automations use).
                # Compile via AutomationBuilder then strip the suffix.
                _A_SUFFIX = "_A_00000000z0000z0000z0000z000000000000"
                def _compile_for_layout(cond: str) -> str:
                    return ab._compile_condition(cond, list_name).replace(_A_SUFFIX, "")

                rules = []
                if fspec.get("validation"):
                    val = fspec["validation"]
                    items = val if isinstance(val, list) else [val]
                    for v in items:
                        cond = v.get("if") or v.get("expression")
                        msg  = v.get("message", "")
                        if not cond:
                            continue
                        rules.append({
                            "type": 1,
                            "expression": _compile_for_layout(cond),
                            "message": msg,
                        })
                if fspec.get("required_when"):
                    cond = fspec["required_when"]
                    rules.append({
                        "type": 0,
                        "expression": _compile_for_layout(cond),
                        "isRequired": True,
                    })
                if not rules:
                    continue

                fid = self.state.get_field_id(list_name, fname)
                if not fid:
                    continue

                payload = {
                    "entityType": 0,
                    "entityId": str(fid),
                    "recordLayoutId": layout_id,
                    "listId": list_id,
                    "layoutSettingExpressions": rules,
                }

                if str(fid) in by_entity:
                    payload["id"] = by_entity[str(fid)]["id"]
                    try:
                        self.client.update_layout_setting(payload)
                        print(f"    · {list_name}.{fname:<30s} updated ({len(rules)} rules)")
                    except WorkiomAPIError as e:
                        print(f"    ⚠️  {list_name}.{fname}: {e.message}")
                else:
                    try:
                        r = self.client.create_layout_setting(payload)
                        print(f"    ✅ {list_name}.{fname:<30s} created ({len(rules)} rules)")
                    except WorkiomAPIError as e:
                        print(f"    ⚠️  {list_name}.{fname}: {e.message}")

    def _get_default_layout_id(self, list_name: str, list_id: str) -> str | None:
        """Return the default RecordLayout's UUID for a list (cached in state)."""
        layouts = self.state.data.get("lists", {}).get(list_name, {}).get("layouts", {})
        if layouts:
            # Prefer "Default" layout name; fall back to first
            return layouts.get("Default") or next(iter(layouts.values()), None)
        return None

    # ─── Reports ──────────────────────────────────────────────────────────────

    # Widget type string → (widgetType int, summaryMode int|None)
    _WIDGET_TYPE_MAP = {
        "kpi_count": (W.NUMBER, 0),
        "kpi":       (W.NUMBER, 1),
        "bar":       (W.BAR,    None),
        "pie":       (W.PIE,    None),
        "table":     (W.TABLE,  None),
    }

    # Aggregation string → fieldAggregationType int
    _AGG_MAP = {
        "count": AGG.COUNT,
        "sum":   AGG.SUM,
        "avg":   AGG.AVG,
        "min":   AGG.MIN,
        "max":   AGG.MAX,
    }

    # Date frequency string → groupingDateFrequency int
    _FREQ_MAP = {
        "day":     FREQ.DAY,
        "week":    FREQ.WEEK,
        "month":   FREQ.MONTH,
        "quarter": FREQ.QUARTER,
        "year":    FREQ.YEAR,
    }

    def _ensure_report(self, app_id: str, spec: dict) -> int | None:
        """Create a report (AppDashboard widget) if it doesn't already exist."""
        label = spec["label"]

        existing_id = self.state.get_report_id(label)
        if existing_id:
            self._log("report", label, "already exists", str(existing_id))
            return existing_id

        body = self._build_report_body(spec)
        if body is None:
            return None

        try:
            result = self.client.create_report(app_id, body)
            report_id = result["id"]
            self.state.set_report_id(label, report_id)
            self._log("report", label, "created", str(report_id))
            return report_id
        except WorkiomAPIError as e:
            print(f"  ✗ [report    ] {label}: {e}")
            return None

    def _build_report_body(self, spec: dict) -> dict | None:
        """Compile a report spec dict into an AppDashboard API payload."""
        label      = spec["label"]
        list_name  = spec["list"]
        list_id    = self.state.get_list_id(list_name)
        if not list_id:
            print(f"  ✗ [report    ] {label}: list '{list_name}' not found in state")
            return None

        widget_type_str = spec.get("type", "bar")
        widget_type, summary_mode = self._WIDGET_TYPE_MAP.get(
            widget_type_str, (W.BAR, None))

        agg_str = spec.get("aggregation", "count")
        agg_type = self._AGG_MAP.get(agg_str, AGG.COUNT)

        # value_field: field to aggregate (None for pure record count)
        value_field_id = []
        if spec.get("value_field"):
            fid = self.state.get_field_id(list_name, spec["value_field"])
            if fid:
                value_field_id = [fid]

        # group_by field
        grouping_field_id = None
        if spec.get("group_by"):
            grouping_field_id = self.state.get_field_id(list_name, spec["group_by"])

        # sub_group_by field
        sub_grouping_field_id = None
        if spec.get("sub_group_by"):
            sub_grouping_field_id = self.state.get_field_id(
                list_name, spec["sub_group_by"])

        # Date frequencies
        freq_str = spec.get("group_date_freq", "month")
        grouping_date_freq = self._FREQ_MAP.get(freq_str, FREQ.MONTH)
        sub_freq_str = spec.get("sub_group_date_freq", freq_str)
        sub_grouping_date_freq = self._FREQ_MAP.get(sub_freq_str, FREQ.MONTH)

        # Filters (same format as view filters)
        filters = []
        if spec.get("filter"):
            built = self._build_view_filter(list_name, spec["filter"])
            if built:
                # Strip view-specific fields from filter objects
                filters = [{k: v for k, v in f.items()
                            if k not in ("viewId",)} for f in built]

        return {
            "label":                  label,
            "icon":                   spec.get("icon", "fal fa-chart-bar"),
            "listId":                 list_id,
            "viewId":                 spec.get("view_id", None),
            "filters":                filters,
            "filterCollectionOperator": 0,
            "widgetType":             widget_type,
            "fieldsIds":              [],
            "summaryMode":            summary_mode,
            "valueFieldId":           value_field_id,
            "fieldAggregationType":   agg_type,
            "groupingFieldId":        grouping_field_id,
            "groupingDateFrequency":  grouping_date_freq if grouping_field_id else None,
            "subGroupingFieldId":     sub_grouping_field_id,
            "subGroupingDateFrequency": sub_grouping_date_freq if sub_grouping_field_id else None,
            "isPin":                  spec.get("pin", True),
            "showTotalAsLabel":       spec.get("show_total_as_label", False),
            "sortingType":            spec.get("sorting", 0),
            "sortingType2":           0,
            "target":                 spec.get("target", None),
            "limit":                  spec.get("limit", 100),
            "limitSub":               spec.get("limit_sub", 100),
            "flipSides":              spec.get("flip_sides", False),
            "fileId":                 None,
            "xGroupOthers":           True,
            "yGroupOthers":           True,
            "showLabel":              spec.get("show_label", False),
            "wrappingNumbers":        spec.get("wrapping_numbers", False),
        }

    # ─── Logging ──────────────────────────────────────────────────────────────

    def _log(self, kind: str, name: str, action: str, id_: str = ""):
        icons = {"app": "📦", "folder": "📁", "list": "📋", "field": "🔤",
                 "view": "👁 ", "form": "📝", "automation": "⚡", "report": "📊",
                 "layout": "🗂 "}
        icon = icons.get(kind, "•")
        id_str = f" ({id_})" if id_ and "created" in action else ""
        status = "✅" if "created" in action else "·"
        print(f"  {status} {icon} [{kind:10s}] {name:<35s} {action}{id_str}")

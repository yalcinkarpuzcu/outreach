"""
WorkiomClient — low-level wrapper around the Workiom REST API.
All HTTP calls go through here. No business logic.
"""
from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Optional
from urllib.parse import urlencode

#BASE_URL = "https://api-tr.workiom.com"
BASE_URL = "https://api.workiom.com"
#BASE_URL = "https://yts-api.invest.gov.tr"

class WorkiomAPIError(Exception):
    def __init__(self, method: str, path: str, message: str, details: str = ""):
        self.method = method
        self.path = path
        self.message = message
        self.details = details
        super().__init__(f"{method} {path} → {message}" + (f" | {details}" if details else ""))


class WorkiomClient:
    MIN_REQUEST_INTERVAL = 1.0   # saniye — gerekirse 1.5-2.0'a çıkar

    def __init__(self, api_key: str, verbose: bool = False):
        self.api_key = api_key
        self.verbose = verbose
        self._last_request_time = 0.0

    def _request(self, method: str, path: str, body: Optional[dict] = None,
             params: Optional[dict] = None) -> Any:
        # ── Self-throttle: art arda isteklerin arasına minimum boşluk koy ──
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.monotonic()

        url = BASE_URL + path
        if params:
            url = url + "?" + urlencode(params)

        cmd = [
            "curl", "-s", "-X", method, url,
            "--connect-timeout", "10", "--max-time", "30",
            "-H", f"X-Api-Key: {self.api_key}",
            "-H", "Content-Type: application/json",
        ]
        if body is not None:
            cmd += ["-d", json.dumps(body)]

        if self.verbose:
            print(f"    → {method} {url}")

        result = None
        for attempt in range(3):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
                break
            except subprocess.TimeoutExpired:
                print(f"    ⚠️  Zaman aşımı (deneme {attempt+1}/3): {method} {path}")
                time.sleep(2 * (attempt + 1))

        if result is None:
            raise WorkiomAPIError(method, path, "3 denemede de cevap gelmedi (network donmuş olabilir)")

        if result.returncode != 0:
            raise WorkiomAPIError(method, path, f"curl çıkış kodu {result.returncode}",
                                result.stderr.strip()[:300])

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise WorkiomAPIError(method, path, "JSON olmayan cevap",
                                f"stdout={result.stdout[:200]!r} stderr={result.stderr[:200]!r}")

        if not data.get("success"):
            err = data.get("error") or {}
            raise WorkiomAPIError(method, path, err.get("message", "Bilinmeyen hata"),
                                err.get("details") or "")

        self._last_request_time = time.monotonic()
        return data["result"]

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict, params: Optional[dict] = None) -> Any:
        return self._request("POST", path, body=body, params=params)

    def put(self, path: str, body: dict, params: Optional[dict] = None) -> Any:
        return self._request("PUT", path, body=body, params=params)

    def delete(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("DELETE", path, params=params)

    # ─── Apps ─────────────────────────────────────────────────────────────────

    def get_all_apps(self) -> list[dict]:
        return self.get("/api/services/app/Apps/GetAll")["items"]

    def create_app(self, name: str, description: str = "", icon: str = "",
                   color: str = "") -> dict:
        body = {"name": name, "description": description}
        if icon:
            body["icon"] = icon
        if color:
            body["color"] = color
        return self.post("/api/services/app/Apps/Create", body)

    def update_app(self, app_id: str, name: str, description: str = "",
                   icon: str = "", color: str = "") -> dict:
        body = {"name": name, "description": description}
        if icon:
            body["icon"] = icon
        if color:
            body["color"] = color
        return self.put("/api/services/app/Apps/Update", body, {"id": app_id})

    def delete_app(self, app_id: str) -> Any:
        return self.delete("/api/services/app/Apps/Delete", {"id": app_id})

    # ─── Lists ────────────────────────────────────────────────────────────────

    def get_all_lists(self, app_id: str) -> list[dict]:
        return self.get("/api/services/app/Lists/GetAll",
                        {"appId": app_id})["items"]

    def create_list(self, app_id: str, name: str, icon: str = "far fa-stream",
                    folder_id: Optional[str] = None, list_type: int = 0) -> dict:
        """
        list_type:
          0 = Data list (default; watcher only)
          1 = Task list (auto status, dueDate, assignee, subTasks, parentTask)
          2 = Process list (auto title, status, assignee)
        """
        body = {"name": name, "appId": app_id, "type": list_type,
                "icon": icon, "isVisible": True}
        if folder_id:
            body["folderId"] = folder_id
        return self.post("/api/services/app/Lists/Create", body, {"appId": app_id})

    def delete_list(self, app_id: str, list_id: str) -> Any:
        return self.delete("/api/services/app/Lists/Delete",
                           {"appId": app_id, "Id": list_id})

    # ─── Folders ──────────────────────────────────────────────────────────────

    def create_folder(self, app_id: str, name: str, order: int = 0) -> dict:
        """
        Create a folder (group) in an app to organise lists.
        Returns: { id, name, order, listIds }
        Note: Folders/GetAll is not accessible via X-Api-Key (returns 302).
              Idempotency is handled via state tracking only.
        """
        return self.post("/api/services/app/Folders/Create",
                         {"name": name, "order": order},
                         {"appId": app_id})

    # ─── Fields ───────────────────────────────────────────────────────────────

    def get_all_fields(self, list_id: str) -> list[dict]:
        return self.get("/api/services/app/Fields/GetAll",
                        {"listId": list_id, "withSystemFields": "true"})["items"]

    def create_field(self, list_id: str, body: dict) -> dict:
        return self.post("/api/services/app/Fields/Create", body, {"listId": list_id})

    def update_field(self, list_id: str, field_id: int, body: dict) -> dict:
        return self.put("/api/services/app/Fields/Update", body,
                        {"listId": list_id, "id": field_id})

    def delete_field(self, list_id: str, field_id: int) -> Any:
        return self.delete("/api/services/app/Fields/Delete",
                           {"listId": list_id, "id": field_id})

    # ─── LayoutSetting (per-field validation + required-when logic) ───────────
    #
    # A LayoutSetting holds the validation/logic rule expressions for a single
    # field within a record layout. Schema:
    #   { id, entityType: 0 (field), entityId: "<field_id_str>",
    #     recordLayoutId: <layout_uuid>, listId: <list_uuid>,
    #     layoutSettingExpressions: [
    #       {type: 1, expression, message},            # validation
    #       {type: 0, expression, isRequired: True},   # required-when
    #     ] }

    def get_layout_settings(self, list_id: str) -> list[dict]:
        return self.get("/api/services/app/LayoutSetting/GetAll",
                        {"listId": list_id})["items"]

    def create_layout_setting(self, body: dict) -> dict:
        return self.post("/api/services/app/LayoutSetting/Create", body, {})

    def update_layout_setting(self, body: dict) -> dict:
        return self.put("/api/services/app/LayoutSetting/Update", body, {})

    def delete_layout_setting(self, layout_setting_id: int) -> Any:
        return self.delete("/api/services/app/LayoutSetting/Delete",
                           {"id": layout_setting_id})

    # ─── Views ────────────────────────────────────────────────────────────────

    def get_all_views(self, list_id: str) -> list[dict]:
        return self.get("/api/services/app/Views/GetAll",
                        {"listId": list_id})["items"]

    def create_view(self, list_id: str, body: dict) -> dict:
        return self.post("/api/services/app/Views/Create", body, {"listId": list_id})

    def update_view(self, view_id: int, list_id: str, body: dict) -> dict:
        return self.put("/api/services/app/Views/Update", body,
                        {"listId": list_id, "id": view_id})

    def update_view_state(self, view_id: int, list_id: str, body: dict) -> dict:
        return self.put("/api/services/app/Views/UpdateState", body,
                        {"listId": list_id, "id": view_id})

    def delete_view(self, view_id: int, list_id: str) -> Any:
        return self.delete("/api/services/app/Views/Delete",
                           {"id": view_id, "listId": list_id})

    # ─── Forms ────────────────────────────────────────────────────────────────

    def get_all_forms(self, app_id: str) -> list[dict]:
        """
        GetUserAppForms returns a dict keyed by listId, each value a list of forms.
        We flatten it into a single list.
        """
        result = self.get("/api/services/app/Forms/GetUserAppForms",
                          {"appId": app_id})
        forms = []
        if isinstance(result, dict):
            for form_list in result.values():
                if isinstance(form_list, list):
                    forms.extend(form_list)
        return forms

    def create_form(self, body: dict) -> dict:
        return self.post("/api/services/app/Forms/Create", body)

    def delete_form(self, form_id: str) -> Any:
        return self.delete("/api/services/app/Forms/Delete", {"formId": form_id})

    # ─── Automations ──────────────────────────────────────────────────────────

    def get_all_automations(self, app_id: str) -> list[dict]:
        return self.get("/api/services/app/Automation/GetAll",
                        {"appId": app_id})["items"]

    def create_automation(self, app_id: str, body: dict) -> dict:
        return self.post("/api/services/app/Automation/Create", body,
                         {"appId": app_id})

    def delete_automation(self, automation_id: int) -> Any:
        return self.delete("/api/services/app/Automation/Delete",
                           {"automationId": automation_id})

    # ─── Records ──────────────────────────────────────────────────────────────

    def get_records(self, list_id: str, skip: int = 0,
                    max_count: int = 500) -> dict:
        return self.post("/api/services/app/Data/All",
                         {"listId": list_id, "maxResultCount": max_count,
                          "skipCount": skip})

    def get_all_records(self, list_id: str) -> list[dict]:
        records, skip = [], 0
        while True:
            batch = self.get_records(list_id, skip)
            records.extend(batch["items"])
            if len(records) >= batch["totalCount"] or not batch["items"]:
                break
            skip += 500
        return records

    def create_record(self, list_id: str, payload: dict) -> str:
        """Returns the new record's _id string."""
        result = self.post("/api/services/app/Data/Create", payload,
                           {"listId": list_id})
        return result["_id"]

    def update_record(self, list_id: str, record_id: str, payload: dict) -> Any:
        return self.put("/api/services/app/Data/UpdatePartial", payload,
                        {"listId": list_id, "id": record_id})

    def delete_record(self, list_id: str, record_id: str) -> Any:
        return self.delete("/api/services/app/Data/Delete",
                           {"listId": list_id, "id": record_id})

    # ─── Record Layouts ───────────────────────────────────────────────────────

    def create_layout(self, body: dict) -> dict:
        return self.post("/api/services/app/RecordLayout/Create", body)

    def delete_layout(self, layout_id: str) -> Any:
        return self.delete("/api/services/app/RecordLayout/Delete", {"id": layout_id})

    # ─── Reports (AppDashboard) ───────────────────────────────────────────────

    def get_all_reports(self, app_id: str) -> list[dict]:
        return self.get("/api/services/app/AppDashboard/GetAll",
                        {"appId": app_id})["items"]

    def create_report(self, app_id: str, body: dict) -> dict:
        return self.post("/api/services/app/AppDashboard/Create", body,
                         {"appId": app_id})

    def update_report(self, app_id: str, report_id: int, body: dict) -> dict:
        return self.put("/api/services/app/AppDashboard/Update", body,
                        {"appId": app_id, "id": report_id})

    def delete_report(self, app_id: str, report_id: int) -> Any:
        return self.delete("/api/services/app/AppDashboard/Delete",
                           {"appId": app_id, "id": report_id})

    # ─── Users ────────────────────────────────────────────────────────────────

    def get_all_users(self) -> list[dict]:
        return self.get("/api/services/app/User/GetAll",
                        {"isActive": "true"})["items"]

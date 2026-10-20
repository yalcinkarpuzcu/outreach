"""
Per-app state management.
Each app spec gets its own state/<app_slug>.json file tracking all created IDs.

State structure:
{
  "app_name": "HR Suite",
  "app_id": "uuid",
  "folders": {
    "People & Organization": "folder-uuid",
    ...
  },
  "lists": {
    "Employees": {
      "id": "uuid",
      "fields": { "First Name": 1234567, "Last Name": 1234568, ... },
      "views":  { "All Employees": 999001, "By Department": 999002 },
      "forms":  { "New Employee Form": "uuid" }
    },
    ...
  },
  "automations": {
    "Notify on employee created": 580
  }
}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

STATE_DIR = Path("state")


def _slugify(name: str) -> str:
    import unicodedata
    # Normalize and lower
    name = name.lower()
    # Keep ASCII alphanumerics AND Unicode letters/digits (covers Arabic, etc.)
    # Replace everything else (spaces, punctuation) with underscore
    result = re.sub(r"[^\w]+", "_", name, flags=re.UNICODE).strip("_")
    # If the result is empty or only underscores, fall back to a hex hash
    if not result or result == "_":
        result = format(abs(hash(name)) % (16 ** 8), "08x")
    return result


def state_path(app_name: str) -> Path:
    return STATE_DIR / f"{_slugify(app_name)}.json"


class AppState:
    """
    Thin wrapper around a per-app state dict.
    Persisted to state/<slug>.json after every mutation.
    """

    def __init__(self, app_name: str):
        self.app_name = app_name
        self._path = state_path(app_name)
        self._data: dict = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if self._path.exists():
            data = json.loads(self._path.read_text())
            # Backward compat: add missing keys for older state files
            data.setdefault("folders", {})
            data.setdefault("reports", {})
            return data
        return {"app_name": self.app_name, "app_id": None,
                "folders": {}, "lists": {}, "automations": {}, "reports": {}}

    def save(self):
        STATE_DIR.mkdir(exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2))

    # ── App ───────────────────────────────────────────────────────────────────

    @property
    def app_id(self) -> str | None:
        return self._data.get("app_id")

    @app_id.setter
    def app_id(self, value: str):
        self._data["app_id"] = value
        self.save()

    # ── Folders ───────────────────────────────────────────────────────────────

    def get_folder_id(self, folder_name: str) -> str | None:
        return self._data["folders"].get(folder_name)

    def set_folder_id(self, folder_name: str, folder_id: str):
        self._data["folders"][folder_name] = folder_id
        self.save()

    # ── Lists ─────────────────────────────────────────────────────────────────

    def get_list_id(self, list_name: str) -> str | None:
        return self._data["lists"].get(list_name, {}).get("id")

    def set_list_id(self, list_name: str, list_id: str):
        self._data["lists"].setdefault(list_name, {
            "id": None, "fields": {}, "views": {}, "forms": {}, "layouts": {}
        })
        self._data["lists"][list_name]["id"] = list_id
        self.save()

    def get_list_names(self) -> list[str]:
        return list(self._data["lists"].keys())

    # ── Fields ────────────────────────────────────────────────────────────────

    def get_field_id(self, list_name: str, field_name: str) -> int | None:
        return self._data["lists"].get(list_name, {}).get("fields", {}).get(field_name)

    def set_field_id(self, list_name: str, field_name: str, field_id: int):
        self._data["lists"].setdefault(list_name, {
            "id": None, "fields": {}, "views": {}, "forms": {}
        })
        self._data["lists"][list_name]["fields"][field_name] = field_id
        self.save()

    def get_all_fields(self, list_name: str) -> dict[str, int]:
        return self._data["lists"].get(list_name, {}).get("fields", {})

    # ── Views ─────────────────────────────────────────────────────────────────

    def get_view_id(self, list_name: str, view_name: str) -> int | None:
        return self._data["lists"].get(list_name, {}).get("views", {}).get(view_name)

    def set_view_id(self, list_name: str, view_name: str, view_id: int):
        self._data["lists"][list_name]["views"][view_name] = view_id
        self.save()

    # ── Forms ─────────────────────────────────────────────────────────────────

    def get_form_id(self, list_name: str, form_name: str) -> str | None:
        return self._data["lists"].get(list_name, {}).get("forms", {}).get(form_name)

    def set_form_id(self, list_name: str, form_name: str, form_id: str):
        self._data["lists"][list_name].setdefault("forms", {})[form_name] = form_id
        self.save()

    # ── Automations ───────────────────────────────────────────────────────────

    def get_automation_id(self, name: str) -> int | None:
        return self._data.setdefault("automations", {}).get(name)

    def set_automation_id(self, name: str, automation_id: int):
        self._data.setdefault("automations", {})[name] = automation_id
        self.save()

    # ── Layouts ───────────────────────────────────────────────────────────────

    def get_layout_id(self, list_name: str, layout_name: str) -> str | None:
        return self._data["lists"].get(list_name, {}).get("layouts", {}).get(layout_name)

    def set_layout_id(self, list_name: str, layout_name: str, layout_id: str):
        self._data["lists"].setdefault(list_name, {
            "id": None, "fields": {}, "views": {}, "forms": {}, "layouts": {}
        })
        self._data["lists"][list_name].setdefault("layouts", {})[layout_name] = layout_id
        self.save()

    # ── Reports ───────────────────────────────────────────────────────────────

    def get_report_id(self, label: str) -> int | None:
        return self._data.setdefault("reports", {}).get(label)

    def set_report_id(self, label: str, report_id: int):
        self._data.setdefault("reports", {})[label] = report_id
        self.save()

    # ── Raw access (for teardown / introspection) ──────────────────────────────

    @property
    def data(self) -> dict:
        return self._data

    def exists(self) -> bool:
        return self._path.exists() and bool(self._data.get("app_id"))

    def wipe(self):
        """Remove the state file (call after successful teardown)."""
        if self._path.exists():
            self._path.unlink()

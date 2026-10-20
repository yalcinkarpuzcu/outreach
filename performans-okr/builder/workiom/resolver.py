"""
Resolver — finds list IDs for cross-app LINK fields.

Resolution order:
  1. State files in state/ directory (fast, no API call)
  2. Live API scan (slower, used as fallback)

Usage:
    resolver = Resolver(client)
    list_id = resolver.resolve(target_app="HR Core", target_list="Employees")
"""
from __future__ import annotations

import json
from pathlib import Path

from workiom.client import WorkiomClient
from workiom.state import STATE_DIR


class ResolutionError(Exception):
    pass


class Resolver:
    def __init__(self, client: WorkiomClient):
        self.client = client
        self._app_cache: dict[str, str] = {}   # app name → app_id
        self._list_cache: dict[str, str] = {}  # "AppName::ListName" → list_id

    def resolve_list(self, target_app: str, target_list: str) -> str:
        """
        Return the list UUID for a given app name + list name.
        Raises ResolutionError if not found.
        """
        cache_key = f"{target_app}::{target_list}"

        if cache_key in self._list_cache:
            return self._list_cache[cache_key]

        # 1. Try state files
        list_id = self._from_state_files(target_app, target_list)
        if list_id:
            self._list_cache[cache_key] = list_id
            return list_id

        # 2. Live API fallback
        list_id = self._from_api(target_app, target_list)
        if list_id:
            self._list_cache[cache_key] = list_id
            return list_id

        raise ResolutionError(
            f"Cannot resolve list '{target_list}' in app '{target_app}'. "
            f"Make sure that app is built first."
        )

    def resolve_app(self, target_app: str) -> str:
        """Return the app UUID for a given app name."""
        if target_app in self._app_cache:
            return self._app_cache[target_app]

        # Try state files first
        for state_file in STATE_DIR.glob("*.json"):
            try:
                data = json.loads(state_file.read_text())
                if data.get("app_name") == target_app and data.get("app_id"):
                    self._app_cache[target_app] = data["app_id"]
                    return data["app_id"]
            except (json.JSONDecodeError, KeyError):
                continue

        # Live API fallback
        apps = self.client.get_all_apps()
        for app in apps:
            if app["name"] == target_app:
                self._app_cache[target_app] = app["id"]
                return app["id"]

        raise ResolutionError(f"Cannot resolve app '{target_app}'.")

    # ── Private ───────────────────────────────────────────────────────────────

    def _from_state_files(self, target_app: str, target_list: str) -> str | None:
        """Scan all state JSON files for a matching app+list combo."""
        if not STATE_DIR.exists():
            return None

        for state_file in STATE_DIR.glob("*.json"):
            try:
                data = json.loads(state_file.read_text())
                if data.get("app_name") == target_app:
                    return data.get("lists", {}).get(target_list, {}).get("id")
            except (json.JSONDecodeError, KeyError):
                continue
        return None

    def _from_api(self, target_app: str, target_list: str) -> str | None:
        """Scan live API for app+list."""
        try:
            apps = self.client.get_all_apps()
            for app in apps:
                if app["name"] == target_app:
                    lists = self.client.get_all_lists(app["id"])
                    for lst in lists:
                        if lst["name"] == target_list:
                            return lst["id"]
        except Exception:
            pass
        return None

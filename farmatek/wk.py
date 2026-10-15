"""Ortak yardımcılar: workiom-builder client'ı + state + sık kullanılan çağrılar.

Kullanım:  API_KEY=... WORKIOM_BUILDER=<skill dizini> python farmatek/farmatek_ileri.py <faz>
"""
from __future__ import annotations

import glob
import json
import os
import sys
import uuid

BUILDER = os.environ.get("WORKIOM_BUILDER") or glob.glob(
    "/root/.claude/skills/synced/*/workiom-builder")[0]
sys.path.insert(0, BUILDER)

from workiom.client import WorkiomClient, WorkiomAPIError  # noqa: E402

APP_NAME = "Ar-Ge Proje Yönetimi"
STATE_PATH = os.path.join(BUILDER, "state", "ar_ge_proje_yönetimi.json")
API = "/api/services/app"

c = WorkiomClient(api_key=os.environ["API_KEY"])
c.MIN_REQUEST_INTERVAL = 0.35


def state() -> dict:
    return json.load(open(STATE_PATH))


APP_ID = state()["app_id"]


def list_id(name: str) -> str:
    return state()["lists"][name]["id"]


def fields(list_name: str) -> list[dict]:
    return c.get(f"{API}/Fields/GetAll", {"listId": list_id(list_name), "withSystemFields": "true"})["items"]


def fmap(list_name: str) -> dict[str, dict]:
    return {f["name"]: f for f in fields(list_name)}


def fid(list_name: str, field_name: str) -> int:
    return fmap(list_name)[field_name]["id"]


def opt(list_name: str, field_name: str, label: str) -> str:
    f = fmap(list_name)[field_name]
    return next(v["id"] for v in f["staticListValues"] if v["label"] == label)


def update_field(list_name: str, field: dict, **changes) -> dict:
    body = {**field, **changes}
    return c.put(f"{API}/Fields/Update", body, {"listId": list_id(list_name), "id": field["id"]})


def create_field(list_name: str, body: dict) -> dict:
    body = {"isRequired": False, "isVisible": True, **body}
    return c.post(f"{API}/Fields/Create", body, {"listId": list_id(list_name)})


def ensure_field(list_name: str, body: dict) -> int:
    ex = fmap(list_name).get(body["name"])
    if ex:
        print(f"  · {list_name}.{body['name']} mevcut ({ex['id']})")
        return ex["id"]
    r = create_field(list_name, body)
    print(f"  ✅ {list_name}.{body['name']} oluşturuldu ({r['id']})")
    return r["id"]


def views(list_name: str) -> list[dict]:
    return c.get(f"{API}/Views/GetAll", {"listId": list_id(list_name)})["items"]


def new_uuid() -> str:
    return str(uuid.uuid4())


def z(u: str) -> str:
    return u.replace("-", "z")


ZERO = "00000000-0000-0000-0000-000000000000"

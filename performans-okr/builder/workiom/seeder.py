"""
Seeder — populates a built app with sample/reference data defined in the spec.

Spec format for seed data:
    "seed": {
        "Departments": [
            {"Name": "Human Resources", "Department Code": "HR-001", "Status": "Active"},
            {"Name": "Finance",         "Department Code": "FIN-001", "Status": "Active"},
        ],
        "Leave Types": [
            {"Name": "Annual Leave", "Max Days Per Year": 21, "Paid": True},
        ],
    }

Values are keyed by field NAME (not ID). The seeder resolves field IDs from state.
LINK field values are specified by the record's primary field value (its name):
    {"Employee": "Ahmed Al-Rashid", "Leave Type": "Annual Leave"}
The seeder resolves these to record _ids automatically.
"""
from __future__ import annotations

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState


class Seeder:
    def __init__(self, client: WorkiomClient, state: AppState):
        self.client = client
        self.state = state
        self._record_cache: dict[str, dict[str, str]] = {}  # list_name → {primary_value: _id}
        # field_name → {"dataType": int, "linkedListId": str|None, "id": int}
        self._field_metadata_cache: dict[str, dict[str, dict]] = {}

    def seed(self, spec: dict):
        seed_data = spec.get("seed", {})
        if not seed_data:
            print("  ℹ️  No seed data defined in spec.")
            return

        print(f"\n{'═'*60}")
        print(f"  Seeding: {spec['name']}")
        print(f"{'═'*60}")

        # Build ordered list of all list names (top-level then folder lists)
        # This respects dependency order defined in the spec.
        list_order = [ls["name"] for ls in spec.get("lists", [])]
        for folder_spec in spec.get("folders", []):
            for ls in folder_spec.get("lists", []):
                list_order.append(ls["name"])

        for list_name in list_order:
            if list_name not in seed_data:
                continue
            rows = seed_data[list_name]
            self._seed_list(list_name, rows)

        print(f"\n  ✅  Seeding complete: {spec['name']}\n")

    def _seed_list(self, list_name: str, rows: list[dict]):
        list_id = self.state.get_list_id(list_name)
        if not list_id:
            print(f"  ⚠️  List '{list_name}' not in state — skipping seed.")
            return

        field_map = self.state.get_all_fields(list_name)  # name → id
        # Find primary field
        primary_field_id = self._get_primary_field_id(list_id)

        print(f"\n  📋  {list_name} ({len(rows)} rows)")

        # Load existing records to avoid duplicates (upsert by primary value)
        existing = self._get_existing_map(list_name, list_id, primary_field_id)

        for row in rows:
            primary_value = row.get("Name", "")
            payload = {}

            for field_name, value in row.items():
                # Primary field
                if field_name == "Name":
                    if primary_field_id:
                        payload[str(primary_field_id)] = value
                    continue

                field_id = field_map.get(field_name)
                if not field_id:
                    continue  # Unknown field — skip

                # Detect LINK field (value is a string name → resolve to _id)
                if isinstance(value, str) and self._is_link_field(list_name, field_name):
                    resolved = self._resolve_link(field_name, value)
                    if resolved:
                        payload[str(field_id)] = [{"_id": resolved}]
                    # If unresolvable, skip this field
                else:
                    payload[str(field_id)] = value

            if not payload:
                continue

            if primary_value and primary_value in existing:
                # Update existing
                try:
                    self.client.update_record(list_id, existing[primary_value], payload)
                    print(f"    ·  Updated: {primary_value}")
                except WorkiomAPIError as e:
                    print(f"    ⚠️  Update failed for '{primary_value}': {e.message}")
            else:
                # Create new
                try:
                    record_id = self.client.create_record(list_id, payload)
                    print(f"    ✅ Created: {primary_value or '(unnamed)'} → {record_id}")
                    # Cache for downstream LINK resolution
                    if primary_value:
                        self._record_cache.setdefault(list_name, {})[primary_value] = record_id
                        existing[primary_value] = record_id
                except WorkiomAPIError as e:
                    print(f"    ⚠️  Create failed for '{primary_value}': {e.message}")

    def _get_primary_field_id(self, list_id: str) -> int | None:
        try:
            fields = self.client.get_all_fields(list_id)
            for f in fields:
                if f.get("isPrimary") or f.get("isPrimaryRecordName"):
                    return f["id"]
        except WorkiomAPIError:
            pass
        return None

    def _get_existing_map(self, list_name: str,
                           list_id: str, primary_field_id: int | None) -> dict[str, str]:
        """Returns {primary_value: record_id} for existing records."""
        if list_name in self._record_cache:
            return self._record_cache[list_name]

        result = {}
        if not primary_field_id:
            return result

        try:
            records = self.client.get_all_records(list_id)
            for rec in records:
                val = rec.get(str(primary_field_id), "")
                if val:
                    result[str(val)] = rec["_id"]
        except WorkiomAPIError:
            pass

        self._record_cache[list_name] = result
        return result

    def _get_field_metadata(self, list_name: str) -> dict:
        if list_name in self._field_metadata_cache:
            return self._field_metadata_cache[list_name]
        list_id = self.state.get_list_id(list_name)
        if not list_id:
            return {}
        try:
            fields = self.client.get_all_fields(list_id)
            md = {
                f["name"]: {
                    "id": f.get("id"),
                    "dataType": f.get("dataType", -1),
                    "linkedListId": f.get("linkedListId"),
                }
                for f in fields
            }
            self._field_metadata_cache[list_name] = md
            return md
        except WorkiomAPIError:
            return {}

    def _is_link_field(self, list_name: str, field_name: str) -> bool:
        """Authoritative: check the field's dataType via API metadata; fall back
        to a heuristic if metadata is unavailable."""
        md = self._get_field_metadata(list_name).get(field_name)
        if md and md.get("dataType") == 5:   # F.LINK
            return True
        if md:
            return False
        # Fallback heuristic: field name matches a known list name
        known_lists = self.state.get_list_names()
        for lst in known_lists:
            if lst.rstrip("s") == field_name or lst == field_name or \
               field_name in lst or lst in field_name:
                return True
        return False

    def _resolve_link(self, field_name: str, value: str) -> str | None:
        """Find record _id by primary value in the most likely target list."""
        # Search all cached lists for a matching primary value
        for list_name, cache in self._record_cache.items():
            if value in cache:
                return cache[value]

        # Try loading from API for uncached lists
        for list_name in self.state.get_list_names():
            if list_name in self._record_cache:
                continue
            list_id = self.state.get_list_id(list_name)
            if not list_id:
                continue
            primary_id = self._get_primary_field_id(list_id)
            existing = self._get_existing_map(list_name, list_id, primary_id)
            if value in existing:
                return existing[value]

        return None

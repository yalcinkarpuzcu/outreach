"""
Teardown — deletes a Workiom app and all its contents, then wipes the state file.

Usage:
    teardown = Teardown(client, state)
    teardown.run(app_name="HR Core", confirm=True)
"""

from workiom.client import WorkiomClient, WorkiomAPIError
from workiom.state import AppState


class Teardown:
    def __init__(self, client: WorkiomClient, state: AppState):
        self.client = client
        self.state = state

    def run(self, dry_run: bool = False):
        app_name = self.state.app_name
        app_id = self.state.app_id

        if not app_id:
            # Try to find by name in live API
            apps = self.client.get_all_apps()
            for app in apps:
                if app["name"] == app_name:
                    app_id = app["id"]
                    break

        if not app_id:
            print(f"  ⚠️  App '{app_name}' not found in workspace. Nothing to delete.")
            self.state.wipe()
            return

        print(f"\n{'═'*60}")
        print(f"  Tearing down: {app_name} ({app_id})")
        print(f"{'═'*60}")

        if dry_run:
            print("  DRY RUN — no changes made.")
            return

        # Delete automations first
        try:
            automations = self.client.get_all_automations(app_id)
            for auto in automations:
                try:
                    self.client.delete_automation(auto["id"])
                    print(f"  🗑  Deleted automation: {auto.get('name', auto['id'])}")
                except WorkiomAPIError as e:
                    print(f"  ⚠️  Could not delete automation {auto['id']}: {e.message}")
        except WorkiomAPIError:
            pass

        # Delete forms
        try:
            forms = self.client.get_all_forms(app_id)
            for form in forms:
                try:
                    self.client.delete_form(form["id"])
                    print(f"  🗑  Deleted form: {form.get('name', form['id'])}")
                except WorkiomAPIError as e:
                    print(f"  ⚠️  Could not delete form {form['id']}: {e.message}")
        except WorkiomAPIError:
            pass

        # Delete the app (cascades to lists/fields/views/records)
        try:
            self.client.delete_app(app_id)
            print(f"  🗑  Deleted app: {app_name}")
        except WorkiomAPIError as e:
            print(f"  ⚠️  Could not delete app: {e.message}")
            return

        # Wipe state file
        self.state.wipe()
        print(f"  ✅  Teardown complete: {app_name}\n")

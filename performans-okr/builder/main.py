#!/usr/bin/env python3
from __future__ import annotations
"""
Workiom Builder CLI

Usage:
  python main.py build   apps/hr_core.py [apps/hr_leave.py ...]
  python main.py seed    apps/hr_core.py
  python main.py teardown apps/hr_core.py [--dry-run]
  python main.py status  [apps/hr_core.py]

Multi-tenant options (any command):
  --api-key  YOUR_KEY         Use this API key directly
  --profile  prod             Load .env.prod for API key

If neither --api-key nor --profile is given, loads API_KEY from .env
"""

import argparse
import importlib.util
import os
import sys
from pathlib import Path


def load_env(profile: str | None = None) -> str:
    """Load API key from .env or .env.<profile>."""
    env_file = f".env.{profile}" if profile else ".env"
    path = Path(env_file)

    api_key = ""
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if not api_key:
        api_key = os.environ.get("API_KEY", "")

    if not api_key:
        print(f"❌  No API key found. Add API_KEY=... to {env_file} or use --api-key.")
        sys.exit(1)

    return api_key


def load_spec(spec_path: str) -> dict:
    """Import a spec file and return its SPEC dict."""
    path = Path(spec_path)
    if not path.exists():
        print(f"❌  Spec file not found: {spec_path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("spec_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "SPEC"):
        print(f"❌  {spec_path} does not define a SPEC variable.")
        sys.exit(1)

    return module.SPEC


def get_client_and_state(api_key: str, spec: dict):
    """Instantiate WorkiomClient, AppState, and Resolver."""
    from workiom.client import WorkiomClient
    from workiom.state import AppState
    from workiom.resolver import Resolver

    client = WorkiomClient(api_key=api_key)
    state = AppState(app_name=spec["name"])
    resolver = Resolver(client)
    return client, state, resolver


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_build(args):
    from workiom.builder import Builder

    api_key = args.api_key or load_env(args.profile)

    for spec_path in args.specs:
        spec = load_spec(spec_path)
        client, state, resolver = get_client_and_state(api_key, spec)
        builder = Builder(client, state, resolver, verbose=args.verbose)
        builder.build(spec)


def cmd_seed(args):
    from workiom.seeder import Seeder

    api_key = args.api_key or load_env(args.profile)
    spec = load_spec(args.spec)
    client, state, _ = get_client_and_state(api_key, spec)

    if not state.exists():
        print(f"❌  No state found for '{spec['name']}'. Run 'build' first.")
        sys.exit(1)

    seeder = Seeder(client, state)
    seeder.seed(spec)


def cmd_teardown(args):
    from workiom.teardown import Teardown

    api_key = args.api_key or load_env(args.profile)
    spec = load_spec(args.spec)
    client, state, _ = get_client_and_state(api_key, spec)

    if not args.yes:
        answer = input(f"⚠️   Delete app '{spec['name']}' and all its data? [y/N]: ")
        if answer.lower() != "y":
            print("Aborted.")
            return

    teardown = Teardown(client, state)
    teardown.run(dry_run=args.dry_run)


def cmd_status(args):
    import json
    from workiom.state import STATE_DIR

    api_key = args.api_key or load_env(args.profile)

    if args.spec:
        # Status for a specific app
        spec = load_spec(args.spec)
        from workiom.state import AppState
        state = AppState(spec["name"])
        if state.exists():
            print(json.dumps(state.data, indent=2))
        else:
            print(f"  No state found for '{spec['name']}'.")
        return

    # Status for all tracked apps
    state_files = list(STATE_DIR.glob("*.json")) if STATE_DIR.exists() else []
    if not state_files:
        print("  No apps tracked yet.")
        return

    print(f"\n{'═'*50}")
    print(f"  Tracked apps ({len(state_files)})")
    print(f"{'═'*50}")
    for sf in sorted(state_files):
        try:
            data = json.loads(sf.read_text())
            name = data.get("app_name", "?")
            app_id = data.get("app_id", "?")
            n_lists = len(data.get("lists", {}))
            n_autos = len(data.get("automations", {}))
            print(f"  📦 {name:<30s} {n_lists} lists  {n_autos} automations")
            print(f"     ID: {app_id}")
        except Exception:
            print(f"  ⚠️  Corrupt state: {sf.name}")


# ─── CLI setup ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Workiom Builder — build Workiom apps from Python specs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument("--api-key",  metavar="KEY",     help="Workiom API key")
    parser.add_argument("--profile",  metavar="PROFILE", help="Load .env.<profile>")
    parser.add_argument("--verbose",  action="store_true", help="Show API requests")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = subparsers.add_parser("build", help="Build app(s) from spec file(s)")
    p_build.add_argument("specs", nargs="+", metavar="SPEC",
                         help="Path(s) to spec .py file(s)")
    p_build.set_defaults(func=cmd_build)

    # seed
    p_seed = subparsers.add_parser("seed", help="Populate an app with sample data")
    p_seed.add_argument("spec", metavar="SPEC", help="Path to spec .py file")
    p_seed.set_defaults(func=cmd_seed)

    # teardown
    p_tear = subparsers.add_parser("teardown", help="Delete an app from Workiom")
    p_tear.add_argument("spec", metavar="SPEC", help="Path to spec .py file")
    p_tear.add_argument("--dry-run", action="store_true",
                        help="Show what would be deleted without deleting")
    p_tear.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")
    p_tear.set_defaults(func=cmd_teardown)

    # status
    p_status = subparsers.add_parser("status", help="Show tracked app state")
    p_status.add_argument("spec", nargs="?", metavar="SPEC",
                          help="Specific spec (optional)")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

import argparse
import json
import sys
from orchestrator_core.planner import make_plan

from orchestrator_core.catalog.index import load_specs


def _list() -> None:
    """Print a table of available specs."""
    specs = load_specs()
    print("Name | Version | Entry-points")
    for name in sorted(specs):
        spec = specs[name]
        version = spec.get("version", "")
        entrypoints = spec.get("entrypoints", [])
        names = [ep.get("name", "") for ep in entrypoints if isinstance(ep, dict)]
        print(f"{name} | {version} | {', '.join(names)}")


def _show(name: str) -> None:
    """Print the full JSON spec for a given utility name."""
    specs = load_specs()
    if name not in specs:
        sys.exit(f"spec '{name}' not found")
    print(json.dumps(specs[name], indent=2))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser("orchestrator_core")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("name")
    # plan command to create execution plan from prompt
    plan_p = sub.add_parser("plan")
    plan_p.add_argument("prompt", nargs="+", help="Prompt text for planning")
    args = parser.parse_args(argv)
    if args.cmd == "list":
        _list()
    elif args.cmd == "show":
        _show(args.name)
    elif args.cmd == "plan":
        # build and display plan
        prompt = " ".join(args.prompt)
        plan = make_plan(prompt)
        print("Resolved Capabilities:")
        for cap in plan.get("resolved", []):
            print(f"  - {cap}")
        print("Missing Capabilities:")
        for cap in plan.get("missing", []):
            print(f"  - {cap}")
        # write plan.json to current directory
        try:
            with open("plan.json", "w") as f:
                json.dump(plan, f, indent=2)
        except Exception:
            pass
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

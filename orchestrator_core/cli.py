import argparse
import json
import sys

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
    args = parser.parse_args(argv)
    if args.cmd == "list":
        _list()
    elif args.cmd == "show":
        _show(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

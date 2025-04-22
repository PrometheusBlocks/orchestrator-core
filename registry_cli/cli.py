"""Registry CLI — publish/fetch utility specs from GitHub repos.

Usage:
    pb-registry publish path/to/utility_contract.json
    pb-registry fetch utility_name > spec.json
"""

import argparse
import json
import sys
from pathlib import Path

REGISTRY_DIR = Path.home() / ".pb_registry"
REGISTRY_DIR.mkdir(exist_ok=True)


def publish(spec_path: str):
    p = Path(spec_path)
    if not p.exists():
        sys.exit(f"spec file {spec_path} not found")
    spec = json.loads(p.read_text())
    target = REGISTRY_DIR / f"{spec['name']}-{spec['version']}.json"
    target.write_text(json.dumps(spec, indent=2))
    print(f"Published {target}")


def fetch(name: str):
    matches = sorted(REGISTRY_DIR.glob(f"{name}-*.json"), reverse=True)
    if not matches:
        sys.exit("spec not found")
    print(matches[0].read_text())


def main(argv=None):
    parser = argparse.ArgumentParser("pb-registry")
    sub = parser.add_subparsers(dest="cmd")

    pub = sub.add_parser("publish")
    pub.add_argument("spec_path")

    get = sub.add_parser("fetch")
    get.add_argument("name")

    args = parser.parse_args(argv)
    if args.cmd == "publish":
        publish(args.spec_path)
    elif args.cmd == "fetch":
        fetch(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

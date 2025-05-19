import argparse
import json
import sys
from pathlib import Path

from orchestrator_core.catalog.index import load_specs


def _load_params(source: str) -> dict:
    """Load parameters from a JSON string or file path."""
    path = Path(source)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as exc:  # pragma: no cover - file read errors
            sys.exit(f"Failed to read parameters file '{source}': {exc}")
    try:
        return json.loads(source)
    except json.JSONDecodeError as exc:
        sys.exit(f"Invalid JSON for parameters: {exc}")


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
    plan_p = sub.add_parser(
        "plan",
        help="Generate execution plan from a natural language prompt (LLM-based) and write plan.json to the current directory",
    )
    plan_p.add_argument("prompt", nargs="+", help="Prompt text for planning")
    # scaffold command to scaffold project based on plan.json
    scaffold_p = sub.add_parser(
        "scaffold",
        help="Scaffold project directories for utilities defined in plan.json",
    )
    scaffold_p.add_argument("project_name", help="Name of the project directory to create")
    scaffold_p.add_argument(
        "directory",
        help="Base directory where the project should be created",
    )

    execute_p = sub.add_parser(
        "execute",
        help="Execute a single utility entrypoint in a scaffolded project",
    )
    execute_p.add_argument("project", help="Path to project directory")
    execute_p.add_argument("--utility", required=True, help="Utility id to run")
    execute_p.add_argument(
        "--entrypoint", required=True, help="Entrypoint function name"
    )
    execute_p.add_argument(
        "--params_json",
        default="{}",
        help="JSON string or path to JSON file with parameters",
    )
    args = parser.parse_args(argv)
    if args.cmd == "list":
        _list()
    elif args.cmd == "show":
        _show(args.name)
    elif args.cmd == "plan":
        # build and display structured execution plan via LLM parser
        prompt = " ".join(args.prompt)
        from orchestrator_core.planner.parser import prompt_to_plan

        plan_steps = prompt_to_plan(prompt)
        # Print plan as JSON
        print(json.dumps(plan_steps, indent=2))
        # write plan.json to current directory
        try:
            with open("plan.json", "w") as f:
                json.dump(plan_steps, f, indent=2)
        except Exception as e:
            print(f"Warning: failed to write plan.json: {e}", file=sys.stderr)
    elif args.cmd == "scaffold":
        plan_file = Path("plan.json")
        if not plan_file.exists():
            sys.exit("plan.json not found in current directory")
        try:
            raw_plan = json.loads(plan_file.read_text())
        except Exception as e:
            sys.exit(f"Failed to load plan.json: {e}")
        proposed = []
        if isinstance(raw_plan, dict) and "proposed_utilities" in raw_plan:
            proposed = [u for u in raw_plan["proposed_utilities"] if isinstance(u, dict)]
        if not proposed:
            sys.exit("plan.json must contain 'proposed_utilities' with utility contracts")
        plan = {
            "resolved": [],
            "missing": [u.get("name") for u in proposed if u.get("name")],
            "proposed_utilities": proposed,
        }
        from orchestrator_core.executor.scaffolder import scaffold_project

        project_path = scaffold_project(
            plan,
            Path(args.directory),
            args.project_name,
            "https://github.com/PrometheusBlocks/block-template.git",
        )
        print(f"Scaffolded project created at: {project_path}")
    elif args.cmd == "execute":
        from orchestrator_core.executor.runner import execute_utility

        params = _load_params(args.params_json)
        result = execute_utility(
            Path(args.project), args.utility, args.entrypoint, params
        )
        print(
            json.dumps(
                {
                    "return": result.return_value,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                indent=2,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

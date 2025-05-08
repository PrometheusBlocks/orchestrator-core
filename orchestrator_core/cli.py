import argparse
import json
import sys
from pathlib import Path

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
    plan_p = sub.add_parser(
        "plan",
        help="Generate execution plan from a natural language prompt (LLM-based) and write plan.json to the current directory",
    )
    plan_p.add_argument("prompt", nargs="+", help="Prompt text for planning")
    # scaffold command to scaffold project based on plan.json
    scaffold_p = sub.add_parser(
        "scaffold",
        help="Scaffold project: clone resolved utilities and scaffold missing ones from plan.json",
    )
    scaffold_p.add_argument(
        "--plan", dest="plan", default="plan.json", help="Path to input plan.json file"
    )
    scaffold_p.add_argument(
        "--outdir",
        dest="outdir",
        default=".",
        help="Base directory to create the scaffolded project",
    )
    scaffold_p.add_argument(
        "--template-url",
        dest="template_url",
        default="https://github.com/PrometheusBlocks/block-template.git",
        help="Generic block template repository URL",
    )
    scaffold_p.add_argument(
        "project_name",
        help="Name of the project directory to create",
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
        # Scaffold project structure from a plan.json or execution plan list
        # Load raw plan file
        try:
            with open(args.plan) as f:
                raw_plan = json.load(f)
        except Exception as e:
            sys.exit(f"Failed to load plan file '{args.plan}': {e}")
        # If plan includes full proposed utilities specs, capture them for later
        proposed_contracts = {}
        if isinstance(raw_plan, dict) and "proposed_utilities" in raw_plan:
            for item in raw_plan.get("proposed_utilities", []):
                if isinstance(item, dict) and item.get("name"):
                    proposed_contracts[item["name"]] = item
        # Transform plan formats into scaffolding plan
        specs = load_specs()
        # 1) Execution plan list -> extract actions
        if isinstance(raw_plan, list):
            actions = [
                step.get("action")
                for step in raw_plan
                if isinstance(step, dict) and "action" in step
            ]
            resolved = [act for act in actions if act in specs]
            missing = [act for act in actions if act not in specs]
            plan = {"resolved": resolved, "missing": missing}
        # 2) Direct scaffolding plan dict
        elif isinstance(raw_plan, dict) and (
            "resolved" in raw_plan or "missing" in raw_plan
        ):
            plan = {
                "resolved": raw_plan.get("resolved", []),
                "missing": raw_plan.get("missing", []),
            }
        # 3) Legacy LLM layout with proposed_utilities
        elif isinstance(raw_plan, dict) and "proposed_utilities" in raw_plan:
            utilities = []
            for item in raw_plan.get("proposed_utilities", []):
                if isinstance(item, dict) and item.get("name"):
                    utilities.append(item["name"])
            resolved = [u for u in utilities if u in specs]
            missing = [u for u in utilities if u not in specs]
            plan = {"resolved": resolved, "missing": missing}
        else:
            # Error for unsupported plan format
            sys.exit(
                "Invalid plan format: must be:\n"
                "  - a list of execution-step dicts (with 'action'),\n"
                "  - a scaffolding plan dict (with 'resolved'/'missing'),\n"
                "  - or a dict with 'proposed_utilities' array."
            )
        # Run scaffolder
        from orchestrator_core.executor.scaffolder import scaffold_project

        project_path = scaffold_project(
            plan,
            Path(args.outdir),
            args.project_name,
            args.template_url,
        )
        # Overwrite placeholder contracts with full specs from proposed_utilities
        if proposed_contracts:
            for name, contract in proposed_contracts.items():
                util_dir = project_path / name
                contract_path = util_dir / "utility_contract.json"
                try:
                    with open(contract_path, "w") as f:
                        json.dump(contract, f, indent=2)
                    print(
                        f"Wrote proposed utility_contract.json for '{name}' from plan.json."
                    )
                except Exception as e:
                    print(
                        f"Warning: failed to write contract for '{name}': {e}",
                        file=sys.stderr,
                    )
        print(f"Scaffolded project created at: {project_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

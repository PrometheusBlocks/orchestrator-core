import argparse
import json
import sys
from pathlib import Path

from orchestrator_core.catalog.index import load_specs
from orchestrator_core.skills.core import (
    PlanningSkill,
    CodeGenerationSkill,
    SelfInspectionSkill,
)


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


def _self_improve(goal: str) -> None:
    """Improve the orchestrator's capabilities to achieve a goal."""
    print(f"\U0001F9E0 Planning self-improvement for: {goal}")

    try:
        planner = PlanningSkill()
        plan = planner.plan_self_improvement(goal)

        print(f"\U0001F4CB Generated plan with {len(plan)} steps:")
        for step in plan:
            print(f"  {step['step_id']}: {step['description']}")

        print("\n\u26A0\uFE0F SAFETY CHECK \u26A0\uFE0F")
        print("This will modify the orchestrator codebase.")
        print("Review the plan carefully:")
        for step in plan:
            action = step["action"]
            inputs = step.get("inputs", {})
            if action == "modify_existing":
                file_path = inputs.get("file_path", "unknown")
                print(f"  - Will modify: {file_path}")
            elif action == "generate_code":
                output_path = inputs.get("output_path", "unknown")
                print(f"  - Will create: {output_path}")
            elif action == "create_utility":
                name = inputs.get("name", "unknown")
                print(f"  - Will create utility: {name}")

        confirm = input("\nProceed with this plan? (y/N): ").strip().lower()
        if confirm != "y":
            print("Self-improvement cancelled.")
            return

        for step in plan:
            action = step["action"]
            description = step["description"]
            inputs = step.get("inputs", {})

            print(f"\n\U0001F527 Executing: {description}")

            if action == "generate_code":
                _execute_generate_code(inputs)
            elif action == "modify_existing":
                _execute_modify_existing(inputs)
            elif action == "create_utility":
                _execute_create_utility(inputs)
            elif action == "test_capability":
                _execute_test_capability(inputs)
            else:
                print(f"\u26A0\uFE0F  Unknown action: {action}")

        print("\n\U0001F389 Self-improvement complete!")

    except Exception as e:
        print(f"\u274C Self-improvement failed: {e}")


def _execute_generate_code(inputs: dict) -> None:
    """Execute code generation step."""
    try:
        code_gen = CodeGenerationSkill()

        description = inputs.get("description", "Generate code")
        function_name = inputs.get("function_name", "new_function")
        parameters = inputs.get("parameters", {})
        output_path = inputs.get("output_path", "generated_code.py")

        code = code_gen.generate_function(description, function_name, parameters)
        Path(output_path).write_text(code)
        print(f"\u2705 Generated code: {output_path}")

    except Exception as e:
        print(f"\u274C Code generation failed: {e}")


def _execute_modify_existing(inputs: dict) -> None:
    """Execute existing code modification step."""
    file_path = inputs.get("file_path", "")
    modification = inputs.get("modification", "")

    print("\u26A0\uFE0F  Manual modification needed:")
    print(f"   File: {file_path}")
    print(f"   Change: {modification}")
    print("   (Automatic modification not implemented yet)")


def _validate_generated_code(code: str, utility_name: str) -> bool:
    """Validate that generated code is functional and not just placeholders."""
    if not code or len(code.strip()) < 50:
        print(f"\u26A0\uFE0F  Generated code for {utility_name} is too short")
        return False

    placeholder_signs = [
        "TODO",
        "FIXME",
        "placeholder",
        "pass",
        "NotImplemented",
        "raise NotImplementedError",
        "# Implementation needed",
    ]

    code_lower = code.lower()
    placeholder_count = sum(1 for sign in placeholder_signs if sign.lower() in code_lower)
    if placeholder_count > 2:
        print(f"\u26A0\uFE0F  Generated code for {utility_name} appears to have too many placeholders")
        return False

    if "def " not in code:
        print(f"\u26A0\uFE0F  Generated code for {utility_name} doesn't contain function definitions")
        return False

    try:
        compile(code, f"{utility_name}.py", "exec")
        print(f"\u2705 Generated code for {utility_name} passes syntax validation")
        return True
    except SyntaxError as e:
        print(f"\u274C Generated code for {utility_name} has syntax errors: {e}")
        return False


def _execute_create_utility(inputs: dict) -> None:
    """Execute utility creation with real functional code using o4-mini."""
    try:
        name = inputs.get("name", "new_utility")
        description = inputs.get("description", "Generated utility")

        print(f"\U0001F916 Using o4-mini to generate functional code for {name}...")

        code_gen = CodeGenerationSkill()

        contract = code_gen.generate_utility_contract(name, description)
        print(f"\U0001F4CB Generated contract for {name}")

        print(f"\U0001F9E0 o4-mini reasoning through implementation...")
        implementation_code = code_gen.generate_complete_utility_implementation(name, description, contract)

        if not _validate_generated_code(implementation_code, name):
            print(f"\u26A0\uFE0F Code quality check failed for {name}. Proceeding anyway...")
            print("\U0001F4DD Preview of generated code:")
            print(implementation_code[:500] + "..." if len(implementation_code) > 500 else implementation_code)

        from orchestrator_core.executor.scaffolder import scaffold_project

        plan = {"resolved": [], "missing": [name], "proposed_utilities": [contract]}

        output_dir = Path("./generated_utilities")
        project_path = scaffold_project(
            plan,
            output_dir,
            name,
            "https://github.com/PrometheusBlocks/block-template.git",
        )

        print(f"\U0001F4DD Writing o4-mini generated code...")

        implementation_files = [
            project_path / name / f"{name}.py",
            project_path / name / "__init__.py",
            project_path / name / "main.py",
        ]

        code_written = False
        for impl_file in implementation_files:
            if impl_file.parent.exists():
                try:
                    impl_file.write_text(implementation_code, encoding="utf-8")
                    print(f"\u2705 Wrote implementation to: {impl_file}")
                    code_written = True
                    break
                except Exception as e:
                    print(f"\u26A0\uFE0F  Failed to write to {impl_file}: {e}")

        if not code_written:
            standalone_file = output_dir / f"{name}_implementation.py"
            standalone_file.write_text(implementation_code, encoding="utf-8")
            print(f"\u2705 Created standalone implementation: {standalone_file}")

        contract_file = project_path / name / "utility_contract.json"
        if contract_file.exists():
            import json
            with contract_file.open('w') as f:
                json.dump(contract, f, indent=2)
            print(f"\U0001F4C4 Updated contract: {contract_file}")

        print(f"\U0001F389 Created functional utility with o4-mini: {project_path}")
        print(f"\U0001F9EA Test the implementation:")
        print(f"   cd {project_path}/{name}")
        print(f"   python {name}.py")

    except Exception as e:
        print(f"\u274C o4-mini utility creation failed: {e}")
        import traceback
        traceback.print_exc()


def _execute_test_capability(inputs: dict) -> None:
    """Execute capability testing step."""
    capability = inputs.get("capability", "unknown")
    print(f"\U0001F9EA Testing capability: {capability}")
    print("   (Automatic testing not implemented yet)")


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

    improve_p = sub.add_parser(
        "improve",
        help="Improve the orchestrator's capabilities through self-modification",
    )
    improve_p.add_argument("goal", nargs="+", help="What capability to add or improve")

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
    elif args.cmd == "improve":
        goal = " ".join(args.goal)
        _self_improve(goal)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

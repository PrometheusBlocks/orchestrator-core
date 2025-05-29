import os
from pathlib import Path
from typing import Dict, Any
import json


class CodeGenerationSkill:
    """Generate Python code using LLM."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

    def generate_function(self, description: str, function_name: str, parameters: Dict[str, Any]) -> str:
        """Generate a Python function based on description.

        Args:
            description: What the function should do
            function_name: Name of the function to generate
            parameters: Dictionary of parameter names and types

        Returns:
            String containing the generated Python function
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            param_str = "\n".join([f"    {name}: {ptype}" for name, ptype in parameters.items()])

            prompt = f"""Generate a Python function with these specifications:
Function name: {function_name}
Description: {description}
Parameters:
{param_str}

Return only the function code, properly formatted with docstring.
Do not include imports unless absolutely necessary.
"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Return only clean, working code."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"# Error generating function: {str(e)}\ndef {function_name}(*args, **kwargs):\n    pass"

    def generate_utility_contract(self, name: str, description: str) -> Dict[str, Any]:
        """Generate a utility contract JSON.

        Args:
            name: Name of the utility
            description: What the utility does

        Returns:
            Dictionary representing a UtilityContract
        """
        return {
            "name": name,
            "version": "0.1.0-dev",
            "language": "python",
            "description": description,
            "size_budget": 200000,
            "entrypoints": [
                {
                    "name": "run",
                    "description": f"Main entrypoint for {name}",
                    "parameters_schema": {"type": "object", "properties": {}},
                    "return_schema": {"type": "object"},
                }
            ],
            "deps": [],
            "tests": [],
        }


class SelfInspectionSkill:
    """Inspect and analyze the orchestrator's own code."""

    def __init__(self) -> None:
        self.base_path = Path(__file__).parent.parent

    def read_own_source(self, module_path: str) -> str:
        """Read source code of orchestrator modules.

        Args:
            module_path: Relative path from orchestrator_core/ (e.g., "cli.py")

        Returns:
            String containing the source code
        """
        try:
            file_path = self.base_path / module_path
            if not file_path.exists():
                return f"# File not found: {module_path}"
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"# Error reading {module_path}: {str(e)}"

    def list_available_skills(self) -> list:
        """List all currently available skills/utilities.

        Returns:
            List of utility names
        """
        try:
            from orchestrator_core.catalog.index import load_specs

            specs = load_specs()
            return list(specs.keys())
        except Exception as e:
            print(f"Error loading skills: {e}")
            return []

    def analyze_skill_dependencies(self, skill_name: str) -> Dict[str, Any]:
        """Analyze what other skills a given skill depends on.

        Args:
            skill_name: Name of the skill to analyze

        Returns:
            Dictionary with dependency information
        """
        try:
            from orchestrator_core.catalog.index import load_specs

            specs = load_specs()

            if skill_name not in specs:
                return {"error": f"Skill '{skill_name}' not found"}

            spec = specs[skill_name]
            return {
                "name": skill_name,
                "dependencies": spec.get("deps", []),
                "entrypoints": spec.get("entrypoints", []),
                "version": spec.get("version", "unknown"),
            }
        except Exception as e:
            return {"error": str(e)}

    def list_source_files(self) -> list:
        """List all Python source files in the orchestrator.

        Returns:
            List of relative paths to .py files
        """
        try:
            py_files = []
            for file_path in self.base_path.rglob("*.py"):
                if "__pycache__" not in str(file_path):
                    relative_path = file_path.relative_to(self.base_path)
                    py_files.append(str(relative_path))
            return sorted(py_files)
        except Exception as e:
            print(f"Error listing files: {e}")
            return []


class PlanningSkill:
    """Enhanced planning that can break down complex self-improvement tasks."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")

    def plan_self_improvement(self, goal: str) -> list:
        """Create a plan for improving the orchestrator itself.

        Args:
            goal: What capability to add or improve

        Returns:
            List of plan steps (dictionaries)
        """
        inspector = SelfInspectionSkill()
        current_skills = inspector.list_available_skills()
        source_files = inspector.list_source_files()

        if not self.api_key:
            return [
                {
                    "step_id": 1,
                    "action": "create_utility",
                    "inputs": {"name": "new_capability", "description": goal},
                    "description": f"Create new capability: {goal}",
                }
            ]

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            prompt = f"""
Goal: {goal}

Current orchestrator capabilities: {current_skills}
Current source files: {source_files[:10]}

Create a JSON array of steps to achieve this goal. Each step should have:
- step_id: sequential number
- action: one of ["generate_code", "modify_existing", "create_utility", "test_capability"]
- inputs: dictionary with specific parameters for the action
- description: human-readable description

Focus on practical, implementable steps for a Python codebase.
Limit to 3-5 steps maximum.

Return only valid JSON array.
"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a software development planner. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            try:
                plan = json.loads(content)
                if isinstance(plan, list):
                    return plan
                return [plan]
            except json.JSONDecodeError:
                return [
                    {
                        "step_id": 1,
                        "action": "create_utility",
                        "inputs": {"name": "generated_capability", "description": goal},
                        "description": f"Generate capability for: {goal}",
                    }
                ]
        except Exception as e:
            print(f"Planning error: {e}")
            return [
                {
                    "step_id": 1,
                    "action": "create_utility",
                    "inputs": {"name": "fallback_capability", "description": goal},
                    "description": f"Fallback plan for: {goal}",
                }
            ]

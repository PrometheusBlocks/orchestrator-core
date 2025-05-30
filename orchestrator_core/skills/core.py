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
        """Generate a Python function based on description using o4-mini reasoning model.

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

            developer_instructions = """You are an expert Python developer. Generate complete, working Python functions.

# Instructions
* Generate production-ready Python code with proper error handling
* Include comprehensive docstrings with examples
* Add type hints for all parameters and return values
* Write actual functional code, not placeholders
* Include necessary imports within the function if needed
* Test edge cases and provide robust implementations

# Output Format
Return only the Python function code. No explanations or markdown formatting."""

            param_descriptions = []
            for name, ptype in parameters.items():
                param_descriptions.append(f"- {name}: {ptype}")

            user_input = f"""Generate a Python function with these specifications:

Function name: {function_name}
Purpose: {description}
Parameters:
{chr(10).join(param_descriptions)}

The function should be complete, tested, and ready for production use."""

            response = client.responses.create(
                model="o4-mini-2025-04-16",
                instructions=developer_instructions,
                input=user_input,
            )

            if hasattr(response, "output_text") and response.output_text:
                return response.output_text.strip()
            output_text = ""
            for item in getattr(response, "output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        output_text += content.get("text", "")
            return output_text.strip() if output_text else self._fallback_function(function_name, description)

        except Exception as e:
            print(f"o4-mini code generation failed: {e}")
            return self._fallback_function(function_name, description)

    def _fallback_function(self, function_name: str, description: str) -> str:
        """Fallback function when o4-mini is unavailable."""
        return f'''def {function_name}(*args, **kwargs):
    """
    {description}

    This is a fallback implementation. o4-mini generation failed.
    """
    print(f"Executing {function_name}: {description}")
    return {{"status": "fallback", "message": "o4-mini unavailable"}}'''

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

    def generate_complete_utility_implementation(self, name: str, description: str, contract: Dict[str, Any]) -> str:
        """Generate a complete Python implementation for a utility using o4-mini.

        Args:
            name: Name of the utility
            description: What the utility should do
            contract: The utility contract with entrypoints

        Returns:
            Complete Python module code as string
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            entrypoints = contract.get("entrypoints", [])
            entrypoint_specs = []
            for ep in entrypoints:
                ep_name = ep.get("name", "run")
                ep_desc = ep.get("description", "Main function")
                ep_params = ep.get("parameters_schema", {})
                ep_return = ep.get("return_schema", {})
                entrypoint_specs.append(
                    f"""
Function: {ep_name}
Description: {ep_desc}
Parameters Schema: {ep_params}
Return Schema: {ep_return}
"""
                )

            developer_instructions = """You are an expert Python developer creating production-ready utility modules.

# Identity
You specialize in creating complete, self-contained Python utilities that solve specific problems.

# Instructions
* Generate a complete Python module with all necessary imports
* Implement ALL required functions with full functionality, not placeholders
* Add comprehensive error handling and input validation
* Include detailed docstrings with usage examples
* Use type hints throughout
* Make functions robust and production-ready
* Add helper functions if needed to support main functionality
* Include a main block for testing if appropriate

# Output Format
Return only the complete Python module code. No markdown formatting or explanations."""

            user_input = f"""Create a complete Python utility module for '{name}'.

Overall Purpose: {description}

Required Functions:
{chr(10).join(entrypoint_specs)}

Generate a fully functional Python module that implements these requirements. The code should be ready to use immediately without any modifications."""

            response = client.responses.create(
                model="o4-mini-2025-04-16",
                instructions=developer_instructions,
                input=user_input,
            )

            if hasattr(response, "output_text") and response.output_text:
                generated_code = response.output_text.strip()
            else:
                output_text = ""
                for item in getattr(response, "output", []):
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            output_text += content.get("text", "")
                generated_code = output_text.strip()

            if not generated_code:
                return self._fallback_utility_implementation(name, description, entrypoints)

            return generated_code

        except Exception as e:
            print(f"o4-mini utility generation failed: {e}")
            return self._fallback_utility_implementation(name, description, contract.get("entrypoints", []))

    def _fallback_utility_implementation(self, name: str, description: str, entrypoints: list) -> str:
        """Generate fallback utility implementation."""
        functions = []
        for ep in entrypoints:
            ep_name = ep.get("name", "run")
            ep_desc = ep.get("description", "Main function")
            functions.append(
                f'''
def {ep_name}(*args, **kwargs):
    """
    {ep_desc}

    Fallback implementation for {name}.
    """
    print(f"Executing {ep_name} for {name}")
    return {{"status": "fallback", "description": "{description}"}}
'''
            )

        return f'''"""
{name} - {description}

This is a fallback implementation generated when o4-mini was unavailable.
"""

import json
from typing import Any, Dict

{chr(10).join(functions)}

if __name__ == "__main__":
    print("Utility '{name}' loaded successfully (fallback mode)")
'''


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
        """Create a detailed plan for improving the orchestrator using o4-mini reasoning.

        Args:
            goal: What capability to add or improve

        Returns:
            List of detailed plan steps (dictionaries)
        """
        inspector = SelfInspectionSkill()
        current_skills = inspector.list_available_skills()
        source_files = inspector.list_source_files()[:15]

        if not self.api_key:
            return self._fallback_plan(goal)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            developer_instructions = """You are an expert software architect specializing in self-improving AI systems.

# Identity  
You design detailed implementation plans for adding new capabilities to AI orchestration systems.

# Instructions
* Analyze the current system architecture thoroughly
* Create step-by-step plans with specific, actionable tasks
* Focus on generating working code, not just scaffolding
* Include implementation details and file modifications
* Plan for testing and integration
* Consider dependencies and potential conflicts
* Generate JSON format plans with specific action types

# Available Actions
- "generate_code": Create new Python functions or modules
- "modify_existing": Modify existing orchestrator files  
- "create_utility": Create complete working utilities
- "test_capability": Test newly created functionality
- "integrate_utility": Register new utilities in the system

# Output Format
Return a JSON array of steps. Each step must include:
- step_id: sequential number
- action: one of the available actions above
- inputs: specific parameters needed for the action
- description: clear explanation of what this step accomplishes
- rationale: why this step is necessary"""

            user_input = f"""Goal: {goal}

Current System State:
- Available utilities: {current_skills}
- Source files: {source_files}

Create a detailed implementation plan to achieve this goal. The plan should result in working, functional code being added to the orchestrator. Focus on practical implementation steps that will create real capabilities, not just project structure.

Limit the plan to 3-5 high-impact steps."""

            response = client.responses.create(
                model="o4-mini-2025-04-16",
                instructions=developer_instructions,
                input=user_input,
            )

            if hasattr(response, "output_text") and response.output_text:
                content = response.output_text.strip()
            else:
                content = ""
                for item in getattr(response, "output", []):
                    for chunk in item.get("content", []):
                        if chunk.get("type") == "output_text":
                            content += chunk.get("text", "")

            import re

            try:
                plan_data = json.loads(content)
                if isinstance(plan_data, list):
                    return plan_data
                else:
                    return [plan_data]
            except json.JSONDecodeError:
                json_match = re.search(r"\[[\s\S]*?\]", content)
                if json_match:
                    try:
                        plan_data = json.loads(json_match.group(0))
                        return plan_data if isinstance(plan_data, list) else [plan_data]
                    except json.JSONDecodeError:
                        pass
                return self._fallback_plan(goal)

        except Exception as e:
            print(f"o4-mini planning failed: {e}")
            return self._fallback_plan(goal)

    def _fallback_plan(self, goal: str) -> list:
        """Generate simple fallback plan when o4-mini is unavailable."""
        return [{
            "step_id": 1,
            "action": "create_utility",
            "inputs": {"name": "generated_capability", "description": goal},
            "description": f"Create working utility for: {goal}",
            "rationale": "Fallback plan due to o4-mini unavailability",
        }]

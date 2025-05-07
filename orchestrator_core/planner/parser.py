import os
import json
from pathlib import Path
import yaml


def prompt_to_capabilities(prompt: str, use_llm: bool = False) -> list[str]:
    """
    1) Load core keywords.yml and any *.yml in planner/packs
    2) Case-insensitive keyword match; return unique capability list.
    3) If use_llm is True OR env USE_LLM_PARSER=1:
         • Call OpenAI chat completion (gpt-4o-mini) with system prompt:
           "You are a capability extractor. Return a JSON array of capability IDs."
         • Merge LLM result with keyword result.
    """
    mapping: dict[str, list[str]] = {}
    base_dir = Path(__file__).parent
    # Load core keywords
    keywords_file = base_dir / "keywords.yml"
    try:
        core_data = yaml.safe_load(keywords_file.read_text())
        if isinstance(core_data, dict):
            for k, v in core_data.items():
                if isinstance(v, list):
                    mapping[k.strip().lower()] = v
    except Exception:
        pass
    # Load pack keywords
    packs_dir = base_dir / "packs"
    if packs_dir.exists():
        for pack_file in packs_dir.glob("*.yml"):
            try:
                pack_data = yaml.safe_load(pack_file.read_text())
                if isinstance(pack_data, dict):
                    for k, v in pack_data.items():
                        if isinstance(v, list):
                            mapping[k.strip().lower()] = v
            except Exception:
                pass
    lower_prompt = prompt.lower()
    caps: list[str] = []
    caps_set: set[str] = set()
    # Keyword matching: match if any token in the keyword appears in prompt
    for key, vals in mapping.items():
        tokens = key.split()
        if not any(token and token in lower_prompt for token in tokens):
            continue
        for cap in vals:
            if isinstance(cap, str) and cap not in caps_set:
                caps_set.add(cap)
                caps.append(cap)
    # LLM integration
    use_llm_env = os.getenv("USE_LLM_PARSER", "") in ("1", "true", "True")
    if (use_llm or use_llm_env) and os.getenv("OPENAI_API_KEY"):
        try:
            import openai

            system_prompt = (
                "You are a capability extractor. Return a JSON array of capability IDs."
            )
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            llm_content = response.choices[0].message.content
            llm_caps = json.loads(llm_content)
            if isinstance(llm_caps, list):
                for cap in llm_caps:
                    if isinstance(cap, str) and cap not in caps_set:
                        caps_set.add(cap)
                        caps.append(cap)
        except Exception:
            pass
    return caps
  
def prompt_to_plan(prompt: str) -> list[dict]:
    """
    Use OpenAI GPT-4.1 to generate a structured execution plan for the given prompt.
    Falls back to keyword-based planning if the LLM call fails or returns invalid JSON.
    """
    # Load available utilities
    try:
        from orchestrator_core.catalog.index import load_specs

        specs = load_specs()
        utilities = list(specs.values())
    except Exception:
        utilities = []
    # Build system messages
    system_prompt = (
        "You are a planning agent for PrometheusBlocks, a modular AI system composed of small, composable utility blocks."
        "Each block must conform to a schema called a utility contract."
        "This is the utility contract:"
        f"""
        "Utility Contract — shared schema for all PrometheusBlocks utilities"

            from pydantic import BaseModel, Field"
            from typing import List

            MAX_UTILITY_TOKENS = 200_000


            class Dependency(BaseModel):
                package: str
                version: str = Field(..., pattern=r"^[^\s]+$")


            class EntryPoint(BaseModel):
                name: str
                description: str
                parameters_schema: dict
                return_schema: dict


            class UtilityContract(BaseModel):
                name: str
                version: str
                language: str = Field(..., description="e.g. python, swift")
                description: str
                size_budget: int = MAX_UTILITY_TOKENS
                entrypoints: List[EntryPoint]
                deps: List[Dependency] = []
                tests: List[str] = []

            class Config:
             title = "PrometheusBlocks Utility Contract"
                # Pydantic v2: strip whitespace from strings
                str_strip_whitespace = True
                

        "Given a user prompt and a list of available utilities, identify utilities that can be used to fulfill the request."
        "If the existing utilities are not sufficient, suggest additional utility contracts that would be needed."
        "Output a JSON array of used capabilities, missing capabilities, and proposed utilities, along with a written plan."""
    )
    # Context with utilities
    try:
        utilities_json = json.dumps({"utilities": utilities})
    except Exception:
        utilities_json = "{}\n"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Available utilities: {utilities_json}"},
        {"role": "user", "content": prompt},
    ]
    # Call OpenAI Responses API for structured planning
    try:
        import os
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Combine instructions: system prompt + utilities context
        instructions = system_prompt + "\nAvailable utilities: " + utilities_json
        resp = client.responses.create(
            model="gpt-4.1-2025-04-14",
            instructions=instructions,
            input=prompt,
        )
        # Extract text output
        if hasattr(resp, "output_text") and resp.output_text is not None:
            content = resp.output_text
            print(f"LLM response: {content}")
        else:
            parts: list[str] = []
            for item in getattr(resp, "output", []):
                for chunk in item.get("content", []):
                    if chunk.get("type") == "output_text":
                        parts.append(chunk.get("text", ""))
            content = "".join(parts)
        plan = json.loads(content)
        # Validate structure
        if not isinstance(plan, list):
            raise ValueError("Plan is not a list")
        validated: list[dict] = []
        expected_id = 1
        for item in plan:
            if (
                not isinstance(item, dict)
                or item.get("step_id") != expected_id
                or not isinstance(item.get("action"), str)
                or not isinstance(item.get("inputs"), dict)
                or not isinstance(item.get("description"), str)
            ):
                raise ValueError(f"Invalid plan item: {item}")
            validated.append(item)
            expected_id += 1
        return validated
    # Capture the exception as 'e'
    except Exception as e:
        # Print the exception before falling back
        print(f"LLM planning failed, falling back to keyword plan. Error: {e}")
        # Fallback: simple keyword-based plan
        caps = prompt_to_capabilities(prompt)
        steps: list[dict] = []
        for idx, cap in enumerate(caps, start=1):
            steps.append({
                "step_id": idx,
                "action": cap,
                "inputs": {}, # Defaulting to empty inputs for fallback
                "description": f"Keyword-based match for '{cap}'", # Add basic description
            })
        return steps

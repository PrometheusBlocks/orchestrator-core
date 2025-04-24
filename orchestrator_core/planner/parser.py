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

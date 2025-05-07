# Sprint Code Plan

This document outlines the plan for the upcoming sprint, focused on two primary objectives:
1. Migrate the GitHub Client implementation to use the `requests` library.
2. Fully implement the LLM parser using ChatGPT 4.1 (`gpt-4.1-2025-04-14`) to generate structured execution plans based on user prompts and available utilities.

---

## 1. Migrate GitHub Client to `requests`

**Goal:** Replace existing `urllib`-based HTTP logic in `orchestrator_core/catalog/github_client.py` with a cleaner, more maintainable `requests`-based implementation, while preserving current functionality (search API + fallback per-repo fetch, semver selection, authentication, pagination).

**Steps:**
1. Add `requests` to `requirements.txt` (pin latest compatible version).
2. In `github_client.py`:
   - Remove imports: `urllib.request`, `urllib.error`, `urllib.parse`, `ssl`, `certifi`.
   - Import `requests` and instantiate a `requests.Session()`.
   - Build default headers (`Accept`, optional `Authorization` from `GITHUB_TOKEN`).
   - Replace `_get_json(url)` helper with a `session.get(url, headers=headers)` call, invoking `.json()` and preserving HTTP error handling.
   - Handle pagination by inspecting `response.headers.get('Link')` and following `rel="next"` links.
   - Maintain existing logic for base64 decoding, JSON schema validation (`UtilityContract`), size checks, and semver comparison.
3. Update or create unit tests in `tests/test_catalog.py` to mock `requests.Session` and validate both success and error paths.
4. Verify functionality manually via CLI (`python -m orchestrator_core.cli list`) and existing tests.

---

## 2. Implement LLM Parser with ChatGPT 4.1

**Goal:** Enhance the planner to generate a step-by-step execution plan (not just capability IDs) by leveraging the `gpt-4.1-2025-04-14` model. The parser should consume a natural language prompt and the catalog of available utilities, and output a structured JSON plan.

**Design Overview:**
1. **Inputs:**
   - `prompt: str` from the user.
   - `utilities: list[dict]` representing all available specs (from `fetch_github_specs` and local registry).
2. **Prompt Construction:**
   - System message: Describe the assistant role (an orchestrator planning utility calls).
   - Context: JSON-serialized list of utilities (including name, description, inputs, outputs, version).
   - User message: The original natural language prompt.
3. **API Call:**
   - Use `openai.ChatCompletion.create` with `model="gpt-4.1-2025-04-14"`.
   - Expect response content to be valid JSON conforming to a predefined schema (array of steps).
4. **Expected Output Schema:**
   ```json
   [
     {
       "step_id": 1,
       "action": "utility_name",
       "inputs": { "param1": "value1", ... },
       "description": "Brief description of this step."
     },
     ...
   ]
   ```
5. **Post-Processing:**
   - Validate JSON against schema (e.g., ensure `step_id` ordering, required fields).
   - Fall back to keyword-based capability extraction if LLM response is invalid or API errors occur.

**Implementation Steps & Status:**
1. Add dependency on `openai` in `requirements.txt` if not present or update to latest.
2. Create or extend `orchestrator_core/planner/parser.py` with a new function (e.g., `prompt_to_plan`) encapsulating the above logic.
3. Implement prompt templates, API invocation, and response parsing.
4. Integrate `prompt_to_plan` into CLI (`orchestrator_core/cli.py`) and API endpoint (`orchestrator_core/api/main.py`), writing `plan.json` with the structured plan.
5. Write unit tests in `tests/test_planner.py` that mock `openai.ChatCompletion` and verify both happy path (valid JSON) and failure modes (invalid JSON, API errors).
6. Update documentation (CLI help text, README) to describe the new plan output format.
   
Status (2025-05-02):
- [x] Step 1: Verified `openai` dependency in `requirements.txt`.
- [x] Step 2: Implemented `prompt_to_plan` function.
- [x] Step 3: Built prompt templates, API call, and response parsing with validation.
- [x] Step 4: Integrated `prompt_to_plan` into CLI and API endpoint.
- [x] Step 5: Added unit tests (`tests/test_planner_parser.py`).
- [ ] Step 6: Documentation updates pending.

---

## 3. Timeline & Deliverables

* Day 1-2 (2025-05-02): ✅ Migrate GitHub client to `requests`, update tests, and verify existing workflows.
* Day 3-4 (2025-05-02): ✅ Prototype LLM plan generation; defined prompt templates and output schema.
* Day 5 (2025-05-02): ✅ Integrate into CLI/API and implement fallback logic.
* Day 6: Write comprehensive unit tests and update documentation.
* Day 7: Final review, polish, and merge.

---

This plan focuses on root-cause improvements, maintains current functionality, and lays out clear steps for review and testing.